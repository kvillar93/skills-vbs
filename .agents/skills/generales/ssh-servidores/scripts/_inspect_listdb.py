#!/usr/bin/env python3
import subprocess

REMOTE = r"""
set +e
echo UNIT=$(systemctl show odoo-server -p FragmentPath -p ExecStart --no-pager | tr '\n' '|')
echo PID=$(systemctl show odoo-server -p MainPID --value)
ps -p "$(systemctl show odoo-server -p MainPID --value)" -o args= 2>/dev/null | head -c 400
echo
echo CONF_LINES
sudo -n grep -nE 'list_db|^\[options\]' /etc/odoo-server.conf 2>/dev/null
echo ODOORC
sudo -n grep -n list_db /home/odoo/.odoorc /opt/odoo/debian/odoo.conf /etc/odoo/odoo.conf 2>/dev/null
echo JOURNAL
sudo -n journalctl -u odoo-server -n 15 --no-pager 2>/dev/null | grep -iE 'list_db|error|conf' | head
"""
for alias in ("vbsolutions", "alter-legal", "ashton-school"):
    p = subprocess.run(
        [
            r"C:\Windows\System32\OpenSSH\ssh.exe",
            "-o", "BatchMode=yes",
            alias,
            "bash", "-s",
        ],
        input=REMOTE.encode(),
        capture_output=True,
        timeout=25,
    )
    print("====", alias, "====")
    print(p.stdout.decode("utf-8", "replace")[:2500])
    print()
