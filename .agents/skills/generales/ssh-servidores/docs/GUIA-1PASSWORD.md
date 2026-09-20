# Guía: 1Password para SSH (tú + Cursor)

Las `.ppk` de Google Drive no se tocan. El token del service account **nunca** se pega en el chat.

## 1. Cuenta y apps (tú)

1. Crea la cuenta en [1password.com](https://1password.com) (Individual alcanza).
2. Instala la app y el CLI:

```powershell
winget install -e --id AgileBits.1Password --accept-package-agreements --accept-source-agreements
winget install -e --id AgileBits.1Password.CLI --accept-package-agreements --accept-source-agreements
```

3. Abre 1Password, inicia sesión, activa **Settings → Developer → Use the SSH agent** y **Integrate with 1Password CLI**.
4. Deja el servicio de Windows `OpenSSH Authentication Agent` en **Disabled** (ya lo está).

## Estado (2026-09-06)

- Vault `SSH-Infra`: 7 **Documentos** PEM (`vbsolutions`, `odoo_xolver`, `externo`, `OdooEPX`, `fpaxv3`, `umbrafinance`, `vvl`). La plantilla SSH Key de la CLI no guardaba la clave.
- Service account `cursor-cloud-ssh` (solo lectura de `SSH-Infra`).
- Token guardado en vault **Cursor**, ítem `cursor-cloud-ssh`. Cópialo de la app (no del chat) al dashboard de Cursor como Runtime Secret `OP_SERVICE_ACCOUNT_TOKEN`.
- `agent.toml` apunta a `SSH-Infra`. El Agent de Windows aún no lista identidades hasta que actives **Use the SSH Agent** y desbloquees la app. Local ya entra con `~/.ssh`.

## 2. Vault e importar claves

En una terminal (no hace falta pegar nada aquí):

```powershell
op signin
python $env:USERPROFILE\.cursor\skills\ssh-servidores\scripts\subir_a_1password.py --solo-comprobar
python $env:USERPROFILE\.cursor\skills\ssh-servidores\scripts\subir_a_1password.py
```

Si algún ítem falla: en la app, **Nuevo ítem → SSH Key → Importar archivo** y elige `C:\Users\kevin\.ssh\vbsolutions` (y el resto). No abras esas PEM en Cursor.

Logins (Aurora, Backup STI, etc.): créalos a mano en `SSH-Infra`. No los dictes en el chat.

## 3. Probar en este PC

```powershell
ssh -o BatchMode=yes -o ConnectTimeout=10 vbs-hermes "whoami && hostname"
```

Con la app desbloqueada debe usar el Agent. Ciérrala y el mismo comando debe seguir con `~/.ssh`.

## 4. Cloud Agents / Cursor web

El token ya está como Runtime Secret `OP_SERVICE_ACCOUNT_TOKEN`. En **cada** agente nuevo:

1. Activa **Sync Skills for Cloud Agents**: Cursor **Settings → Agents → Context and Tools** (o busca `Sync Skills`). También: barra lateral **Customize → Skills**. No está en el dashboard de Cloud Agents.
2. Primeros comandos:

```bash
bash ~/.cursor/skills/ssh-servidores/scripts/bootstrap_cloud.sh
python3 ~/.cursor/skills/ssh-servidores/scripts/ssh_via_op.py vbs-hermes -- whoami
```

`ssh_via_op.py` no usa `~/.ssh/config`: saca host/usuario/puerto de `hosts.md` y la PEM del vault.

Opcional en el snapshot/install de Cloud Agents: la misma línea de `bootstrap_cloud.sh`.

Si el token se filtra: revócalo en 1Password.com y crea otro. No hace falta rotar las PEM salvo que alguien haya leído el vault.

## 5. Qué no hacer

- No subas PEM a secretos sueltos de Cursor (una por clave).
- No actives el `ssh-agent` de Windows.
- No automatices hosts con password.
- No borres Drive ni `~/.ssh` hasta que local + cloud lleven días bien.
