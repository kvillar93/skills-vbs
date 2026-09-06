#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

SSH = r"C:\Windows\System32\OpenSSH\ssh.exe"
SCRIPT = Path(__file__).with_name("score_odoo_passwords.py")
PREV = Path(__file__).with_name("diag-out") / "resultados.json"
OUT = Path(__file__).with_name("diag-out") / "passwords.json"

SKIP = {"vbs-hermes", "vbs-hermes-chatwoot"}


def aliases() -> list[str]:
    rows = json.loads(PREV.read_text(encoding="utf-8"))
    out = []
    for r in rows:
        if r.get("alias") in SKIP:
            continue
        if r.get("status") != "ok":
            continue
        ssh = r.get("ssh") or {}
        if ssh.get("ODOO_SVC") in {None, "", "none"}:
            continue
        out.append(r["alias"])
    return out


def parse_kv(text: str) -> dict:
    data = {}
    for line in text.splitlines():
        if "=" not in line:
            continue
        k, v = line.split("=", 1)
        data[k.strip()] = v.strip()
    return data


def run_one(alias: str) -> dict:
    t0 = time.time()
    script = SCRIPT.read_bytes().replace(b"\r\n", b"\n")
    try:
        proc = subprocess.run(
            [
                SSH,
                "-o", "BatchMode=yes",
                "-o", "ConnectTimeout=12",
                "-o", "StrictHostKeyChecking=accept-new",
                alias,
                "python3", "-",
            ],
            input=script,
            capture_output=True,
            timeout=40,
        )
        kv = parse_kv(proc.stdout.decode("utf-8", "replace"))
        status = "ok" if kv.get("DONE") == "1" else "error"
        stderr = proc.stderr.decode("utf-8", "replace")[-300:]
    except subprocess.TimeoutExpired:
        kv, status, stderr = {}, "timeout", "timeout"
    return {
        "alias": alias,
        "status": status,
        "elapsed_s": round(time.time() - t0, 1),
        "data": kv,
        "stderr": stderr,
    }


def main() -> int:
    hosts = aliases()
    print(f"Hosts Odoo: {len(hosts)}", flush=True)
    results = []
    with ThreadPoolExecutor(max_workers=10) as pool:
        futs = {pool.submit(run_one, a): a for a in hosts}
        for i, fut in enumerate(as_completed(futs), 1):
            alias = futs[fut]
            try:
                row = fut.result()
            except Exception as exc:
                row = {"alias": alias, "status": "error", "data": {}, "error": str(exc)}
            results.append(row)
            d = row.get("data") or {}
            print(
                f"[{i}/{len(hosts)}] {row['alias']} {row['status']} "
                f"master={d.get('ADMIN_PASSWD_VERDICT','?')} "
                f"db={d.get('DB_PASSWORD_VERDICT','?')} "
                f"login={d.get('ADMIN_LOGIN','?')}",
                flush=True,
            )
    results.sort(key=lambda r: r.get("alias") or "")
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Escrito {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
