#!/usr/bin/env bash
# Prepara una VM de Cloud Agent / Cursor web para SSH vía 1Password.
# Idempotente. No imprime secretos.
set -euo pipefail

buscar_skill() {
  local c
  for c in \
    "${SSH_SERVIDORES_DIR:-}" \
    "$HOME/.cursor/skills/ssh-servidores" \
    "/root/.cursor/skills/ssh-servidores" \
    "$(cd "$(dirname "$0")/.." && pwd)"
  do
    if [[ -n "$c" && -f "$c/scripts/ssh_via_op.py" ]]; then
      echo "$c"
      return 0
    fi
  done
  return 1
}

SKILL="$(buscar_skill)" || {
  echo "No encuentro la skill ssh-servidores. Activa Sync Skills en Cloud Agents." >&2
  exit 1
}

if ! command -v python3 >/dev/null 2>&1; then
  echo "Falta python3 en esta VM." >&2
  exit 1
fi

if ! command -v ssh >/dev/null 2>&1; then
  echo "Falta el cliente ssh. En Debian/Ubuntu: apt-get update && apt-get install -y openssh-client unzip curl" >&2
  exit 1
fi

if ! command -v unzip >/dev/null 2>&1 || ! command -v curl >/dev/null 2>&1; then
  if command -v apt-get >/dev/null 2>&1; then
    sudo apt-get update -qq
    sudo apt-get install -y -qq unzip curl >/dev/null
  fi
fi

bash "$SKILL/scripts/setup_op_cloud.sh"

echo "Skill: $SKILL"
echo "Listo. Conecta así (no uses ssh <alias> a pelo):"
echo "  python3 \"$SKILL/scripts/ssh_via_op.py\" vbs-hermes -- whoami"
