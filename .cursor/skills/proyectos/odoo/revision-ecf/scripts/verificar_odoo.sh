# Verifica Odoo tras reinicio: servicio, HTTP y errores del log desde $1 (UTC)
desde="$1"
for i in $(seq 1 30); do
  code=$(curl -s -o /dev/null -w '%{http_code}' --max-time 5 http://127.0.0.1:8069/web/login)
  [ "$code" = "200" ] && break
  sleep 4
done
echo "SERVICIO|$(systemctl is-active odoo-server)|HTTP=$code|desde=$(systemctl show odoo-server -p ActiveEnterTimestamp --value)"
sudo tail -c 3000000 /var/log/odoo/odoo-server.log | grep -a -E '^[0-9-]+ [0-9:,]+ [0-9]+ (ERROR|CRITICAL)' | awk -v d="$desde" '($1" "$2) >= d' | grep -v generate_advanced_report | cut -c1-220 | tail -8
echo "ERRORES_DESDE|$(sudo tail -c 3000000 /var/log/odoo/odoo-server.log | grep -a -E '^[0-9-]+ [0-9:,]+ [0-9]+ (ERROR|CRITICAL)' | awk -v d="$desde" '($1" "$2) >= d' | grep -v -c generate_advanced_report)"
