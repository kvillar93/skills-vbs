# Uso: bash -s -- <ff|merge>
set -e
modo=$1
p=$(sudo grep -E '^\s*addons_path' /etc/odoo-server.conf | cut -d= -f2 | tr ',' '\n' | tr -d ' ' | grep -E 'addons(CE|EP)1[46]$' | head -1)
G="sudo git -c safe.directory=* -c user.name=Kevin_Villar -c user.email=kvillar@lifterdo.com -C $p"
antes=$($G rev-parse HEAD)
echo "ANTES|$antes"
if [ "$modo" = ff ]; then $G pull -q --ff-only origin master; else $G pull -q --no-rebase --no-edit origin master; fi
echo "DESPUES|$($G rev-parse HEAD)|dirty=$($G status --porcelain --untracked-files=no | wc -l)"
# Chequeo de sintaxis de los .py cambiados
err=0
for f in $($G diff --name-only $antes HEAD -- '*.py'); do
  sudo python3 -c "import ast,sys; ast.parse(open(sys.argv[1],encoding='utf-8').read())" "$p/$f" 2>/tmp/pyc.err || { echo "SINTAXIS|$f|$(head -c 300 /tmp/pyc.err)"; err=1; }
done
echo "SINTAXIS_OK|$((1-err))"
