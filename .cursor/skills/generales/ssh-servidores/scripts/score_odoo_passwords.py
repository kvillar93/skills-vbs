#!/usr/bin/env python3
"""Puntua claves Odoo/Postgres en el host. NUNCA imprime secretos."""
import base64
import configparser
import hashlib
import hmac
import os
import re
import subprocess
import sys

COMMON = {
    "admin", "odoo", "postgres", "password", "123456", "1234", "12345",
    "admin123", "odoo123", "changeme", "master", "secret", "pass",
    "qwerty", "letmein", "welcome", "root", "test", "test123",
    "Admin", "Odoo", "Password", "admin1", "odooadmin",
}

DEFAULT_USER_PW = [
    "admin", "odoo", "Admin", "123456", "1234", "password",
    "odoo123", "admin123", "changeme", "master", "test",
]


def kv(k, v):
    print(f"{k}={v}")


def find_conf():
    candidates = [
        "/etc/odoo-server.conf",
        "/etc/odoo/odoo.conf",
        "/etc/odoo.conf",
        "/opt/odoo/odoo.conf",
    ]
    for p in candidates:
        if os.path.isfile(p) and os.access(p, os.R_OK):
            return p
    try:
        out = subprocess.check_output(
            [
                "sudo", "-n", "find", "/etc", "/opt", "-maxdepth", "4",
                "(", "-name", "odoo-server.conf", "-o", "-name", "odoo.conf", ")",
            ],
            text=True,
            stderr=subprocess.DEVNULL,
        )
        for line in out.splitlines():
            if line.strip():
                return line.strip()
    except Exception:
        pass
    return ""


def read_file(path):
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            return fh.read()
    except PermissionError:
        return subprocess.check_output(["sudo", "-n", "cat", path], text=True, stderr=subprocess.DEVNULL)


def parse_options(text):
    cfg = configparser.ConfigParser(interpolation=None)
    try:
        cfg.read_string(text)
    except Exception:
        return {}
    if cfg.has_section("options"):
        return {k: v for k, v in cfg.items("options")}
    if cfg.sections():
        sec = cfg.sections()[0]
        return {k: v for k, v in cfg.items(sec)}
    return {}


def charset(s):
    flags = []
    if any(c.islower() for c in s):
        flags.append("min")
    if any(c.isupper() for c in s):
        flags.append("may")
    if any(c.isdigit() for c in s):
        flags.append("num")
    if any(not c.isalnum() for c in s):
        flags.append("sim")
    return "+".join(flags) if flags else "none"


def verdict(s, missing):
    if missing:
        return "ausente"
    if s is None or s == "":
        return "vacia"
    low = s.lower()
    if s in COMMON or low in COMMON:
        return "debil_comun"
    kinds = charset(s).count("+") + (0 if charset(s) == "none" else 1)
    n = len(s)
    if n < 10:
        return "debil_corta"
    if n < 12:
        return "debil_corta" if kinds < 3 else "media"
    if n >= 16 and kinds >= 3:
        return "fuerte"
    if n >= 12 and kinds >= 2:
        return "media"
    return "debil_simple"


def fp(s):
    if not s:
        return "-"
    return hashlib.sha256(s.encode("utf-8", "replace")).hexdigest()[:12]


def b64_adapt_decode(data):
    data = data.replace(".", "+")
    pad = "=" * ((4 - len(data) % 4) % 4)
    return base64.b64decode(data + pad)


def verify_pbkdf2_sha512(password, stored):
    # $pbkdf2-sha512$rounds$salt$hash
    parts = stored.split("$")
    if len(parts) < 5 or parts[1] != "pbkdf2-sha512":
        return False
    try:
        rounds = int(parts[2])
        salt = b64_adapt_decode(parts[3])
        expected = b64_adapt_decode(parts[4])
    except Exception:
        return False
    dk = hashlib.pbkdf2_hmac("sha512", password.encode("utf-8"), salt, rounds, dklen=len(expected))
    return hmac.compare_digest(dk, expected)


