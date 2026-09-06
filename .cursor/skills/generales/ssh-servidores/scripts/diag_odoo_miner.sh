#!/bin/bash
# Diagnostico SOLO LECTURA: ataque Odoo list_db + server action + COPY FROM PROGRAM + miner.
# No modifica archivos, servicios, roles ni bases de datos.
set +e
export LANG=C
umask 077

kv() { printf '%s=%s\n' "$1" "$(printf '%s' "$2" | tr '\n' '|' | sed 's/|$//')"; }

kv HOST "$(hostname)"
kv DATE "$(date -u +%FT%TZ)"
kv NCPU "$(nproc 2>/dev/null || echo 0)"
kv LOAD "$(cut -d' ' -f1-3 /proc/loadavg 2>/dev/null)"
kv UPTIME_S "$(awk '{print int($1)}' /proc/uptime 2>/dev/null)"

if command -v docker >/dev/null 2>&1; then
  kv DOCKER "$(docker ps --format '{{.Names}}:{{.Image}}' 2>/dev/null | tr '\n' ';')"
else
  kv DOCKER "none"
fi

ODOO_UNIT="$(systemctl list-units --type=service --state=running --no-pager 2>/dev/null | awk '/odoo/{print $1; exit}')"
PG_UNIT="$(systemctl list-units --type=service --state=running --no-pager 2>/dev/null | awk '/postgres/{print $1; exit}')"
kv ODOO_SVC "${ODOO_UNIT:-none}"
kv PG_SVC "${PG_UNIT:-none}"

CONF=""
for p in /etc/odoo/odoo.conf /etc/odoo.conf /etc/odoo-server.conf /opt/odoo/odoo.conf /opt/odoo/debian/odoo.conf; do
  if [ -r "$p" ] || sudo -n test -r "$p" 2>/dev/null; then
    CONF="$p"
    break
  fi
done
if [ -z "$CONF" ]; then
  CONF="$(sudo -n find /etc /opt /home /var/lib/odoo -maxdepth 4 \( -name 'odoo.conf' -o -name 'odoo-server.conf' -o -name 'openerp-server.conf' \) 2>/dev/null | head -1)"
fi
kv ODOO_CONF "${CONF:-notfound}"

LISTDB="notfound"
if [ -n "$CONF" ]; then
  LISTDB="$(sudo -n grep -E '^[[:space:]]*list_db' "$CONF" 2>/dev/null | head -1 | tr -d '[:space:]')"
fi
kv LIST_DB "${LISTDB:-notfound}"

ROLES="$(sudo -n -u postgres psql -Atc "SELECT usename || ':' || usesuper FROM pg_user ORDER BY usename" 2>/dev/null | tr '\n' ';')"
kv PG_ROLES "${ROLES:-unavailable}"
SUPERS="$(sudo -n -u postgres psql -Atc "SELECT usename FROM pg_user WHERE usesuper IS TRUE" 2>/dev/null | tr '\n' ',')"
kv PG_SUPERUSERS "${SUPERS:-unavailable}"

TOPCPU="$(ps -eo pcpu,user,comm --sort=-pcpu --no-headers 2>/dev/null | head -8 | awk '{printf "%s%%:%s:%s;", $1,$2,$3}')"
kv TOPCPU "$TOPCPU"

MINER="$(ps -eo comm,args --no-headers 2>/dev/null | grep -Ei 'xmrig|kinsing|kdevtmpfsi|sysupdate|minerd|cryptonight|c3pool|minexmr|/tmp/\.[a-zA-Z0-9]{4,}' | grep -v grep | head -8)"
kv MINER_PS "${MINER:-none}"

CRON_HIT="$(sudo -n sh -c 'crontab -l 2>/dev/null; cat /etc/crontab /etc/cron.d/* /var/spool/cron/crontabs/* 2>/dev/null' | grep -Ei 'curl |wget |xmrig|kinsing|/tmp/|base64 |pastebin|busybox' | grep -v '^#' | head -12)"
kv CRON_SUSPECT "${CRON_HIT:-none}"

TMP_HIT="$(sudo -n find /tmp /var/tmp /dev/shm -maxdepth 2 \( -iname '*xmrig*' -o -iname '*kinsing*' -o -iname '*kdevtmpfsi*' -o -iname 'sysupdate*' \) 2>/dev/null | head -20)"
kv TMP_MALWARE "${TMP_HIT:-none}"

CODE_HITS=""
DBS="$(sudo -n -u postgres psql -Atc "SELECT datname FROM pg_database WHERE datistemplate = false AND datname NOT IN ('postgres')" 2>/dev/null)"
kv PG_DBS "$(printf '%s' "$DBS" | tr '\n' ',')"
if [ -n "$DBS" ]; then
  while IFS= read -r db; do
    [ -z "$db" ] && continue
    hits="$(sudo -n -u postgres psql -d "$db" -Atc "SELECT id::text || ':' || COALESCE(name,'') FROM ir_act_server WHERE state = 'code' AND (code ILIKE '%os.system%' OR code ILIKE '%subprocess%' OR code ILIKE '%from program%' OR code ILIKE '%COPY %' OR code ILIKE '%/dev/shm%' OR code ILIKE '%xmrig%' OR code ILIKE '%kinsing%' OR code ILIKE '%wget %' OR code ILIKE '%curl %http%') LIMIT 15" 2>/dev/null)"
    if [ -n "$hits" ]; then
      CODE_HITS="${CODE_HITS}${db}=>{$(printf '%s' "$hits" | tr '\n' ',')};"
    fi
  done <<EOF
$DBS
EOF
fi
kv IR_ACT_CODE "${CODE_HITS:-none}"

kv DONE 1
