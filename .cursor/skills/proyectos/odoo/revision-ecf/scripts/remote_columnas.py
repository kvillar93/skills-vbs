"""Corre en el servidor (solo lectura). Uso: python3 - <repo> <db>
Para los .py que cambia el pull en módulos INSTALADOS, detecta campos almacenados definidos en
origin/master y comprueba que su columna exista en la BD. Lista las que faltan (requerirían -u)."""
import ast
import subprocess
import sys

repo, db = sys.argv[1], sys.argv[2]


def sh(cmd):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True).stdout


G = "sudo git -c safe.directory=* -C %s " % repo
base = sh(G + "merge-base HEAD origin/master").strip()
instalados = set(sh("sudo -u postgres psql -At -d %s -c \"select name from ir_module_module where state='installed'\"" % db).split())
columnas = set()
for l in sh("sudo -u postgres psql -At -F'|' -d %s -c \"select table_name, column_name from information_schema.columns where table_schema='public'\"" % db).splitlines():
    t, c = l.split("|")
    columnas.add((t, c))
tablas = {t for t, _ in columnas}

archivos = [f for f in sh(G + "diff --name-only %s origin/master -- '*.py'" % base).split()
            if f.split("/")[0] in instalados]


def kw(call, name):
    for k in call.keywords:
        if k.arg == name:
            return k.value
    return None


def es_true(node):
    return isinstance(node, ast.Constant) and node.value is True


def campos_de(src):
    res = set()
    try:
        t = ast.parse(src)
    except SyntaxError:
        return res
    for c in [n for n in ast.walk(t) if isinstance(n, ast.ClassDef)]:
        for st in c.body:
            if isinstance(st, ast.Assign) and len(st.targets) == 1 and isinstance(st.targets[0], ast.Name):
                res.add((c.name, st.targets[0].id))
    return res


previos = set()
for f in archivos:
    for cn, fn in campos_de(sh(G + "show %s:%s" % (base, f))):
        previos.add((f, cn, fn))

faltan = []
revisados = 0
for f in archivos:
    src = sh(G + "show origin/master:%s" % f)
    try:
        tree = ast.parse(src)
    except SyntaxError as e:
        faltan.append((f, "-", "-", "SyntaxError %s" % e))
        continue
    for cls in [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]:
        modelo = None
        abstracto = False
        for st in cls.body:
            if isinstance(st, ast.Assign) and len(st.targets) == 1 and isinstance(st.targets[0], ast.Name):
                n = st.targets[0].id
                if n == "_name" and isinstance(st.value, ast.Constant):
                    modelo = st.value.value
                elif n == "_inherit" and modelo is None:
                    if isinstance(st.value, ast.Constant):
                        modelo = st.value.value
                    elif isinstance(st.value, ast.List) and st.value.elts and isinstance(st.value.elts[0], ast.Constant):
                        modelo = st.value.elts[0].value
                elif n in ("_auto",) and isinstance(st.value, ast.Constant) and st.value.value is False:
                    abstracto = True
        base_names = [b.attr if isinstance(b, ast.Attribute) else getattr(b, "id", "") for b in cls.bases]
        if not modelo or abstracto or "TransientModel" in base_names or "AbstractModel" in base_names:
            continue
        tabla = modelo.replace(".", "_")
        for st in cls.body:
            if not (isinstance(st, ast.Assign) and len(st.targets) == 1 and isinstance(st.targets[0], ast.Name)):
                continue
            v = st.value
            if not (isinstance(v, ast.Call) and isinstance(v.func, ast.Attribute)
                    and isinstance(v.func.value, ast.Name) and v.func.value.id == "fields"):
                continue
            tipo = v.func.attr
            campo = st.targets[0].id
            if tipo in ("One2many",):
                continue
            # Binary/Image se guardan como adjunto (sin columna) salvo attachment=False
            att = kw(v, "attachment")
            if tipo in ("Binary", "Image") and not (isinstance(att, ast.Constant) and att.value is False):
                continue
            if es_true(kw(v, "company_dependent")):
                continue
            # Solo campos que no existían antes del pull en este mismo archivo
            if (f, cls.name, campo) in previos:
                continue
            store = kw(v, "store")
            if (kw(v, "compute") is not None or kw(v, "related") is not None) and not es_true(store):
                continue
            revisados += 1
            if tipo == "Many2many":
                continue  # tabla relacional: Odoo la crea si falta al cargar
            if tabla not in tablas:
                faltan.append((f, modelo, campo, "tabla %s no existe (modelo nuevo; Odoo la crea al cargar)" % tabla))
            elif (tabla, campo) not in columnas:
                faltan.append((f, modelo, campo, "FALTA COLUMNA"))

print("archivos=%d campos_almacenados_revisados=%d" % (len(archivos), revisados))
for x in faltan:
    print("FALTA|%s|%s|%s|%s" % x)
