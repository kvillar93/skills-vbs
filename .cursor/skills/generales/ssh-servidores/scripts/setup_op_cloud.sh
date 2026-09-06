#!/usr/bin/env bash
# Instala 1Password CLI en una VM Linux (Cloud Agent). Idempotente.
# No imprime secretos. Requiere OP_SERVICE_ACCOUNT_TOKEN ya inyectado.
set -euo pipefail

if command -v op >/dev/null 2>&1; then
  echo "op ya instalado: $(op --version 2>/dev/null || true)"
else
  ARCH="$(uname -m)"
  case "$ARCH" in
    x86_64|amd64) OP_ARCH="amd64" ;;
    aarch64|arm64) OP_ARCH="arm64" ;;
    *) echo "Arquitectura no soportada: $ARCH" >&2; exit 1 ;;
  esac
  TMP="$(mktemp -d)"
  trap 'rm -rf "$TMP"' EXIT
  curl -fsSL "https://cache.agilebits.com/dist/1P/op2/pkg/v2.31.1/op_linux_${OP_ARCH}_v2.31.1.zip" -o "$TMP/op.zip"
  unzip -qo "$TMP/op.zip" -d "$TMP"
  install -m 0755 "$TMP/op" /usr/local/bin/op
  echo "op instalado: $(op --version)"
fi

if [[ -z "${OP_SERVICE_ACCOUNT_TOKEN:-}" ]]; then
  echo "Falta OP_SERVICE_ACCOUNT_TOKEN. Añádelo como Runtime Secret en Cursor." >&2
  exit 2
fi

op vault list --format=json >/dev/null
echo "Sesión de service account ok (vaults accesibles)."
