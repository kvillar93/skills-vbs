"""Mapa no secreto: alias/PEM -> item de 1Password.

No lee claves ni habla con la CLI. Solo nombres.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

VAULT_NOMBRE = "SSH-Infra"
HOSTS_MD = Path(__file__).resolve().parents[1] / "hosts.md"

NOMBRES_PEM = (
    "externo",
    "fpaxv3",
    "OdooEPX",
    "odoo_xolver",
    "umbrafinance",
    "vbsolutions",
    "vvl",
)

# alias canónico -> título del Login en el vault
ALIASES_PASSWORD = {
    "aurora": "aurora",
    "backup-sti": "backup-sti",
    "odoo-quickbooks-jean": "odoo-quickbooks-jean",
    "power-bi-server": "power-bi-server",
    "sti-nuevo": "sti-nuevo",
    "sti-nuevo-server": "sti-nuevo",
    "ssh-tercero-stocaklu": "stockalu-tercero",
    "stockalu-tercero": "stockalu-tercero",
}

# alias extra que no coinciden con el slug de hosts.md
ALIASES_A_PEM = {
    "75g-vbs": "vbsolutions",
    "ashtonschool-sd": "vbsolutions",
    "encf-vbs": "vbsolutions",
    "nmp-guud": "vbsolutions",
    "perm": "vbsolutions",
    "saas-vbs": "vbsolutions",
    "umbra-finance": "umbrafinance",
    "vwc": "vbsolutions",
    "75grados": "odoo_xolver",
    "farmaciasvip": "odoo_xolver",
    "gtiseguridad": "odoo_xolver",
    "saas-lifter": "odoo_xolver",
    "vvl-ppk": "vvl",
}


def _canon(alias: str) -> str:
    return alias.strip().lower().strip("`")


@dataclass(frozen=True)
class DestinoSsh:
    alias: str
    hostname: str
    usuario: str
    puerto: int
    auth: str
    pem: str | None

    @property
    def es_password(self) -> bool:
        return self.auth.lower() == "password" or not self.pem


def es_sesion_nube() -> bool:
    """Cloud Agent / VM remota: token SA o socket OIDC de Cursor."""
    if os.environ.get("OP_SERVICE_ACCOUNT_TOKEN"):
        return True
    if Path("/run/cursor/api.sock").exists():
        return True
    return os.environ.get("CURSOR_CLOUD_AGENT", "").lower() in {"1", "true", "yes"}


def _aliases_de_celda(celda: str) -> list[str]:
    nombres = re.findall(r"`([^`]+)`", celda)
    nombres.extend(re.findall(r"\(([^)]+)\)", celda))
    return [_canon(n) for n in nombres if n.strip()]


@lru_cache(maxsize=1)
def destinos() -> dict[str, DestinoSsh]:
    """Todos los alias de hosts.md (hostname/usuario/puerto/pem)."""
    if not HOSTS_MD.is_file():
        return {}
    mapa: dict[str, DestinoSsh] = {}
    for line in HOSTS_MD.read_text(encoding="utf-8").splitlines():
        if not line.startswith("| `"):
            continue
        celdas = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(celdas) < 7:
            continue
        hostname = celdas[2].strip("`").strip()
        usuario = celdas[3].strip("`").strip()
        if usuario in {"", "—", "-"}:
            usuario = ""
        try:
            puerto = int(celdas[4])
        except ValueError:
            puerto = 22
        auth = celdas[5].strip()
        pem_raw = celdas[6].strip("`").strip()
        pem = None if pem_raw in {"", "—", "-", "NO CONVERTIDA"} else pem_raw
        aliases = _aliases_de_celda(celdas[0])
        if not aliases or not hostname:
            continue
        dest = DestinoSsh(
            alias=aliases[0],
            hostname=hostname,
            usuario=usuario or "ubuntu",
            puerto=puerto,
            auth=auth,
            pem=pem,
        )
        for alias in aliases:
            mapa[alias] = dest
    return mapa


def destino_para_alias(alias: str) -> DestinoSsh:
    dest = destinos().get(_canon(alias))
    if dest is None:
        raise ValueError(
            f"Alias '{alias}' no está en hosts.md. Revisa el inventario de ssh-servidores."
        )
    return dest


@lru_cache(maxsize=1)
def _aliases_desde_hosts() -> dict[str, str]:
    """alias -> nombre PEM, leído de hosts.md (sin secretos)."""
    if not HOSTS_MD.is_file():
        return {}
    mapa: dict[str, str] = {}
    for line in HOSTS_MD.read_text(encoding="utf-8").splitlines():
        if not line.startswith("| `"):
            continue
        celdas = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(celdas) < 7:
            continue
        pem = celdas[6].strip("`").strip()
        if pem in {"", "—", "-", "NO CONVERTIDA"}:
            continue
        for alias in re.findall(r"`([^`]+)`", celdas[0]):
            mapa[_canon(alias)] = pem
        extra = re.findall(r"\(([^)]+)\)", celdas[0])
        for alias in extra:
            mapa[_canon(alias)] = pem
    return mapa


def nombres_pem() -> tuple[str, ...]:
    return NOMBRES_PEM


def aliases_password() -> dict[str, str]:
    return dict(ALIASES_PASSWORD)


def item_para_pem(nombre_pem: str) -> str:
    nombre = nombre_pem.strip()
    if nombre not in NOMBRES_PEM:
        raise ValueError(f"PEM desconocida: {nombre}")
    return nombre


def es_host_password(alias: str) -> bool:
    if _canon(alias) in ALIASES_PASSWORD:
        return True
    dest = destinos().get(_canon(alias))
    return bool(dest and dest.es_password)


def item_para_alias(alias: str, pem_de_hosts: str | None = None) -> str:
    """Devuelve el título del ítem SSH Key o Login.

    pem_de_hosts: columna 'Clave PEM' de hosts.md (o None si no se conoce).
    """
    clave = _canon(alias)
    if clave in ALIASES_PASSWORD:
        return ALIASES_PASSWORD[clave]
    if clave in ALIASES_A_PEM:
        return ALIASES_A_PEM[clave]
    if pem_de_hosts and pem_de_hosts.strip() not in {"", "—", "-", "NO CONVERTIDA"}:
        return item_para_pem(pem_de_hosts.strip())
    pem_hosts = _aliases_desde_hosts().get(clave)
    if pem_hosts:
        return item_para_pem(pem_hosts)
    # muchos aliases se llaman distinto a la PEM; el caller debe pasar pem_de_hosts
    raise ValueError(
        f"No pude resolver el ítem de 1Password para el alias '{alias}'. "
        "Pasa el nombre de PEM desde hosts.md."
    )


def referencia_clave_privada(titulo_item: str) -> str:
    return f"op://{VAULT_NOMBRE}/{titulo_item}/private key?ssh-format=openssh"


def referencias_clave_privada(titulo_item: str) -> tuple[str, ...]:
    """Orden de lectura: documento PEM, luego campo SSH Key nativo."""
    return (
        f"op://{VAULT_NOMBRE}/{titulo_item}/{titulo_item}.pem",
        f"op://{VAULT_NOMBRE}/{titulo_item}",
        f"op://{VAULT_NOMBRE}/{titulo_item}/private key?ssh-format=openssh",
    )
