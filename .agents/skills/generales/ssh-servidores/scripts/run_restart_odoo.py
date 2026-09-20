#!/usr/bin/env python3
from __future__ import annotations

import json
import ssl
import subprocess
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

SSH = r"C:\Windows\System32\OpenSSH\ssh.exe"
ROOT = Path(__file__).parent
SH = ROOT / "restart_odoo_real.sh"
PREV = ROOT / "diag-out" / "resultados.json"
APPLY = ROOT / "diag-out" / "apply_listdb.json"
OUT = ROOT / "diag-out" / "restart_odoo.json"
MULTI_DB = {"75-grados-vbsolutions", "inecar", "qtek", "saas-vbs"}  # odootest se incluye: hubo ALTER ROLE


def parse_kv(text: str) -> dict:
    data = {}
    for line in text.splitlines():
        if "=" not in line:
            continue
        k, v = line.split("=", 1)
        data[k.strip()] = v.strip()
    return data


def aliases() -> list[dict]:
    rows = json.loads(PREV.read_text(encoding="utf-8"))
    out = []
    seen = set()
    for r in rows:
        alias = r.get("alias")
        if alias in MULTI_DB:
            continue
        if r.get("status") != "ok":
            continue
        ssh = r.get("ssh") or {}
        if ssh.get("ODOO_SVC") in {None, "", "none"} and alias != "odootest":
            continue
        n = (r.get("list_db_http") or {}).get("db_count")
        if n != 1 and alias != "odootest":
            continue
        if alias in seen:
            continue
        seen.add(alias)
        out.append({"alias": alias, "hostname": r.get("hostname")})
    if "odootest" not in seen:
        out.append({"alias": "odootest", "hostname": "odootest.vbsolutions.app"})
    return out


def http_json_list(hostname: str) -> dict:
    payload = b'{"jsonrpc":"2.0","method":"call","id":1,"params":{}}'
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    url = f"https://{hostname}/web/database/list"
    req = urllib.request.Request(
        url, data=payload, headers={"Content-Type": "application/json"}, method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=12, context=ctx) as resp:
            body = resp.read(4000).decode("utf-8", "replace")
        parsed = json.loads(body)
        result = parsed.get("result")
        return {"exposed": isinstance(result, list), "status": "http_ok"}
    except Exception as exc:
        return {"exposed": False, "status": type(exc).__name__}


def http_login(hostname: str) -> int | None:
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    url = f"https://{hostname}/web/login"
    req = urllib.request.Request(url, headers={"User-Agent": "vbs-harden/1"}, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=12, context=ctx) as resp:
            return resp.getcode()
    except urllib.error.HTTPError as exc:
        return exc.code
    except Exception:
        return None


def run_one(host: dict) -> dict:
    t0 = time.time()
    blob = SH.read_bytes().replace(b"\r\n", b"\n")
    try:
        proc = subprocess.run(
            [
                SSH, "-o", "BatchMode=yes", "-o", "ConnectTimeout=12",
                host["alias"], "bash", "-s",
            ],
            input=blob, capture_output=True, timeout=70,
        )
        kv = parse_kv(proc.stdout.decode("utf-8", "replace"))
        stderr = proc.stderr.decode("utf-8", "replace")[-300:]
    except subprocess.TimeoutExpired:
        kv, stderr = {"RESULT": "timeout"}, "timeout"
    time.sleep(2)
    lst = http_json_list(host["hostname"] or host["alias"])
    login = http_login(host["hostname"] or host["alias"])
    procs = int(kv.get("AFTER_START") or 0)
    ok = kv.get("RESULT") == "ok" and procs >= 1 and login in {200, 303, 302} and not lst.get("exposed")
    # odootest is multi-db: list_db may still be exposed; require odoo up only
    if host["alias"] == "odootest":
        ok = procs >= 1 and login in {200, 303, 302}
    return {
        "alias": host["alias"],
        "hostname": host.get("hostname"),
        "ok": ok,
        "elapsed_s": round(time.time() - t0, 1),
        "remote": kv,
        "list_http": lst,
        "login_https": login,
        "stderr": stderr,
    }


def main() -> int:
    hosts = aliases()
    print(f"Reinicio real Odoo en {len(hosts)} hosts", flush=True)
    results = []
    with ThreadPoolExecutor(max_workers=6) as pool:
        futs = {pool.submit(run_one, h): h["alias"] for h in hosts}
        for i, fut in enumerate(as_completed(futs), 1):
            alias = futs[fut]
            try:
                row = fut.result()
            except Exception as exc:
                row = {"alias": alias, "ok": False, "error": str(exc)}
            results.append(row)
            print(
                f"[{i}/{len(hosts)}] {row.get('alias')} ok={row.get('ok')} "
                f"procs={((row.get('remote') or {}).get('AFTER_START'))} "
                f"login={row.get('login_https')} exposed={((row.get('list_http') or {}).get('exposed'))}",
                flush=True,
            )
    results.sort(key=lambda r: (not r.get("ok"), r.get("alias") or ""))
    OUT.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    ok_n = sum(1 for r in results if r.get("ok"))
    print(f"ok={ok_n} fail={len(results)-ok_n} -> {OUT}")
    return 0 if ok_n == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
