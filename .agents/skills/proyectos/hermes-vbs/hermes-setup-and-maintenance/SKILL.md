---
name: hermes-setup-and-maintenance
description: >-
  Instala, configura y mantiene un servidor de Hermes Agent (Nous Research) en una
  instancia AWS EC2 t3.medium con Ubuntu 26.04, operándolo de forma remota por SSH
  nativo (alias vbs-hermes / vbs-hermes-chatwoot). Úsala SIEMPRE que el usuario
  mencione Hermes, "el servidor de Hermes", el orquestador en EC2,
  instalar/actualizar/diagnosticar Hermes, configurar su modelo o proveedor,
  levantar el gateway de mensajería (WhatsApp/WasenderAPI, Telegram, etc.), dejarlo
  corriendo como servicio, revisar logs, o cualquier tarea de administración de ese
  servidor por SSH — aunque no diga explícitamente "usa la skill". Preferir OpenSSH
  nativo; en Cloud Agents usa ssh_via_op.py de ssh-servidores. Tabby solo como fallback.
---

# Hermes: instalación y mantenimiento vía SSH nativo

Esta skill te permite provisionar y mantener un servidor de **Hermes Agent**
(https://github.com/NousResearch/hermes-agent) en una **EC2 t3.medium con
Ubuntu 26.04**, ejecutando la operación remota **por OpenSSH nativo**.

Aliases (ver skill `ssh-servidores` y `hosts.md`):

| Rol | Alias | Notas |
|---|---|---|
| Hermes Agent | `vbs-hermes` | usuario `ubuntu` |
| Hermes + Chatwoot | `vbs-hermes-chatwoot` | usuario `ubuntu` |

## Arquitectura

```
Codex (tú) ── OpenSSH ──► EC2 t3.medium (Ubuntu)
                              └─ Hermes Agent
```

- Hermes es un **orquestador**: llama a un LLM remoto por API, no corre el modelo
  localmente. Por eso una t3.medium (2 vCPU / 4 GB RAM) es suficiente.
- El gateway de mensajería se conecta **hacia afuera**; no necesita puertos
  entrantes salvo webhook HTTPS (WasenderAPI).

## Cómo operar (SSH nativo, preferido)

**Local:**

```bash
ssh -o BatchMode=yes -o ConnectTimeout=10 vbs-hermes "whoami && hostname && lsb_release -d"
ssh -o BatchMode=yes vbs-hermes "<comando>"
```

**Cloud Agent / Codex web** (no hay `~/.ssh/config`):

```bash
bash ~/.cursor/skills/ssh-servidores/scripts/bootstrap_cloud.sh
python3 ~/.cursor/skills/ssh-servidores/scripts/ssh_via_op.py vbs-hermes -- whoami && hostname && lsb_release -d
python3 ~/.cursor/skills/ssh-servidores/scripts/ssh_via_op.py vbs-hermes -- "<comando>"
```

1. Confirma host (`ubuntu` + hostname de la EC2) antes de cambiar nada.
2. Un comando remoto por invocación `ssh ... "..."`. Para sesiones largas usa
   `ssh vbs-hermes` con un script o `bash -lc`.
3. Si SSH falla (timeout, Permission denied), **entonces** cae al MCP de Tabby:
   `get_ssh_session_list` → `exec_command` en la pestaña ya abierta. Si Tabby
   tampoco tiene la sesión, pide al usuario que reconecte.

## Prerrequisitos

- Local: `~/.ssh/config` con alias `vbs-hermes` (regenerar con
  `scripts/importar_tabby.py` de `ssh-servidores` si falta).
- Cloud Agent: skill `ssh-servidores` sincronizada + Runtime Secret
  `OP_SERVICE_ACCOUNT_TOKEN` + `bootstrap_cloud.sh`.
- Sistema base: `sudo apt-get update` funciona; hay salida a Internet.
- RAM/espacio: la t3.medium tiene 4 GB. Si no hay swap, **crea 2 GB de swap
  antes de instalar** (ver Flujo A).
- No abras puertos entrantes salvo que WasenderAPI lo pida (443 + reverse proxy).

---

## Flujo A — Provisión inicial e instalación de Hermes

Ejecuta en `vbs-hermes`. Verifica cada paso antes de seguir.

**1. Actualizar base y crear swap (protege la instalación en 4 GB de RAM):**

```bash
sudo apt-get update && sudo apt-get -y upgrade
# Swap de 2 GB solo si no existe ya:
if ! sudo swapon --show | grep -q .; then
  sudo fallocate -l 2G /swapfile && sudo chmod 600 /swapfile
  sudo mkswap /swapfile && sudo swapon /swapfile
  echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
fi
free -h
```

**2. Instalar Hermes** (el instalador trae uv, Python 3.11, Node.js, ripgrep, ffmpeg):

```bash
curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash
source ~/.bashrc
```

**3. Verificar la instalación:**

```bash
hermes doctor
```

Lee la salida completa. `hermes doctor`
diagnostica problemas de entorno; resuélvelos antes de configurar.

---

## Flujo B — Configuración

Hermes se configura con subcomandos interactivos. **Regla de oro de seguridad:**
las API keys y secretos se cargan por el asistente interactivo (`hermes setup`,
`hermes model`) o escribiéndolos en un archivo `.env` con permisos `600`. **Nunca**
pases una API key como argumento en la línea de comandos: queda en el historial del
shell y en el buffer del terminal que el MCP puede leer.

**Comandos base:**

```bash
hermes setup        # Asistente completo: proveedor, modelo, tools, gateway
hermes model        # Elegir proveedor LLM y modelo (sin lock-in)
hermes tools        # Activar/desactivar herramientas
hermes config set   # Fijar valores de configuración puntuales
```

- Si el usuario usa **Nous Portal** (una sola suscripción para modelo + web search +
  imagen + TTS + navegador): `hermes setup --portal` hace login por OAuth y activa
  el Tool Gateway. Verifica con `hermes portal info`.
- Si trae sus propias keys por proveedor (OpenRouter, OpenAI, endpoint propio),
  configúralas con `hermes model` de forma interactiva.

### Gateway de mensajería (WhatsApp / WasenderAPI, Telegram, etc.)

El gateway es un **proceso de larga duración**: conecta Hermes a plataformas de
mensajería. Flujo general:

```bash
hermes gateway setup   # Configurar plataformas y usuarios permitidos
hermes gateway start   # Arrancar el gateway (dejar como servicio, ver Flujo C)
```

**Caso WhatsApp vía WasenderAPI (integración de terceros — verifica antes de asumir):**

Hermes trae soporte nativo de WhatsApp en su gateway, pero WasenderAPI es un
proveedor HTTP/webhook externo, así que la conexión típica es:

1. Guardar las credenciales de WasenderAPI como variables de entorno/config de
   Hermes (nunca en texto plano en la línea de comandos). Ejemplo de patrón seguro:
   ```bash
   umask 077
   # editar el .env de Hermes y añadir las claves de WasenderAPI:
   nano "${HERMES_HOME:-$HOME/.hermes}/.env"
   ```
2. WasenderAPI entrega mensajes por **webhook**, así que el servidor necesita ser
   alcanzable por HTTPS desde Internet. Eso implica: un dominio, un reverse proxy
   (Caddy o nginx) con TLS, y abrir el **443** en el Security Group. No expongas el
   puerto interno del gateway directamente.
3. Confirmar el wiring exacto (nombre de la plataforma, endpoint de envío y ruta del
   webhook) contra la doc de mensajería de Hermes:
   **https://hermes-agent.nousresearch.com/docs/user-guide/messaging**

> Si no tienes certeza del mapeo exacto WasenderAPI↔Hermes, **dilo y consulta la
> doc de mensajería** en lugar de inventar flags. Trátalo como configuración
> específica del proyecto, no como algo asumido.

---

## Flujo C — Dejar Hermes corriendo como servicio (systemd)

En un servidor headless el gateway debe sobrevivir a cierres de sesión SSH y
reinicios. Crea un servicio systemd de usuario o de sistema. Ejemplo de servicio de
sistema (ajusta `User`, rutas y el binario real de `hermes` con `which hermes`):

```bash
HERMES_BIN="$(which hermes)"
sudo tee /etc/systemd/system/hermes-gateway.service >/dev/null <<EOF
[Unit]
Description=Hermes Agent Gateway
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=$(whoami)
WorkingDirectory=$HOME
ExecStart=$HERMES_BIN gateway start
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable --now hermes-gateway
systemctl status hermes-gateway --no-pager
```

Verifica que quedó `active (running)`. Para logs en vivo:
`journalctl -u hermes-gateway -n 100 --no-pager` (o `-f` si el usuario pide seguimiento).

> Alternativa rápida sin systemd: `tmux new -s hermes 'hermes gateway start'`. Menos
> robusta (no arranca en reboot); prefiere systemd para producción.

---

## Flujo D — Mantenimiento rutinario

Tareas frecuentes. Antes de cualquier cambio con riesgo, **haz snapshot de la
config** y explícale al usuario qué vas a hacer.

**Diagnóstico y estado:**
```bash
hermes doctor
systemctl status hermes-gateway --no-pager
journalctl -u hermes-gateway -n 100 --no-pager
```

**Actualizar Hermes:**
```bash
hermes update
sudo systemctl restart hermes-gateway   # reiniciar el servicio tras actualizar
hermes doctor                           # verificar que quedó sano
```

**Snapshot de config antes de tocar (recuperable si algo se rompe):**
```bash
cp -a "${HERMES_HOME:-$HOME/.hermes}" "${HERMES_HOME:-$HOME/.hermes}.bak.$(date +%F_%H%M)"
```

**Salud del host (útil en t3.medium por la RAM):**
```bash
free -h && df -h / && uptime
```

**Reiniciar el gateway:** `sudo systemctl restart hermes-gateway`
**Detenerlo:** `sudo systemctl stop hermes-gateway`

---

## Reglas de seguridad (obligatorias)

Estás ejecutando comandos en un **servidor real** por SSH. Trabaja como un operador
prudente, no como un script optimista.

1. **Confirma el host** (`whoami && hostname`) al inicio de cada sesión y antes de
   cualquier comando destructivo.
2. **Nunca** pongas API keys, tokens ni contraseñas como argumentos en la línea de
   comandos ni en `echo`. Van por asistentes interactivos o a archivos con `600`.
   Todo lo que escribes en el terminal queda en el buffer y en el historial.
3. **Pide confirmación explícita al usuario** antes de: borrar datos, cambiar reglas
   de firewall/Security Group, modificar el `.env`, o cualquier acción irreversible.
   No generalices un permiso a acciones posteriores.
4. **No abras puertos entrantes** salvo que una integración lo exija (p. ej. el 443
   para el webhook de WasenderAPI), y en ese caso usa reverse proxy con TLS.
5. **Snapshot antes de cambios de config** y **`hermes doctor` después** de cualquier
   actualización o cambio significativo.
6. Si algo no coincide con lo esperado (host equivocado, sesión SSH caída, salida
   rara), **detente y reporta** en vez de improvisar.

---

## hermes-vbs (panel/webhook) — skills en el servidor

Al hacer `git push` + `scripts/update.sh` / `deploy.sh` en el servidor Hermes-VBS:

- **NO sobrescribas** los `SKILL.md` del servidor: el usuario los edita desde el panel.
- El deploy solo instala skills **nuevas que falten**.
- Sync forzado del repo → servidor **solo si el usuario lo pide** explícitamente:
  `bash scripts/sync-skills.sh` o `SYNC_SKILLS=1 bash scripts/deploy.sh`.

---

## Referencia rápida de comandos de Hermes

```
hermes              # CLI interactiva
hermes model        # Elegir proveedor y modelo
hermes tools        # Configurar herramientas
hermes config set   # Fijar valores de config
hermes gateway      # Gestión del gateway de mensajería
hermes setup        # Asistente completo de configuración
hermes update       # Actualizar a la última versión
hermes doctor       # Diagnosticar problemas
```

Documentación: https://hermes-agent.nousresearch.com/docs/
- Mensajería/gateway: /docs/user-guide/messaging
- Configuración: /docs/user-guide/configuration
- MCP: /docs/user-guide/features/mcp