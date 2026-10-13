p=$(sudo grep -E '^\s*addons_path' /etc/odoo-server.conf | cut -d= -f2 | tr ',' '\n' | tr -d ' ' | grep -E 'addons(CE|EP)1[46]$' | head -1)
G="sudo git -c safe.directory=* -C $p"
$G fetch -q origin
echo "REPO|$p|HEAD=$($G rev-parse --short HEAD)|origin=$($G rev-parse --short origin/master)|faltan=$($G rev-list --count HEAD..origin/master)"
for f in $($G ls-files --others --exclude-standard); do $G cat-file -e origin/master:$f 2>/dev/null && echo "CHOQUE|$f"; done
echo "FIN_CHOQUES"
