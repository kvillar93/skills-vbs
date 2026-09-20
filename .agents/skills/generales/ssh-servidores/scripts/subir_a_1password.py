#!/usr/bin/env python3
"""Crea el vault SSH-Infra e importa las PEM locales a 1Password.

No imprime material de claves. No lee Drive. No toca Tabby.

Uso (ya autenticado con `op signin` o app de escritorio):
    python subir_a_1password.py
    python subir_a_1password.py --solo-comprobar
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from vault_map import VAULT_NOMBRE, nombres_pem

SSH_DIR = Path.home() / ".ssh"
OP = os.environ.get("OP_BIN", "op")


def _run_op(args: list[str], *, stdin: str | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [OP, *args],
        input=stdin,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def _fail(msg: str, code: int = 1) -> int:
    print(msg, file=sys.stderr)
    return code


def asegurar_sesion() -> str | None:
    who = _run_op(["whoami"])
    if who.returncode != 0:
        return (
            "No hay sesión de 1Password CLI. Abre la app o ejecuta `op signin` "
            "y vuelve a lanzar este script. No pegues tokens en el chat."
        )
    return None


def asegurar_vault() -> str | None:
    listed = _run_op(["vault", "list", "--format=json"])
    if listed.returncode != 0:
        return f"No pude listar vaults: {listed.stderr.strip() or listed.stdout.strip()}"
    try:
        vaults = json.loads(listed.stdout or "[]")
    except json.JSONDecodeError:
        return "La CLI no devolvió JSON de vaults."
    nombres = {v.get("name") for v in vaults if isinstance(v, dict)}
    if VAULT_NOMBRE in nombres:
        print(f"Vault listo: {VAULT_NOMBRE}")
        return None
    created = _run_op(
        ["vault", "create", VAULT_NOMBRE, "--description", "Claves SSH de servidores (Cursor)"]
    )
    if created.returncode != 0:
        return (
            f"No pude crear el vault {VAULT_NOMBRE}. Créalo a mano en 1password.com "
            f"y reintenta. Detalle: {created.stderr.strip() or created.stdout.strip()}"
        )
    print(f"Vault creado: {VAULT_NOMBRE}")
    return None


def items_existentes() -> set[str]:
    listed = _run_op(["item", "list", "--vault", VAULT_NOMBRE, "--format=json"])
    if listed.returncode != 0:
        return set()
    try:
        items = json.loads(listed.stdout or "[]")
    except json.JSONDecodeError:
        return set()
    return {i.get("title") for i in items if isinstance(i, dict) and i.get("title")}


def _plantilla_ssh(titulo: str, pem_text: str) -> dict:
    return {
        "title": titulo,
        "category": "SSH_KEY",
        "vault": {"name": VAULT_NOMBRE},
        "fields": [
            {
                "id": "private_key",
                "type": "SSHKEY",
                "label": "private key",
                "value": pem_text,
            }
        ],
    }


def importar_pem(nombre: str) -> str:
    """Devuelve un estado corto en español. Nunca incluye el PEM."""
    path = SSH_DIR / nombre
    if not path.is_file():
        return f"FALTA archivo local {path.name}"
    if nombre in items_existentes():
        return f"YA EXISTE ítem {nombre}"

    pem_text = path.read_text(encoding="utf-8", errors="strict")
    if "PRIVATE KEY" not in pem_text.splitlines()[0]:
        return f"RECHAZADA {nombre}: no parece una clave privada"

    fd, tmp_name = tempfile.mkstemp(prefix="op-tpl-", suffix=".json")
    tmp = Path(tmp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(_plantilla_ssh(nombre, pem_text), fh)
        created = _run_op(
            ["item", "create", f"--template={tmp}", "--vault", VAULT_NOMBRE]
        )
        if created.returncode == 0:
            return f"IMPORTADA {nombre}"
        detalle = (created.stderr or created.stdout).strip().splitlines()
        corto = detalle[0] if detalle else "error de CLI"
        if "private" in corto.lower() or "BEGIN" in corto:
            corto = "la CLI rechazó la plantilla (importa este ítem a mano en la app)"
        return f"FALLÓ {nombre}: {corto}"
    finally:
        pem_text = ""
        try:
            tmp.write_text("{}", encoding="utf-8")
            tmp.unlink(missing_ok=True)
        except OSError:
            pass


def preparar_plantillas(destino: Path) -> int:
    """Escribe plantillas JSON para que PowerShell ejecute `op` (app integration)."""
    destino.mkdir(parents=True, exist_ok=True)
    ok = 0
    for nombre in nombres_pem():
        path = SSH_DIR / nombre
        if not path.is_file():
            print(f"FALTA archivo local {nombre}")
            continue
        pem_text = path.read_text(encoding="utf-8", errors="strict")
        if "PRIVATE KEY" not in pem_text.splitlines()[0]:
            print(f"RECHAZADA {nombre}: no parece una clave privada")
            continue
        out = destino / f"{nombre}.json"
        out.write_text(json.dumps(_plantilla_ssh(nombre, pem_text)), encoding="utf-8")
        pem_text = ""
        print(f"PLANTILLA {nombre}")
        ok += 1
    return 0 if ok else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Sube PEM locales al vault SSH-Infra")
    parser.add_argument(
        "--solo-comprobar",
        action="store_true",
        help="Solo lista qué PEM hay en disco y qué ítems faltan",
    )
    parser.add_argument(
        "--preparar-plantillas",
        metavar="DIR",
        help="Solo escribe plantillas JSON en DIR; no llama a op",
    )
    args = parser.parse_args()
    if args.preparar_plantillas:
        return preparar_plantillas(Path(args.preparar_plantillas))

    err = asegurar_sesion()
    if err:
        return _fail(err)

    err = asegurar_vault()
    if err:
        return _fail(err)

    presentes = items_existentes()
    print(f"Ítems ya en {VAULT_NOMBRE}: {len(presentes)}")
    for nombre in nombres_pem():
        local = "sí" if (SSH_DIR / nombre).is_file() else "no"
        remoto = "sí" if nombre in presentes else "no"
        print(f"  {nombre:16} local={local}  vault={remoto}")

    if args.solo_comprobar:
        return 0

    print("Importando (el material no se muestra)...")
    fallos = 0
    for nombre in nombres_pem():
        estado = importar_pem(nombre)
        print(f"  {estado}")
        if estado.startswith("FALLÓ") or estado.startswith("FALTA") or estado.startswith("RECHAZADA"):
            fallos += 1

    print(
        "Listo. Si algún ítem FALLÓ, en la app: Nuevo ítem → SSH Key → "
        "Importar archivo, elige C:\\Users\\kevin\\.ssh\\<nombre>. "
        "No abras esa PEM en Cursor."
    )
    return 1 if fallos else 0


if __name__ == "__main__":
    raise SystemExit(main())
