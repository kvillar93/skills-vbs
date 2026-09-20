---
name: chatwoot-vbs
description: >-
  Opera Chatwoot de VBS en el servidor vbs-hermes-chatwoot (EC2). Usar cuando
  el usuario mencione Chatwoot, el inbox, agentes, WhatsApp/WasenderAPI junto
  a Chatwoot, o el alias vbs-hermes-chatwoot. Para el orquestador Hermes en
  la otra EC2 usa hermes-setup-and-maintenance. SSH vía skill ssh-servidores.
---

# Chatwoot VBS

Servidor: alias SSH `vbs-hermes-chatwoot` (usuario `ubuntu`). Inventario en `ssh-servidores` / `hosts.md`.

## Conexión

**Local:**

```bash
ssh -o BatchMode=yes -o ConnectTimeout=10 vbs-hermes-chatwoot "whoami && hostname"
```

**Cloud Agent:**

```bash
bash ~/.cursor/skills/generales/ssh-servidores/scripts/bootstrap_cloud.sh
python3 ~/.cursor/skills/generales/ssh-servidores/scripts/ssh_via_op.py vbs-hermes-chatwoot -- whoami
```

(Si la skill está en `~/.cursor/skills/ssh-servidores` por un install plano, usa esa ruta.)

## Reglas

- Confirma host antes de cambiar `.env`, nginx o docker.
- No imprimas tokens, `SECRET_KEY_BASE` ni webhooks.
- En t3.medium: antes de builds pesados, `free -h` y swap (regla VBS).
- Hermes (orquestador) vive en `vbs-hermes`, no en esta caja, salvo que el usuario diga lo contrario.

## Ampliar esta skill

Cuando haya runbooks (compose, backups, upgrades), añádelos aquí y publica con `mantener-skills-vbs`.
