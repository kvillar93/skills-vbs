# Spec: vault 1Password para SSH (local + Cloud Agents)

Fecha: 2026-09-06  
Skill: `ssh-servidores`  
Estado: aprobado por Kevin (enfoques A, local+cloud, todos los servidores, fallback `~/.ssh`)

## Problema

Las PEM viven en `C:\Users\kevin\.ssh` sin passphrase. Cursor no tiene un vault SSH ligado a la cuenta: un Cloud Agent no ve esas claves. Hace falta un almacén web para que chats locales y Cloud Agents entren a los mismos servidores sin pegar material en el chat. Las `.ppk` de Google Drive no se tocan.

## Objetivos

- Guardar las 7 PEM y los 6 logins-password en un vault web `SSH-Infra` de 1Password.
- En este PC (y otros con la app): SSH Agent de 1Password; si la app está cerrada, fallback a `~/.ssh`.
- En Cloud Agents: CLI `op` + un solo Runtime Secret `OP_SERVICE_ACCOUNT_TOKEN` (solo lectura de `SSH-Infra`).
- El agente nunca imprime PEM, `.ppk`, contraseñas ni el token.
- Hosts `password` se guardan en el vault pero **no se automatizan** (Tabby o terminal interactivo).

## Fuera de alcance

- Borrar o cifrar las copias de Drive.
- Rotar claves en los servidores.
- Instalar Tailscale o un bastión (fase 2 posible, no ahora).
- Secretos sueltos de Cursor por cada PEM.
- Automatizar `sshpass` / passwords en la VM.

## Arquitectura

```
                    1Password.com
                    vault SSH-Infra
                   /              \
          PC local                  Cloud Agent (VM)
     app + SSH Agent              CLI `op` + token
     (Kevin desbloquea)           (Runtime Secret)
              \                      /
               ssh <alias> → servidor
```

- Inventario no secreto: `hosts.md` (alias → host → usuario → nombre de ítem).
- Nombre de ítem SSH Key = nombre de PEM: `vbsolutions`, `odoo_xolver`, `externo`, `OdooEPX`, `fpaxv3`, `umbrafinance`, `vvl`.
- Nombre de ítem Login = alias canónico: `aurora`, `backup-sti`, `odoo-quickbooks-jean`, `power-bi-server`, `sti-nuevo`, `stockalu-tercero`.

## Componentes

| Pieza | Responsabilidad |
|---|---|
| Cuenta + app 1Password | Desbloqueo biométrico/MFA, SSH Agent en Windows |
| Vault `SSH-Infra` | Único almacén de estas credenciales |
| Service account (read-only) | Autenticación no humana para Cloud Agents |
| Runtime Secret `OP_SERVICE_ACCOUNT_TOKEN` | Inyectado en la VM; redactado en transcript |
| `scripts/vault_map.py` | Alias/PEM → ítem; detecta hosts password |
| `scripts/subir_a_1password.py` | Crea vault e importa PEM sin imprimir material |
| `scripts/ssh_via_op.py` | En Cloud: `op read` → temp → `ssh` → borrar |
| `scripts/setup_op_cloud.sh` | Instala `op` en la VM Linux |
| Skill `SKILL.md` | Orden de backends y prohibiciones |

Windows: el SSH Agent de 1Password usa `\\.\pipe\openssh-ssh-agent`. El servicio `ssh-agent` de Windows debe seguir **Disabled**.

## Flujos

### Local

1. App desbloqueada → OpenSSH pide claves al Agent de 1Password.
2. App cerrada o Agent no disponible → `IdentityFile` de `~/.ssh/config` (comportamiento actual).
3. Host password → mensaje: usar Tabby; no leer el Login.

### Cloud Agent

1. Existe `OP_SERVICE_ACCOUNT_TOKEN`.
2. Setup instala `op`.
3. `python scripts/ssh_via_op.py <alias> -- <comando>`.
4. Si el alias es password, sale con código 2 y texto en español (sin secretos).
5. `op read "op://SSH-Infra/<item>/private key?ssh-format=openssh"` redirigido a un temp 600.
6. `ssh -i temp -o IdentitiesOnly=yes -o BatchMode=yes`.
7. Borrar temp en `finally`. stdout/stderr de `op` no se echoan.

### Subida de claves

`op item create --category ssh` **genera** una clave nueva; no importa PEM. La importación se hace:

1. Preferido: plantilla JSON (`op item template get ssh` + `op item create --template`) escrita a un temp y borrada.
2. Si la CLI no acepta el private key en plantilla: checklist para importar a mano en la app (`Nuevo ítem → SSH Key → Importar archivo`) desde `~/.ssh\<nombre>`, sin abrir el archivo en el chat.

Drive no se usa como origen.

## Errores

| Situación | Comportamiento |
|---|---|
| 1Password bloqueado en local | Aviso + fallback `~/.ssh` |
| Sin token en Cloud | Salir con mensaje; no inventar rutas de clave |
| Ítem ausente | `Falta el ítem <nombre> en el vault SSH-Infra` |
| Host password | No automatizar |
| `op` no instalado | Indicar winget/script de setup |

Si el token se filtra: revocarlo en 1Password.com. Rotar PEM solo si hay sospecha de lectura del vault.

## Pruebas de aceptación

- Local, app desbloqueada: `ssh -o BatchMode=yes -o ConnectTimeout=10 vbs-hermes "whoami && hostname"` ok.
- Local, app cerrada: el mismo comando ok vía `~/.ssh`.
- Cloud Agent: el mismo comando vía `ssh_via_op.py`; transcript sin token ni PEM.
- `G:\My Drive\**\*.ppk` intactos.
- Tests unitarios de `vault_map.py` (alias, PEM, password) en verde.

## Seguridad

- Service account: solo lectura, solo `SSH-Infra`.
- Un Runtime Secret, no siete.
- Prohibido commitear tokens, plantillas con PEM, o dumps de `op item get`.
- Cadenas de UI y errores en español.
