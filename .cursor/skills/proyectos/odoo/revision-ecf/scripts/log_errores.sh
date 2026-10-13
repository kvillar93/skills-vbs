# Uso: ssh <alias> "bash -s -- 'AAAA-MM-DD HH:MM'" < log_errores.sh
# Errores ERROR/CRITICAL del log de Odoo desde la fecha (UTC), agrupados. Solo lee los últimos 30 MB.
desde="$1"
sudo tail -c 30000000 /var/log/odoo/odoo-server.log \
  | grep -a -E '^[0-9-]+ [0-9:,]+ [0-9]+ (ERROR|CRITICAL)' \
  | awk -v d="$desde" '($1" "$2) >= d' \
  | sed -E 's/^[0-9-]+ [0-9:,]+ [0-9]+ //' | cut -c1-200 | sort | uniq -c | sort -rn | head -20
