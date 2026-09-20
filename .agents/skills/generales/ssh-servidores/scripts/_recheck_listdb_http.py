#!/usr/bin/env python3
import json
import ssl
import urllib.request
from pathlib import Path
import subprocess

def check(hostname):
    payload = b'{"jsonrpc":"2.0","method":"call","id":1,"params":{}}'
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    url = f"https://{hostname}/web/database/list"
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=10, context=ctx) as resp:
            body = resp.read(2000).decode("utf-8", "replace")
        parsed = json.loads(body)
        result = parsed.get("result")
        err = parsed.get("error")
        exposed = isinstance(result, list)
        return {"exposed": exposed, "result_type": type(result).__name__, "error": (err or {}).get("data", {}).get("name") if isinstance(err, dict) else str(err)[:80] if err else None, "body": body[:180]}
    except Exception as e:
        return {"exposed": False, "error": type(e).__name__}

data = json.loads(Path(r"C:\Users\kevin\.cursor\skills\ssh-servidores\scripts\diag-out\apply_listdb.json").read_text(encoding="utf-8"))
fails = [r for r in data["listdb"] if not r.get("ok")]
print("fails", len(fails))
still = []
fixed = []
for r in fails:
    h = r.get("hostname")
    c = check(h)
    if c.get("exposed"):
        still.append((r["alias"], h, c.get("body")))
    else:
        fixed.append((r["alias"], c.get("error") or c.get("result_type")))
print("NOW_OK", len(fixed), [x[0] for x in fixed[:15]], "..." if len(fixed)>15 else "")
print("STILL_EXPOSED", len(still))
for a,h,b in still[:8]:
    print(a, h, b)

REMOTE = r"""
ps -eo pid,lstart,cmd | grep -E '[o]doo|[p]ython.*openerp' | head -5
echo INIT=$(grep -E 'CONFIG|DAEMON_ARGS|DAEMON_OPTS' /etc/init.d/odoo-server | head -10)
"""
p = subprocess.run(
    [r"C:\Windows\System32\OpenSSH\ssh.exe", "-o", "BatchMode=yes", "vbsolutions", "bash", "-s"],
    input=REMOTE.encode(), capture_output=True, timeout=20,
)
print("==== vbsolutions process ====")
print(p.stdout.decode()[:2000])
