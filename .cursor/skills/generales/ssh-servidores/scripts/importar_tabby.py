#!/usr/bin/env python3
"""Importa perfiles SSH de Tabby: convierte .ppk a PEM y regenera ~/.ssh/config.

Usa puttykeys (https://github.com/scriptjunkie/puttykeys) en local.
No usa puttygen ni sube claves a la nube.
No escribe contraseñas ni material de claves en stdout ni en el inventario.
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from urllib.parse import unquote

import yaml

TABBY_CONFIG = Path(os.environ.get("TABBY_CONFIG", r"C:\Users\kevin\AppData\Roaming\tabby\config.yaml"))
SSH_DIR = Path.home() / ".ssh"
SKILL_DIR = Path(__file__).resolve().parents[1]
SSH_KEYGEN = Path(r"C:\Windows\System32\OpenSSH\ssh-keygen.exe")

KEY_MAP = {
    r"G:\My Drive\Lifter\Operaciones\Herramientas\Odoo Xolver.ppk": "odoo_xolver",
    r"G:\My Drive\VB solutions\Herramientas instancias\vbsolutions.ppk": "vbsolutions",
    r"G:\My Drive\VB solutions\BMCargo\Server Google\private_odoo.ppk": "private_odoo",
    r"G:\My Drive\VB solutions\Herramientas instancias\fpaxv3.ppk": "fpaxv3",
    r"G:\My Drive\VB solutions\Herramientas instancias\OdooEPX.ppk": "OdooEPX",
    r"G:\My Drive\VB solutions\Herramientas instancias\umbrafinance.ppk": "umbrafinance",
    r"G:\My Drive\VB solutions\VVL\VVL.ppk": "vvl",
    r"G:\My Drive\Lifter\Operaciones\Herramientas\externo": "externo",
}

# Aliases extra (compatibles con el config anterior de mayo 2026)
EXTRA_ALIASES = {
    "75 Grados": ["75grados"],
    "75 Grados VBSOLUTIONS": ["75g-vbs"],
    "ASHTON SCHOOL SANTO DOMINGO": ["ashtonschool-sd"],
    "ENCF LIFTER": ["encf-lifter"],
    "ENCF VBSOLUTIONS": ["encf-vbs"],
    "Farmacia VIP": ["farmaciasvip"],
    "GTI": ["gtiseguridad"],
    "LIFTER": ["lifter"],
    "NMP (GUUD STORE)": ["nmp-guud"],
    "ODOO TEST (VBSOLU)": ["odoo-test-vbsolu"],
    "ODOO TEST VBS": ["odoo-test-vbs"],
    "PERMESA": ["perm"],
    "SAAS": ["saas-lifter"],
    "SAAS VBS": ["saas-vbs"],
    "SSH TERCERO STOCAKLU": ["stockalu-tercero"],
    "STI NUEVO SERVER": ["sti-nuevo"],
    "Soluciones Contables": ["soluciones-contables"],
    "UMBRA Finance copy": ["umbra-finance"],
    "VBS HERMES": ["vbs-hermes"],
    "VBS HERMES-CHATWOOT": ["vbs-hermes-chatwoot"],
    "VVL PPK": ["vvl-ppk"],
    "VISIONARY": ["visionary"],
    "VALDESIA WATER COMPANY (VWC)": ["vwc"],
}


def file_from_uri(value) -> str | None:
    if not value:
        return None
    text = str(value).strip()
    if text.startswith("file://"):
        text = text[7:]
    return unquote(text)


def slug(name: str) -> str:
    s = name.strip().lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")


def normalize_key_path(path: str) -> str:
    return os.path.normcase(os.path.normpath(path))


def key_dest_name(ppk_path: str) -> str | None:
    wanted = normalize_key_path(ppk_path)
    for src, dest in KEY_MAP.items():
        if normalize_key_path(src) == wanted:
            return dest
    base = Path(ppk_path).stem
    return slug(base) or None


def ppk_encryption(path: Path) -> str:
    with path.open("r", encoding="latin1") as fh:
        for _ in range(4):
            line = fh.readline()
            if line.lower().startswith("encryption:"):
                return line.split(":", 1)[1].strip().lower()
    return "unknown"


def write_public_key(private_path: Path) -> None:
    if not SSH_KEYGEN.is_file():
        return
    pub = Path(str(private_path) + ".pub")
    result = subprocess.run(
        [str(SSH_KEYGEN), "-y", "-f", str(private_path)],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0 and result.stdout.strip().startswith("ssh-"):
        pub.write_text(result.stdout.strip() + "\n", encoding="ascii")


def protect_windows_acl(path: Path) -> None:
    user = os.environ.get("USERNAME") or os.getlogin()
    subprocess.run(
        ["icacls", str(path), "/inheritance:r"],
        check=False,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        ["icacls", str(path), "/grant:r", f"{user}:(R)"],
        check=False,
        capture_output=True,
        text=True,
    )


def convert_keys() -> dict[str, str]:
    """Devuelve mapa path-ppk-normalizado -> path PEM local."""
    SSH_DIR.mkdir(parents=True, exist_ok=True)
    converted: dict[str, str] = {}
    seen: set[str] = set()

    with TABBY_CONFIG.open(encoding="utf-8") as fh:
        data = yaml.safe_load(fh)

    sources: list[str] = []
    for profile in data.get("profiles") or []:
        if not isinstance(profile, dict) or profile.get("type") != "ssh":
            continue
        for raw in (profile.get("options") or {}).get("privateKeys") or []:
            src = file_from_uri(raw)
            if src:
                sources.append(src)

    for src in sources:
        key = normalize_key_path(src)
        if key in seen:
            continue
        seen.add(key)
        src_path = Path(src)
        dest_name = key_dest_name(src)
        if not dest_name:
            print(f"SKIP sin nombre destino: {src_path.name}", file=sys.stderr)
            continue
        dest = SSH_DIR / dest_name

        if not src_path.is_file():
            print(f"FALTA archivo: {src}", file=sys.stderr)
            continue

        if src_path.suffix.lower() != ".ppk":
            if dest.is_file() and dest.stat().st_size > 200:
                converted[key] = str(dest)
                print(f"YA EXISTE {dest.name} ({dest.stat().st_size} bytes)")
                continue
            try:
                dest.unlink(missing_ok=True)
            except PermissionError:
                subprocess.run(
                    ["icacls", str(dest), "/grant:r", f"{os.environ.get('USERNAME')}:(F)"],
                    capture_output=True,
                    text=True,
                )
                dest.unlink(missing_ok=True)
            shutil.copy2(src_path, dest)
            protect_windows_acl(dest)
            write_public_key(dest)
            converted[key] = str(dest)
            print(f"COPIADO {src_path.name} -> {dest.name} ({dest.stat().st_size} bytes)")
            continue

        enc = ppk_encryption(src_path)
        if enc not in {"none", "null"}:
            print(f"PASSPHRASE requerida ({enc}): {src_path.name} -> no convertida")
            continue

        if dest.is_file() and dest.stat().st_size > 200:
            header = dest.read_text(encoding="ascii", errors="replace").splitlines()[:1]
            if header and "BEGIN" in header[0] and "PRIVATE KEY" in header[0]:
                converted[key] = str(dest)
                print(f"YA EXISTE PEM {dest.name} ({dest.stat().st_size} bytes)")
                continue

        try:
            import puttykeys
        except ImportError as exc:
            raise SystemExit(
                "Falta puttykeys. Instala local: python -m pip install --user puttykeys"
            ) from exc

        pem = puttykeys.ppkraw_to_openssh(src_path.read_text(encoding="latin1"))
        if not pem or "BEGIN" not in pem or len(pem) < 200:
            print(f"ERROR convirtiendo {src_path.name}: PEM invalido", file=sys.stderr)
            continue
        try:
            dest.write_text(pem if pem.endswith("\n") else pem + "\n", encoding="ascii")
        except PermissionError:
            subprocess.run(
                ["icacls", str(dest), "/grant:r", f"{os.environ.get('USERNAME')}:(F)"],
                capture_output=True,
                text=True,
            )
            dest.write_text(pem if pem.endswith("\n") else pem + "\n", encoding="ascii")
        protect_windows_acl(dest)
        write_public_key(dest)
        converted[key] = str(dest)
        header = pem.splitlines()[0]
        print(f"CONVERTIDA {src_path.name} -> {dest.name} ({dest.stat().st_size} bytes, {header})")

    return converted


def load_profiles():
    with TABBY_CONFIG.open(encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    rows = []
    used_aliases: dict[str, str] = {}
    for profile in data.get("profiles") or []:
        if not isinstance(profile, dict) or profile.get("type") != "ssh":
            continue
        name = profile.get("name") or ""
        opt = profile.get("options") or {}
        alias = slug(name)
        if alias in used_aliases:
            alias = f"{alias}-2"
        used_aliases[alias] = name
        extras = [a for a in EXTRA_ALIASES.get(name, []) if a != alias]
        keys = [file_from_uri(k) for k in (opt.get("privateKeys") or [])]
        keys = [k for k in keys if k]
        forwards = []
        for fwd in opt.get("forwardedPorts") or []:
            if not isinstance(fwd, dict):
                continue
            forwards.append(
                {
                    "type": fwd.get("type"),
                    "listen_host": fwd.get("host") or "127.0.0.1",
                    "listen_port": fwd.get("port"),
                    "target": fwd.get("targetAddress"),
                    "target_port": fwd.get("targetPort"),
                    "description": fwd.get("description") or "",
                }
            )
        rows.append(
            {
                "name": name,
                "alias": alias,
                "extras": extras,
                "host": opt.get("host"),
                "user": opt.get("user"),
                "port": opt.get("port") or 22,
                "auth": opt.get("auth") or "publicKey",
                "keys": keys,
                "forwards": forwards,
            }
        )
    return rows


def posix_identity(path: str) -> str:
    return Path(path).as_posix()


def write_ssh_config(rows, converted: dict[str, str]) -> Path:
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [
        f"# Generado desde Tabby ({TABBY_CONFIG}) — {stamp}",
        "# No editar a mano: regenerar con scripts/importar_tabby.py",
        "# Las contraseñas NUNCA se copian aqui.",
        "",
        "Host *",
        "    ServerAliveInterval 30",
        "    ServerAliveCountMax 3",
        "    HashKnownHosts yes",
        "",
    ]

    groups = defaultdict(list)
    for row in rows:
        host = (row["host"] or "").lower()
        if "lifterdo.com" in host or row["alias"] in {"xolver", "plastivo"}:
            group = "LIFTER"
        elif "vbsolutions" in host or row["alias"].startswith("vbs-"):
            group = "VBSOLUTIONS"
        elif row["auth"] == "password":
            group = "PASSWORD"
        else:
            group = "OTROS"
        groups[group].append(row)

    inventory_lines = [
        "# Inventario SSH importado desde Tabby",
        "",
        "Alias para `ssh <alias>`. Las claves PEM viven en `~/.ssh/` (nunca en este archivo).",
        "",
        "| Alias | Nombre Tabby | Host | Usuario | Puerto | Auth | Clave PEM |",
        "|---|---|---|---|---|---|---|",
    ]

    for group in ("VBSOLUTIONS", "LIFTER", "OTROS", "PASSWORD"):
        if group not in groups:
            continue
        lines.append(f"# === {group} ===")
        lines.append("")
        for row in groups[group]:
            names = " ".join([row["alias"], *row["extras"]])
            lines.append(f"Host {names}")
            if row["host"]:
                lines.append(f"    HostName {row['host']}")
            if row["user"]:
                lines.append(f"    User {row['user']}")
            if row["port"] and int(row["port"]) != 22:
                lines.append(f"    Port {row['port']}")

            pem = None
            if row["auth"] == "publicKey" and row["keys"]:
                pem = converted.get(normalize_key_path(row["keys"][0]))
                if pem:
                    lines.append(f'    IdentityFile "{posix_identity(pem)}"')
                    lines.append("    IdentitiesOnly yes")
                    lines.append("    PreferredAuthentications publickey")
                else:
                    lines.append(f"    # Clave no convertida: {Path(row['keys'][0]).name}")
            elif row["auth"] == "password":
                lines.append("    PreferredAuthentications password,keyboard-interactive")
                lines.append("    # Auth por password: SSH pedira la clave de forma interactiva.")

            for fwd in row["forwards"]:
                if fwd["type"] == "Local" and fwd["listen_port"] and fwd["target"] and fwd["target_port"]:
                    listen = f"{fwd['listen_host']}:{fwd['listen_port']}" if fwd["listen_host"] not in {"127.0.0.1", "localhost"} else str(fwd["listen_port"])
                    comment = f"    # {fwd['description']}" if fwd["description"] else "    # LocalForward"
                    lines.append(comment)
                    lines.append(f"    LocalForward {listen} {fwd['target']}:{fwd['target_port']}")

            lines.append("")
            pem_name = Path(pem).name if pem else ("—" if row["auth"] != "publicKey" else "NO CONVERTIDA")
            extras = f" ({', '.join(row['extras'])})" if row["extras"] else ""
            inventory_lines.append(
                f"| `{row['alias']}`{extras} | {row['name']} | `{row['host']}` | {row['user'] or '—'} | {row['port']} | {row['auth']} | `{pem_name}` |"
            )
        lines.append("")

    config_path = SSH_DIR / "config"
    config_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    (SKILL_DIR / "hosts.md").write_text("\n".join(inventory_lines) + "\n", encoding="utf-8")
    return config_path


def main() -> int:
    print("Convirtiendo claves...")
    converted = convert_keys()
    print(f"Claves listas: {len(converted)}")
    rows = load_profiles()
    print(f"Perfiles SSH: {len(rows)}")
    path = write_ssh_config(rows, converted)
    print(f"Config escrito: {path}")
    print(f"Inventario: {SKILL_DIR / 'hosts.md'}")
    missing = [r["name"] for r in rows if r["auth"] == "publicKey" and r["keys"] and normalize_key_path(r["keys"][0]) not in converted]
    if missing:
        print("Perfiles publicKey sin PEM:")
        for name in missing:
            print(f"  - {name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
