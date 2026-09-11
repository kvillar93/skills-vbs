---
name: ssh-infra
description: >-
  Conecta a servers de infraestructura usando .pem sincronizados desde
  1Password (bóveda SSH-Infra) a ~/.ssh/infra, nunca al repo. Use when
  the user pide SSH, scp, conectar a un server, OdooEPX, vbsolutions,
  fpaxv3, umbrafinance, odoo_xolver, vvl, externo, o “usa los pem”.
---

# SSH Infra (PEM seguros)

## Overview

Los `.pem` viven como **Documentos** en la bóveda `SSH-Infra` de 1Password. El agente SSH de 1Password **no** los ofrece (solo ítems tipo SSH Key). Esta skill baja esas claves a `~/.ssh/infra/` (fuera de `/odoo`, permisos 700/600) y conecta con `IdentitiesOnly` sin pasar por el agente vacío.

## When to Use

- Conectar por SSH/SCP a un server del vault SSH-Infra
- El usuario dice “usa los pem”, “entra al server”, “sesión como cloud”
- `ssh-add -l` del agente 1Password no tiene identidades

**No usar** para secretos de app (API keys, `.env`): eso es 1Password Environments / MCP. Las sesiones cloud de Cursor usan el ítem `cursor-cloud-ssh` (bóveda Cursor), no estos PEM.

## Guardado seguro (obligatorio)

| Regla | Detalle |
|-------|---------|
| Directorio | `~/.ssh/infra/` — **nunca** dentro de `/odoo` ni de git |
| Permisos | directorio `700`, cada `.pem` `600`, dueño el usuario |
| Sync | `scripts/sync-pems.sh` via `op document get --output` |
| Chat | no pegar PEM ni fingerprints completos; solo alias y “clave ok” |
| Disco | no copiar PEM a `/tmp` del workspace ni a tickets |

Mapa opcional de destino (no es secreto de clave, sí de inventario):

`~/.ssh/infra/hosts.env` — líneas `alias=usuario@host` (ver `references/hosts.example`).

## Proceso

1. Leer esta skill. No improvisar `IdentityFile` dentro del repo.
2. Comprobar 1Password CLI: `op whoami`. Si falla: `op signin` y que el usuario apruebe en la app.
3. Sincronizar PEM (usa la copia que exista):
   ```bash
   ~/.cursor/skills/ssh-infra/scripts/sync-pems.sh
   # o en el workspace Odoo:
   /odoo/.cursor/skills/ssh-infra/scripts/sync-pems.sh
   ```
   Debe crear `~/.ssh/infra/<alias>.pem` y verificar con `ssh-keygen -l` (no volcar stdout al chat).
4. Resolver destino:
   - Si existe `alias=user@host` en `hosts.env`, usarlo.
   - Inventario Tabby (host/usuario/PEM): skill `ssh-servidores` → `hosts.md`.
   - Si no hay destino, **preguntar** usuario y host. No adivinar IPs.
5. Conectar:
   ```bash
   ~/.local/bin/ssh-infra <alias> [args-ssh…]
   ```
   o el script de la skill. Equivale a `ssh -i ~/.ssh/infra/<alias>.pem -o IdentitiesOnly=yes -o IdentityAgent=none user@host`.
6. En el primer prompt de host key, `accept-new` solo si el usuario confirma el server.

Alias conocidos (nombre del documento = nombre del `.pem`): `vbsolutions`, `fpaxv3`, `umbrafinance`, `odoo_xolver`, `OdooEPX`, `vvl`, `externo`. Usuario por defecto si no hay `hosts.env`: `ubuntu`.

## Common Rationalizations

| Excusa | Realidad |
|--------|----------|
| “Los dejo en /odoo/keys para que el repo los tenga” | El repo no es almacén de secretos. Fuera de git. |
| “Uso el agente 1Password, ya están en el vault” | El agente ignora Documentos `.pem`. |
| “Pego el PEM en el chat para depurar” | Prohibido. `ssh-keygen -l` y código de salida. |
| “Pruebo ubuntu@alias sin hosts.env” | El alias no es DNS. Sin host real el SSH no conecta. |

## Red Flags

- PEM en `/odoo`, `/tmp` del workspace o un commit
- `ssh` sin `IdentitiesOnly` (el agente 1Password vacío puede interferir)
- Imprimir `op document get` en el chat
- Inventar `HostName` o usuario

## Verification

- [ ] `stat -c '%a %n' ~/.ssh/infra ~/.ssh/infra/*.pem` → 700 y 600
- [ ] `sync-pems.sh` termina con conteo `ok` y sin volcar PEM
- [ ] `ssh-infra <alias>` usa `IdentityAgent=none` e `IdentitiesOnly=yes`
- [ ] Tras un SSH real: hostname remoto o `echo ok` en el server
- [ ] Skill registrada en `.cursor/skills/.local-skills` (workspace Odoo)
- [ ] Copia en skills-vbs: `.cursor/skills/proyectos/odoo/ssh-infra/`
