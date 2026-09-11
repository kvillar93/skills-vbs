---
name: ssh-servidores
description: >-
  Conecta a servidores SSH (VBSOLUTIONS, Hermes, Lifter, Odoo, Ashton, Umbra,
  TSHEILA, clientes). En CUALQUIER sesión — local, Cursor web o Cloud Agent —
  usa esta skill. Local: ssh <alias> o ~/.ssh. Nube: bootstrap_cloud.sh +
  ssh_via_op.py / conectar.py con OP_SERVICE_ACCOUNT_TOKEN (vault 1Password
  SSH-Infra). Nunca pegues PEM ni el token. Incluye quoting de PowerShell y
  logs enormes de Odoo.
---

# SSH a servidores (local y Cloud Agents)

Inventario: [hosts.md](hosts.md). Vault: 1Password `SSH-Infra` ([guía](docs/GUIA-1PASSWORD.md)).

**Cloud Agent / Cursor web no tiene** `~/.ssh/config` ni las PEM. No ejecutes `ssh vbs-hermes` a pelo ahí. Resuelve host/usuario/puerto desde `hosts.md` y la clave desde 1Password.

## Qué sesión es

| Señal | Sesión | Cómo conectar |
|---|---|---|
| Hay `OP_SERVICE_ACCOUNT_TOKEN` o `/run/cursor/api.sock` | **Nube** | `bootstrap_cloud.sh` + `ssh_via_op.py` |
| Windows con `~/.ssh/config` | **Local** | `ssh <alias>` (Agent 1Password o PEM) |
| Linux y el agente 1Password no ofrece identidades | **Local Linux** | skill `ssh-infra` (`~/.ssh/infra/*.pem`; las claves no van al repo) |

## Cloud Agent / Cursor web (obligatorio)

Al **empezar** cualquier tarea que toque un servidor:

```bash
bash ~/.cursor/skills/ssh-servidores/scripts/bootstrap_cloud.sh
python3 ~/.cursor/skills/ssh-servidores/scripts/ssh_via_op.py <alias> -- whoami && hostname
```

Equivale: `python3 .../scripts/conectar.py <alias> -- <comando>`.

Si falta la skill: pide activar **Sync Skills for Cloud Agents** en Settings → Agents → Context and Tools (o Customize → Skills). Si falta el token: Runtime Secret `OP_SERVICE_ACCOUNT_TOKEN` (user). No lo pidas en el chat.

SQL / stdin en Linux (Cloud):

```bash
python3 ~/.cursor/skills/ssh-servidores/scripts/ssh_via_op.py tsheila -- sudo -u postgres psql -d tsheila
```

(manda el SQL por stdin, igual que en local).

`StrictHostKeyChecking=accept-new` solo en nube (VM efímera, `known_hosts` vacío).

## Local (este PC)

1. Resuelve el alias en [hosts.md](hosts.md).
2. Confirma el host **antes** de cambiar nada:

```bash
ssh -o BatchMode=yes -o ConnectTimeout=10 <alias> "whoami && hostname && (lsb_release -d 2>/dev/null || true)"
```

3. Comandos simples (sin comillas internas, sin SQL, sin `\d`):

```bash
ssh -o BatchMode=yes <alias> "whoami && hostname"
```

4. Salida larga: archivo local o pagina. No imprimas claves ni `.env`.
5. SQL / Python / `\d`: **stdin**. Recetas: [powershell-odoo.md](powershell-odoo.md).

Aliases frecuentes: `vbsolutions`, `vbs-hermes`, `vbs-hermes-chatwoot`, `ashton-school`, `umbra`, `lifter`, `tsheila`.

## Credenciales

1. Local + app 1Password desbloqueada: SSH Agent.
2. Local, app cerrada: `~/.ssh/<pem>` (Windows) o `~/.ssh/infra/` vía `ssh-infra` (Linux). Las PEM **no** se commitean.
3. Nube: documentos PEM en vault `SSH-Infra` vía `op` + service account.
4. Hosts `password`: Tabby o terminal interactivo. **No automatizar.**

Nunca: pegar PEM, `.ppk`, contraseñas, `config.yaml` de Tabby ni el token. Si algo falla, di el *estado* (sin sesión, falta ítem, falta skill), no el contenido.

## Reglas

- Preferir este SSH frente al MCP de Tabby. Tabby solo si SSH falla o el usuario lo pide.
- `BatchMode=yes` en clave publica.
- `bmcvmod` / `bmcvmod-test`: PEM no convertida (passphrase).
- Antes de borrar datos, tocar firewall o editar `.env`: pedir confirmación.
- **Windows PowerShell:** las comillas de `ssh ... "psql -c \"SELECT ...\""` se rompen. En Cloud Agent (Linux) no aplica ese truco; usa el wrapper y stdin.
- No uses Read/Glob sobre UNC remotas (`\\host\odoo\...`). Lee con `ssh` / `ssh_via_op` + `sudo cat`.
- `/etc/odoo-server.conf` pide sudo. Filtra `passwd|password|secret`.
- **Nunca** `grep` el log completo de Odoo. En TSHEILA llegó a 34G. Primero `sudo ls -lh`; luego `sudo tail -c 2M ... | grep -a`.

## Desde PowerShell (solo local Windows)

Patron que funciona (here-string **simple** `@'...'@`):

```powershell
$sql = @'
SELECT id, name, code FROM hr_salary_rule WHERE code = 'Q2VACDIF2';
'@
$sql | ssh -o BatchMode=yes tsheila "sudo -u postgres psql -d tsheila"
```

Prohibido en PowerShell: `ssh ... "psql -c \"SELECT ...\""`, here-string `@"..."@` con SQL, `\d` en el argumento de `ssh`.

Python a `odoo-bin shell`: stdin. Flags: `--no-http --workers=0 --max-cron-threads=0`. No llames `compute_sheet` para diagnosticar; usa `_get_payslip_lines`.

## Odoo remoto (descubrimiento)

Conf típico Lifter/TSHEILA: `/etc/odoo-server.conf`, servicio `odoo-server`, user `odoo`, addons `/odoo/odoo-server`, `/odoo/enterprise/addons`, `/odoo/custom/addons/addonsEP14`. DB suele llamarse como el cliente (`tsheila`). `list_db = False` no impide `\l` por stdin.

En Odoo 14 no asumas columnas `modules` ni `serialization_field_id` en `ir_model_fields`. Un campo ahi **no implica** columna SQL. En nómina, `False.month` falla; usa `employee.first_contract_date or contract.date_start`.

## Claves y vault

PEM locales: `C:/Users/kevin/.ssh/` (`vbsolutions`, `odoo_xolver`, `externo`, `OdooEPX`, `fpaxv3`, `umbrafinance`, `vvl`).
En 1Password son **documentos** con el mismo título (la plantilla SSH Key de la CLI no guardaba la clave). Drive no se toca.

Reimportar Tabby (solo local):

```bash
python -m pip install --user puttykeys pyyaml
python ~/.cursor/skills/ssh-servidores/scripts/importar_tabby.py
```

`private_odoo.ppk` (bmcvmod): no convertir sin passphrase del usuario; no la guardes en la skill.
