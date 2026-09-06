#!/usr/bin/env bash
# Instala skills VBS en macOS/Linux (symlinks).
set -euo pipefail
REPO="$(cd "$(dirname "$0")/.." && pwd)"
SRC="$REPO/.cursor/skills"
DEST="${HOME}/.cursor/skills"
RULES="${HOME}/.cursor/rules"
mkdir -p "$DEST" "$RULES"

link() {
  local link="$1" target="$2"
  mkdir -p "$(dirname "$link")"
  rm -f "$link" 2>/dev/null || true
  if [ -e "$link" ] && [ ! -L "$link" ]; then
    echo "AVISO: $link existe y no es symlink; no lo toco."
    return
  fi
  ln -sfn "$target" "$link"
  echo "OK $link -> $target"
}

link "$DEST/generales" "$SRC/generales"
link "$DEST/proyectos" "$SRC/proyectos"
link "$DEST/usar-skills-vbs" "$SRC/usar-skills-vbs"
link "$DEST/mantener-skills-vbs" "$SRC/mantener-skills-vbs"
link "$DEST/ssh-servidores" "$SRC/generales/ssh-servidores"
link "$DEST/hermes-setup-and-maintenance" "$SRC/proyectos/hermes-vbs/hermes-setup-and-maintenance"
link "$DEST/chatwoot-vbs" "$SRC/proyectos/chatwoot-vbs/chatwoot-vbs"
cp -f "$REPO/.cursor/rules/skills-vbs-sync.mdc" "$RULES/skills-vbs-sync.mdc"
echo "Listo. git pull en $REPO."
