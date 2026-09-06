#!/usr/bin/env python3
from __future__ import annotations

import json
import ssl
import subprocess
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

SSH = r"C:\Windows\System32\OpenSSH\ssh.exe"
ROOT = Path(__file__).parent
LISTDB_SH = ROOT / "apply_listdb_false.sh"
NOSUPER_SH = ROOT / "apply_odoo_nosuper.sh"
PREV = ROOT / "diag-out" / "resultados.json"
OUT = ROOT / "diag-out" / "apply_listdb.json"

MULTI_DB = {
    "75-grados-vbsolutions",
    "inecar",
    "odootest",
    "qtek",
    "saas-vbs",
}
NOSUPER_ALIASES = ["umbratest", "odoo-test-vbs", "odootest"]


def parse_kv(text: str) -> dict:
    data = {}
    for line in text.splitlines():
        if "=" not in line:
            continue
        k, v = line.split("=", 1)
        data[k.strip()] = v.strip()
    return data


def hosts_one_db() -> list[dict]:
    rows = json.loads(PREV.read_text(encoding="utf-8"))
    out = []
    for r in rows:
        alias = r.get("alias")
        if alias in MULTI_DB:
            continue
        if r.get("status") != "ok":
            continue
        ssh = r.get("ssh") or {}
        if ssh.get("ODOO_SVC") in {None, "", "none"}:
            continue
        n = (r.get("list_db_http") or {}).get("db_count")
        if n != 1:
            continue
        out.append({"alias": alias, "hostname": r.get("hostname")})
    return out


def check_list_db_http(hostname: str) -> dict:
    payload = b'{"jsonrpc":"2.0","method":"call","id":1,"params":{}}'
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    last = ""
    for scheme in ("https", "http"):
        url = f"{scheme}://{hostname}/web/database/list"
        req = urllib.request.Request(
            url,
            data=payload,
            headers={"Content-Type": "application/json", "User-Agent": "vbs-harden/1"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=10, context=ctx) as resp:
                body = resp.read(8000).decode("utf-8", "replace")
            try:
                parsed = json.loads(body)
                result = parsed.get("result")
            except json.JSONDecodeError:
                return {"url": url, "exposed": False, "raw": "no_json"}
            exposed = isinstance(result, list) or (
                isinstance(result, dict) and isinstance(result.get("databases"), list)
            )
            return {"url": url, "exposed": exposed, "error": parsed.get("error", {}).get("message") if isinstance(parsed.get("error"), dict) else None}
        except Exception as exc:
            last = exc.__class__.__name__
            continue
    return {"url": None, "exposed": False, "error": last}


def ssh_script(alias: str, script: Path, timeout: int = 50) -> dict:
    blob = script.read_bytes().replace(b"\r\n", b"\n")
    proc = subprocess.run(
        [
            SSH,
            "-o", "BatchMode=yes",
            "-o", "ConnectTimeout=12",
            "-o", "StrictHostKeyChecking=accept-new",
            alias,
            "bash", "-s",
        ],
        input=blob,
        capture_output=True,
        timeout=timeout,
    )
    return {
        "kv": parse_kv(proc.stdout.decode("utf-8", "replace")),
        "stderr": proc.stderr.decode("utf-8", "replace")[-400:],
        "code": proc.returncode,
    }


def apply_listdb(host: dict) -> dict:
    alias = host["alias"]
    t0 = time.time()
    try:
        remote = ssh_script(alias, LISTDB_SH, timeout=55)
    except subprocess.TimeoutExpired:
        return {"alias": alias, "ok": False, "error": "timeout", "elapsed_s": round(time.time() - t0, 1)}
    kv = remote["kv"]
    http = check_list_db_http(host["hostname"] or alias)
    ok = kv.get("RESULT") == "ok" and kv.get("ACTIVE") == "active" and not http.get("exposed")
    return {
        "alias": alias,
        "hostname": host.get("hostname"),
        "ok": ok,
        "elapsed_s": round(time.time() - t0, 1),
        "remote": kv,
        "http": http,
        "stderr": remote.get("stderr"),
    }


def apply_nosuper(alias: str) -> dict:
    t0 = time.time()
    try:
        remote = ssh_script(alias, NOSUPER_SH, timeout=55)
    except subprocess.TimeoutExpired:
        return {"alias": alias, "ok": False, "error": "timeout"}
    kv = remote["kv"]
    ok = kv.get("RESULT") == "ok" and "super=f" in (kv.get("AFTER") or "")
    return {
        "alias": alias,
        "ok": ok,
        "elapsed_s": round(time.time() - t0, 1),
        "remote": kv,
        "stderr": remote.get("stderr"),
    }


def main() -> int:
    hosts = hosts_one_db()
    print(f"list_db=False en {len(hosts)} hosts de 1 BD", flush=True)
    results = []
    with ThreadPoolExecutor(max_workers=8) as pool:
        futs = {pool.submit(apply_listdb, h): h["alias"] for h in hosts}
        for i, fut in enumerate(as_completed(futs), 1):
            alias = futs[fut]
            try:
                row = fut.result()
            except Exception as exc:
                row = {"alias": alias, "ok": False, "error": str(exc)}
            results.append(row)
            http = row.get("http") or {}
            print(
                f"[{i}/{len(hosts)}] {row.get('alias')} ok={row.get('ok')} "
                f"action={((row.get('remote') or {}).get('ACTION'))} "
                f"active={((row.get('remote') or {}).get('ACTIVE'))} "
                f"exposed={http.get('exposed')}",
                flush=True,
            )
    nosuper = []
    print("NOSUPERUSER en", NOSUPER_ALIASES, flush=True)
    for alias in NOSUPER_ALIASES:
        row = apply_nosuper(alias)
        nosuper.append(row)
        print(
            f"  {alias} ok={row.get('ok')} {((row.get('remote') or {}).get('BEFORE'))} -> {((row.get('remote') or {}).get('AFTER'))}",
            flush=True,
        )
    payload = {
        "listdb": sorted(results, key=lambda r: (not r.get("ok"), r.get("alias") or "")),
        "nosuper": nosuper,
    }
    OUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    ok_n = sum(1 for r in results if r.get("ok"))
    fail_n = len(results) - ok_n
    print(f"list_db ok={ok_n} fail={fail_n}")
    print(f"Escrito {OUT}")
    return 0 if fail_n == 0 and all(r.get("ok") for r in nosuper) else 1


if __name__ == "__main__":
    raise SystemExit(main())
