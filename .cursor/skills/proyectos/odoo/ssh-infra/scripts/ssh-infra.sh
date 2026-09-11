#!/usr/bin/env bash
# ssh-infra <alias> [args ssh…]
# Usa ~/.ssh/infra/<alias>.pem y hosts.env. No usa el agente 1Password.
set -euo pipefail

DEST="${SSH_INFRA_DIR:-$HOME/.ssh/infra}"
DEFAULT_USER="${SSH_INFRA_USER:-ubuntu}"

if [ "${1:-}" = "" ] || [ "${1:-}" = "-h" ] || [ "${1:-}" = "--help" ]; then
  echo "uso: ssh-infra <alias> [args-ssh…]" >&2
  echo "aliases en $DEST/*.pem ; destinos en $DEST/hosts.env" >&2
  exit 2
fi

alias="$1"
shift
pem="$DEST/${alias}.pem"
if [ ! -f "$pem" ]; then
  echo "no existe $pem — corre sync-pems.sh" >&2
  exit 1
fi

user_host=""
if [ -f "$DEST/hosts.env" ]; then
  user_host="$(grep -E "^${alias}=" "$DEST/hosts.env" | head -1 | cut -d= -f2- || true)"
fi

if [ -z "$user_host" ]; then
  echo "falta destino para '$alias' en $DEST/hosts.env (formato alias=usuario@host)" >&2
  exit 1
fi

exec ssh \
  -i "$pem" \
  -o IdentitiesOnly=yes \
  -o IdentityAgent=none \
  -o StrictHostKeyChecking=accept-new \
  "$user_host" \
  "$@"
