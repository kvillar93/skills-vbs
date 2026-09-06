#!/usr/bin/env python3
import subprocess

REMOTE = r"""
echo USER=$(ps -eo user,lstart,cmd | grep '[o]doo-bin' | head -1)
echo COUNT=$(ps -eo cmd | grep -c '[o]doo-bin')
echo PIDFILE
ls -l /var/run/odoo-server.pid /var/run/odoo.pid 2>/dev/null
cat /var/run/odoo-server.pid 2>/dev/null
echo STOP_FN
grep -nE 'stop|kill|pidfile|USER=' /etc/init.d/odoo-server | head -25
"""
for alias in ("vbsolutions", "alter-legal", "tsheila"):
    p = subprocess.run(
        [r"C:\Windows\System32\OpenSSH\ssh.exe", "-o", "BatchMode=yes", alias, "bash", "-s"],
        input=REMOTE.encode(), capture_output=True, timeout=20,
    )
    print("====", alias, "====")
    print(p.stdout.decode("utf-8", "replace")[:1800])
    print()
