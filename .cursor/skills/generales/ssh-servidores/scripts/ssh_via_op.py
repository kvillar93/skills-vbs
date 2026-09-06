#!/usr/bin/env python3
"""SSH para Cloud Agents: pide la PEM a 1Password, conecta, borra el temp.

Uso:
    python ssh_via_op.py vbs-hermes -- whoami
    python ssh_via_op.py tsheila --pem odoo_xolver -- whoami && hostname

No imprime la clave ni el token. Hosts password: sale con código 2.
"""

from __future__ import annotations

import argparse
import os
import stat
import subprocess
import sys
import tempfile
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from vault_map import (
    VAULT_NOMBRE,
    destino_para_alias,
    es_host_password,
    es_sesion_nube,
    item_para_alias,
    referencias_clave_privada,
)

OP = os.environ.get("OP_BIN", "op")
SSH = os.environ.get("SSH_BIN", "ssh")


def _fail(msg: str, code: int = 1) -> int:
    print(msg, file=sys.stderr)
    return code


def main() -> int:
    parser = argparse.ArgumentParser(description="SSH vía 1Password (Cloud)")
    parser.add_argument("alias", help="Alias de ~/.ssh/config o hosts.md")
    parser.add_argument(
        "--pem",
        dest="pem",
        default=None,
        help="Nombre de PEM/ítem si el alias no está en hosts.md",
    )
    args, resto = parser.parse_known_args()
    if resto[:1] == ["--"]:
        resto = resto[1:]
    alias = args.alias

    if es_host_password(alias):
        return _fail(
            f"El host '{alias}' usa password. No se automatiza. Ábrelo en Tabby "
            "o en un terminal interactivo.",
            2,
        )

    if not os.environ.get("OP_SERVICE_ACCOUNT_TOKEN"):
        who = subprocess.run(
            [OP, "whoami"],
            capture_output=True,
            text=True,
        )
        if who.returncode != 0:
            return _fail(
                "No hay OP_SERVICE_ACCOUNT_TOKEN ni sesión de `op`. "
                "En Cloud Agents: añade el Runtime Secret en el dashboard de Cursor. "
                "No lo pegues en el chat."
            )

    try:
        dest = destino_para_alias(alias)
        titulo = item_para_alias(alias, args.pem or dest.pem)
    except ValueError as exc:
        return _fail(str(exc))
    if not dest.usuario:
        return _fail(f"El host '{alias}' no tiene usuario en hosts.md.")

    pem = ""
    ultimo_error = "sin intentos"
    doc = subprocess.run(
        [OP, "document", "get", titulo, "--vault", VAULT_NOMBRE],
        capture_output=True,
        text=True,
    )
    if doc.returncode == 0 and "PRIVATE KEY" in (doc.stdout or ""):
        pem = doc.stdout
    else:
        for ref in referencias_clave_privada(titulo):
            fetched = subprocess.run(
                [OP, "read", ref],
                capture_output=True,
                text=True,
            )
            if fetched.returncode == 0 and "PRIVATE KEY" in (fetched.stdout or ""):
                pem = fetched.stdout
                break
            err = (fetched.stderr or "").strip().splitlines()
            ultimo_error = err[0] if err else "op read falló"
            if "BEGIN" in ultimo_error or "PRIVATE" in ultimo_error:
                ultimo_error = "op read falló (detalle oculto)"
    doc = None
    fetched = None
    if not pem:
        return _fail(f"Falta el ítem {titulo} en el vault SSH-Infra. {ultimo_error}")

    fd, tmp_name = tempfile.mkstemp(prefix="op-ssh-", suffix=".pem")
    tmp = Path(tmp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(pem)
            if not pem.endswith("\n"):
                fh.write("\n")
        pem = ""
        try:
            os.chmod(tmp, stat.S_IRUSR | stat.S_IWUSR)
        except OSError:
            pass
        remoto = list(resto)
        cmd = [
            SSH,
            "-i",
            str(tmp),
            "-p",
            str(dest.puerto),
            "-o",
            "IdentitiesOnly=yes",
            "-o",
            "BatchMode=yes",
            "-o",
            "ConnectTimeout=15",
        ]
        if es_sesion_nube():
            cmd.extend(["-o", "StrictHostKeyChecking=accept-new"])
        cmd.extend([f"{dest.usuario}@{dest.hostname}", *remoto])
        ran = subprocess.run(cmd)
        return ran.returncode
    finally:
        pem = ""
        try:
            tmp.write_text("x", encoding="utf-8")
            tmp.unlink(missing_ok=True)
        except OSError:
            pass


if __name__ == "__main__":
    raise SystemExit(main())
