#!/bin/bash
# Aplica list_db = False. No imprime el resto del conf (puede tener secretos).
set +e
export LANG=C

kv() { printf '%s=%s\n' "$1" "$2"; }

CONF=""
for f in /etc/odoo-server.conf /etc/odoo/odoo.conf /etc/odoo.conf; do
  if sudo -n test -f "$f" 2>/dev/null; then
    CONF="$f"
    break
  fi
done
kv CONF "${CONF:-notfound}"
if [ -z "$CONF" ]; then
  kv RESULT fail_noconf
  exit 1
fi

BEFORE="$(sudo -n grep -E '^[[:space:]]*list_db' "$CONF" 2>/dev/null | tail -1 | tr -d '[:space:]')"
kv BEFORE "${BEFORE:-missing}"

if echo "$BEFORE" | grep -qi 'list_db=False'; then
  kv ACTION already_false
else
  TS="$(date +%Y%m%d%H%M%S)"
  BAK="${CONF}.bak.listdb.${TS}"
  sudo -n cp -a "$CONF" "$BAK"
  kv BACKUP "$BAK"
  if sudo -n grep -qE '^[[:space:]]*list_db' "$CONF"; then
    sudo -n sed -i -E 's/^[[:space:]]*list_db.*/list_db = False/' "$CONF"
    kv ACTION replaced
  elif sudo -n grep -qE '^\[options\]' "$CONF"; then
    sudo -n sed -i '/^\[options\]/a list_db = False' "$CONF"
    kv ACTION inserted
  else
    printf '\n[options]\nlist_db = False\n' | sudo -n tee -a "$CONF" >/dev/null
    kv ACTION appended
  fi
fi

AFTER="$(sudo -n grep -E '^[[:space:]]*list_db' "$CONF" 2>/dev/null | tail -1 | tr -d '[:space:]')"
kv AFTER "${AFTER:-missing}"
COUNT="$(sudo -n grep -cE '^[[:space:]]*list_db' "$CONF" 2>/dev/null)"
kv LIST_DB_LINES "$COUNT"

if ! echo "$AFTER" | grep -qi 'list_db=False'; then
  kv RESULT fail_not_false
  exit 2
fi

if sudo -n systemctl restart odoo-server; then
  kv RESTART ok
else
  kv RESTART fail
  kv RESULT fail_restart
  exit 3
fi

sleep 4
kv ACTIVE "$(systemctl is-active odoo-server 2>/dev/null)"
kv RESULT ok
