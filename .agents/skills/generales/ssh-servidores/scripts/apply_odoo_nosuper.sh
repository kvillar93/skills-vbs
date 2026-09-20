#!/bin/bash
# Quita SUPERUSER al rol odoo; conserva CREATEDB. Solo lectura de flags despues.
set +e
export LANG=C
kv() { printf '%s=%s\n' "$1" "$2"; }

BEFORE="$(sudo -n -u postgres psql -Atc "SELECT 'super=' || rolsuper::text || ' createdb=' || rolcreatedb::text || ' createrole=' || rolcreaterole::text FROM pg_roles WHERE rolname='odoo'" 2>/dev/null)"
kv BEFORE "${BEFORE:-missing}"
if echo "$BEFORE" | grep -q 'super=f'; then
  kv ACTION already_nosuper
else
  sudo -n -u postgres psql -v ON_ERROR_STOP=1 -c "ALTER ROLE odoo NOSUPERUSER;" >/tmp/alter_odoo_role.out 2>/tmp/alter_odoo_role.err
  kv ACTION altered
  kv ALTER_ERR "$(tr '\n' ' ' </tmp/alter_odoo_role.err 2>/dev/null)"
fi
AFTER="$(sudo -n -u postgres psql -Atc "SELECT 'super=' || rolsuper::text || ' createdb=' || rolcreatedb::text || ' createrole=' || rolcreaterole::text FROM pg_roles WHERE rolname='odoo'" 2>/dev/null)"
kv AFTER "${AFTER:-missing}"

if sudo -n systemctl restart odoo-server; then
  kv RESTART ok
else
  kv RESTART fail
fi
sleep 4
kv ACTIVE "$(systemctl is-active odoo-server 2>/dev/null)"
if echo "$AFTER" | grep -q 'super=f'; then
  kv RESULT ok
else
  kv RESULT fail_still_super
  exit 2
fi
