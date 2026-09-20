#!/bin/bash
# Reinicio real de odoo-bin (el SysV pidfile no mata los workers viejos).
set +e
export LANG=C
kv() { printf '%s=%s\n' "$1" "$2"; }

BEFORE="$(ps -eo cmd | grep -c '[o]doo-bin')"
kv BEFORE_PROCS "$BEFORE"
kv LIST_DB "$(sudo -n grep -E '^[[:space:]]*list_db' /etc/odoo-server.conf 2>/dev/null | tail -1 | tr -d '[:space:]')"

sudo -n /etc/init.d/odoo-server stop >/dev/null 2>&1
sleep 1
# Mata workers que el pidfile no cubre
sudo -n pkill -u odoo -f '/odoo/odoo-server/odoo-bin' 2>/dev/null
sudo -n pkill -u odoo -f 'odoo-bin -c' 2>/dev/null
sleep 2
LEFT="$(ps -eo cmd | grep -c '[o]doo-bin')"
if [ "$LEFT" -gt 0 ]; then
  sudo -n pkill -9 -u odoo -f 'odoo-bin' 2>/dev/null
  sleep 1
fi
kv AFTER_STOP "$(ps -eo cmd | grep -c '[o]doo-bin')"

sudo -n /etc/init.d/odoo-server start >/dev/null 2>&1
sleep 6
PROCS="$(ps -eo cmd | grep -c '[o]doo-bin')"
kv AFTER_START "$PROCS"
kv START_TIME "$(ps -eo lstart,cmd | grep '[o]doo-bin' | head -1 | awk '{print $1,$2,$3,$4,$5}')"
LOGIN="$(curl -s -o /dev/null -w '%{http_code}' --max-time 8 http://127.0.0.1:8069/web/login 2>/dev/null)"
kv LOGIN_HTTP "$LOGIN"
if [ "$PROCS" -ge 1 ] && [ "$LOGIN" != "000" ]; then
  kv RESULT ok
else
  kv RESULT fail_down
  exit 1
fi
