#!/usr/bin/env python3
"""Orquesta diagnostico SOLO LECTURA en hosts SSH (clave publica)."""
from __future__ import annotations

import json
import os
import re
import ssl
import subprocess
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

SSH = r"C:\Windows\System32\OpenSSH\ssh.exe"
SCRIPT = Path(__file__).with_name("diag_odoo_miner.sh")
OUT_DIR = Path(__file__).with_name("diag-out")
CONFIG = Path.home() / ".ssh" / "config"

SKIP_AUTH = {"password"}
SKIP_ALIASES = {
    "nmp-guud-store",
    "nmp-guud",
    "odoo-test-vbsolu",
    "vvl-ppk",
    "bmcvmod",
    "bmcvmod-test",
    "aurora",
    "backup-sti",
    "odoo-quickbooks-jean",
    "power-bi-server",
    "sti-nuevo-server",
    "sti-nuevo",
    "ssh-tercero-stocaklu",
    "stockalu-tercero",
}


def parse_hosts(path: Path) -> list[dict]:
    text = path.read_text(encoding="utf-8")
    blocks: list[dict] = []
    current: dict | None = None
    for line in text.splitlines():
        if line.startswith("Host ") and not line.startswith("Host *"):
            if current:
                blocks.append(current)
            names = line.split()[1:]
            current = {
                "alias": names[0],
                "aliases": names,
                "hostname": None,
                "user": None,
                "port": "22",
                "auth": "publickey",
            }
            continue
        if current is None:
            continue
        s = line.strip()
        if s.startswith("HostName "):
            current["hostname"] = s.split(None, 1)[1]
        elif s.startswith("User "):
            current["user"] = s.split(None, 1)[1]
        elif s.startswith("Port "):
            current["port"] = s.split(None, 1)[1]
        elif s.startswith("PreferredAuthentications ") and "password" in s:
            current["auth"] = "password"
    if current:
        blocks.append(current)
    seen = set()
    out = []
    for b in blocks:
        alias = b["alias"]
        host = b.get("hostname") or alias
        if alias in SKIP_ALIASES or b["auth"] == "password":
            continue
        key = (host, b.get("user"), b.get("port"))
        if key in seen:
            continue
        seen.add(key)
        out.append(b)
    return out


def parse_kv(text: str) -> dict:
    data = {}
    for line in text.splitlines():
        if "=" not in line:
            continue
        k, v = line.split("=", 1)
        data[k.strip()] = v.strip()
    return data


def check_list_db_http(hostname: str) -> dict:
    payload = b'{"jsonrpc":"2.0","method":"call","id":1,"params":{}}'
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    for scheme in ("https", "http"):
        url = f"{scheme}://{hostname}/web/database/list"
        req = urllib.request.Request(
            url,
            data=payload,
            headers={"Content-Type": "application/json", "User-Agent": "vbs-diag/1"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=8, context=ctx) as resp:
                body = resp.read(8000).decode("utf-8", "replace")
            dbs = None
            try:
                parsed = json.loads(body)
                result = parsed.get("result")
                if isinstance(result, list):
                    dbs = result
                elif isinstance(result, dict) and "databases" in result:
                    dbs = result.get("databases")
            except json.JSONDecodeError:
                pass
            exposed = isinstance(dbs, list)
            return {
                "url": url,
                "ok": True,
                "exposed": exposed,
                "db_count": len(dbs) if exposed else None,
            }
        except Exception as exc:
            last = str(exc.__class__.__name__)
            continue
    return {"url": None, "ok": False, "exposed": False, "error": last}


def run_one(host: dict) -> dict:
    alias = host["alias"]
    t0 = time.time()
    cmd = [
        SSH,
        "-o", "BatchMode=yes",
        "-o", "ConnectTimeout=12",
        "-o", "StrictHostKeyChecking=accept-new",
        "-o", "ServerAliveInterval=5",
        alias,
        "bash -s",
    ]
    script = SCRIPT.read_bytes().replace(b"\r\n", b"\n")
    try:
        proc = subprocess.run(
            cmd,
            input=script,
            capture_output=True,
            timeout=50,
        )
        stdout = proc.stdout.decode("utf-8", "replace")
        stderr = proc.stderr.decode("utf-8", "replace")
        kv = parse_kv(stdout)
        status = "ok" if proc.returncode == 0 or kv.get("DONE") == "1" else "ssh_error"
        if proc.returncode != 0 and not kv:
            status = "ssh_error"
    except subprocess.TimeoutExpired:
        kv, stderr, status = {}, "timeout", "timeout"
        stdout = ""
    http = check_list_db_http(host["hostname"] or alias)
    return {
        "alias": alias,
        "hostname": host.get("hostname"),
        "user": host.get("user"),
        "status": status,
        "elapsed_s": round(time.time() - t0, 1),
        "ssh": kv,
        "list_db_http": http,
        "stderr": (stderr or "")[-400:],
    }


def nonempty(value: str | None) -> bool:
    return bool(value) and value not in {"none", "unavailable", "notfound"}


def classify(row: dict) -> str:
    if row["status"] != "ok":
        return "offline"
    ssh = row.get("ssh") or {}
    miner = ssh.get("MINER_PS")
    cron = ssh.get("CRON_SUSPECT")
    tmp = ssh.get("TMP_MALWARE")
    ir = ssh.get("IR_ACT_CODE")
    if nonempty(miner) or nonempty(tmp) or nonempty(ir):
        return "compromiso"
    if nonempty(cron):
        return "sospechoso"
    supers = ssh.get("PG_SUPERUSERS") or ""
    odoo_supers = [s.strip() for s in supers.split(",") if s.strip() and s.strip() not in {"postgres"}]
    list_db = (ssh.get("LIST_DB") or "").lower()
    http_exp = bool((row.get("list_db_http") or {}).get("exposed"))
    if "true" in list_db or http_exp or odoo_supers:
        return "vulnerable"
    if not nonempty(ssh.get("ODOO_SVC")) and not nonempty(ssh.get("PG_SVC")):
        return "sin_odoo"
    return "ok"


def main() -> int:
    hosts = parse_hosts(CONFIG)
    OUT_DIR.mkdir(exist_ok=True)
    print(f"Hosts a diagnosticar: {len(hosts)}", flush=True)
    results = []
    workers = min(10, max(1, len(hosts)))
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futs = {pool.submit(run_one, h): h["alias"] for h in hosts}
        for i, fut in enumerate(as_completed(futs), 1):
            alias = futs[fut]
            try:
                row = fut.result()
            except Exception as exc:
                row = {"alias": alias, "status": "error", "error": str(exc), "ssh": {}, "list_db_http": {}}
            row["risk"] = classify(row)
            results.append(row)
            print(f"[{i}/{len(hosts)}] {row['alias']} {row['risk']} {row.get('status')}", flush=True)
    results.sort(key=lambda r: (r.get("risk") != "compromiso", r.get("risk") != "vulnerable", r.get("alias") or ""))
    out = OUT_DIR / "resultados.json"
    out.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Escrito {out}")
    counts = {}
    for r in results:
        counts[r["risk"]] = counts.get(r["risk"], 0) + 1
    print("Resumen:", counts)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