def check_admin_login_hash(db):
    q = "SELECT COALESCE(password, '') FROM res_users WHERE id = 2 OR login = 'admin' ORDER BY id LIMIT 1"
    try:
        raw = subprocess.check_output(
            ["sudo", "-n", "-u", "postgres", "psql", "-d", db, "-Atc", q],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return "sin_hash"
    if not raw:
        return "sin_hash"
    if raw.startswith("$pbkdf2-sha512$"):
        for pw in DEFAULT_USER_PW:
            if verify_pbkdf2_sha512(pw, raw):
                return "default_si"
        return "hash_ok_no_default"
    if raw.startswith("$"):
        return "hash_otro_formato"
    if len(raw) == 32 and re.fullmatch(r"[0-9a-f]+", raw):
        return "md5_inseguro"
    return "texto_o_desconocido"


def pg_hba_trust():
    try:
        out = subprocess.check_output(
            ["sudo", "-n", "sh", "-c", "grep -hE '^[^#].*trust' /etc/postgresql/*/main/pg_hba.conf 2>/dev/null | head -8"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return "unknown"
    return "si" if out else "no"


def main():
    conf = find_conf()
    kv("CONF", conf or "notfound")
    admin_pw = None
    db_pw = None
    db_user = ""
    db_name = ""
    admin_missing = True
    dbpw_missing = True
    if conf:
        opts = parse_options(read_file(conf))
        # configparser lowercases keys
        admin_missing = "admin_passwd" not in opts
        dbpw_missing = "db_password" not in opts
        admin_pw = opts.get("admin_passwd", "")
        db_pw = opts.get("db_password", "")
        db_user = opts.get("db_user", "")
        db_name = opts.get("db_name", "")
    kv("ADMIN_PASSWD_PRESENT", "no" if admin_missing else "si")
    kv("ADMIN_PASSWD_LEN", 0 if admin_missing else len(admin_pw or ""))
    kv("ADMIN_PASSWD_CHARSET", charset(admin_pw or "") if not admin_missing else "-")
    kv("ADMIN_PASSWD_VERDICT", verdict(admin_pw, admin_missing))
    kv("ADMIN_PASSWD_FP", fp(admin_pw) if not admin_missing else "-")
    kv("DB_PASSWORD_PRESENT", "no" if dbpw_missing else "si")
    kv("DB_PASSWORD_LEN", 0 if dbpw_missing else len(db_pw or ""))
    kv("DB_PASSWORD_CHARSET", charset(db_pw or "") if not dbpw_missing else "-")
    kv("DB_PASSWORD_VERDICT", verdict(db_pw, dbpw_missing))
    kv("DB_PASSWORD_FP", fp(db_pw) if not dbpw_missing else "-")
    kv("SAME_ADMIN_DBPW", "si" if (not admin_missing and not dbpw_missing and admin_pw == db_pw and admin_pw) else "no")
    kv("DB_USER_SET", "si" if db_user else "no")
    kv("DB_NAME_SET", "si" if db_name else "no")
    kv("PG_HBA_TRUST", pg_hba_trust())
    try:
        has_pw = subprocess.check_output(
            ["sudo", "-n", "-u", "postgres", "psql", "-Atc",
             "SELECT rolname || ':' || (rolpassword IS NOT NULL)::text FROM pg_authid WHERE rolname IN ('odoo','postgres') ORDER BY rolname"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip().replace("\n", ";")
    except Exception:
        has_pw = "unavailable"
    kv("PG_ROLE_HAS_PASSWORD", has_pw or "unavailable")

    dbs = []
    try:
        raw = subprocess.check_output(
            ["sudo", "-n", "-u", "postgres", "psql", "-Atc",
             "SELECT datname FROM pg_database WHERE datistemplate=false AND datname <> 'postgres'"],
            text=True,
            stderr=subprocess.DEVNULL,
        )
        dbs = [x.strip() for x in raw.splitlines() if x.strip()]
    except Exception:
        dbs = []
    hits = []
    for db in dbs[:8]:
        result = check_admin_login_hash(db)
        if result in {"default_si", "md5_inseguro", "texto_o_desconocido"}:
            hits.append(f"{db}:{result}")
    kv("ADMIN_LOGIN", ",".join(hits) if hits else ("ok_no_default" if dbs else "sin_db"))
    kv("ADMIN_LOGIN_DBS", len(dbs))
    kv("DONE", 1)


if __name__ == "__main__":
    main()
