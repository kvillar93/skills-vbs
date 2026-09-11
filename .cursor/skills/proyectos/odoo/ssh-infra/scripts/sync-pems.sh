#!/usr/bin/env bash
# Sincroniza documentos .pem de la bóveda SSH-Infra a ~/.ssh/infra
# No imprime contenido de claves. Requiere: op signin.
set -euo pipefail

DEST="${SSH_INFRA_DIR:-$HOME/.ssh/infra}"
VAULT="${SSH_INFRA_VAULT:-SSH-Infra}"

if ! command -v op >/dev/null; then
  echo "Falta 1Password CLI (op)" >&2
  exit 1
fi
if ! op whoami >/dev/null 2>&1; then
  echo "1Password CLI no tiene sesión. Ejecuta: op signin" >&2
  exit 1
fi

umask 077
mkdir -p "$DEST"
chmod 700 "$DEST"

tmp="$(mktemp)"
trap 'rm -f "$tmp"' EXIT
op item list --vault "$VAULT" --categories Document --format json >"$tmp"

python3 - "$DEST" "$tmp" <<'PY'
import json, subprocess, sys
from pathlib import Path

dest = Path(sys.argv[1])
docs = json.loads(Path(sys.argv[2]).read_text())
ok = fail = 0
for doc in docs:
    title = doc.get("title") or doc["id"]
    out = dest / f"{title}.pem"
    r = subprocess.run(
        ["op", "document", "get", doc["id"], "--output", str(out)],
        capture_output=True,
        text=True,
        timeout=60,
    )
    if r.returncode != 0 or not out.is_file():
        print(f"FAIL {title}", file=sys.stderr)
        fail += 1
        continue
    out.chmod(0o600)
    chk = subprocess.run(
        ["ssh-keygen", "-l", "-f", str(out)],
        capture_output=True,
        text=True,
    )
    if chk.returncode != 0:
        print(f"NO_SSH {title}", file=sys.stderr)
        fail += 1
        continue
    bits = (chk.stdout.split() or ["?"])[0]
    ktype = (chk.stdout.split() or ["?"])[-1]
    print(f"OK {title} bits={bits} type={ktype}")
    ok += 1
print(f"sync ok={ok} fail={fail}")
sys.exit(1 if fail and not ok else 0)
PY

# plantilla de hosts si no existe
if [ ! -f "$DEST/hosts.env" ]; then
  skill_dir="$(cd "$(dirname "$0")/.." && pwd)"
  if [ -f "$skill_dir/references/hosts.example" ]; then
    cp "$skill_dir/references/hosts.example" "$DEST/hosts.env"
    chmod 600 "$DEST/hosts.env"
    echo "creado $DEST/hosts.env (rellena usuario@host)"
  fi
fi
