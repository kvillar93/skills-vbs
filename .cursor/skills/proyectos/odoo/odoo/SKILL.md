---
name: odoo
description: >-
  Backup y restauración del workspace Odoo (/odoo): rules de Cursor,
  skill de iconos de módulo y cómo rearmar el entorno en otra PC.
  Úsala al cambiar de máquina, al pedir backup de rules/skills de Odoo,
  o al restaurar .cursor del servidor Odoo.
---

# Workspace Odoo (backup)

Origen: https://github.com/kvillar93/skills-vbs  
Carpeta: `.cursor/skills/proyectos/odoo/`

Este producto guarda lo **propio** del workspace `/odoo`. Los extras Addy
ya viven en `.cursor/skills/extras/addyosmani` (opt-in por repo).

## Qué hay

| Ruta | Contenido |
|------|-----------|
| `odoo/SKILL.md` | Esta guía |
| `odoo-module-icon/SKILL.md` | Iconos de módulos Odoo 16 (IA, no SVG a mano) |
| `rules/*.mdc` | Rules del proyecto Odoo (backup) |

Rules incluidas:

- `agent-skills.mdc`
- `custom-modules-guide.mdc`
- `gestion-estudiantes.mdc`
- `odoo-module-icons.mdc`
- `odoo-project-structure.mdc`
- `persona-context.mdc`
- `server-configuration.mdc`

## Restaurar en otra PC (workspace `/odoo`)

Tras clonar este repo (o `git pull`):

```bash
SRC="$HOME/Projects/skills-vbs/.cursor/skills/proyectos/odoo"
DEST="/odoo/.cursor"   # o la raíz del workspace Odoo

mkdir -p "$DEST/rules" "$DEST/skills"
cp -a "$SRC/rules/"*.mdc "$DEST/rules/"
cp -a "$SRC/odoo-module-icon" "$DEST/skills/odoo-module-icon"
```

En Windows, ajusta `$SRC` al clone (`$env:USERPROFILE\Projects\skills-vbs\...`).

Skills de usuario (todas las sesiones): `.\scripts\instalar.ps1` en el clone.
Eso junta `proyectos/` (incluye `odoo`) en `~/.cursor/skills`.

Extras Addy en el repo Odoo (no pisa skills locales):

```powershell
.\scripts\instalar-extras-en-repo.ps1 -Destino "C:\ruta\al\workspace-odoo"
```

## Actualizar este backup

Si cambian rules o `odoo-module-icon` en `/odoo`:

1. Copiar los archivos a `.cursor/skills/proyectos/odoo/` en este repo.
2. Publicar:

```powershell
.\scripts\publicar-cambios.ps1 -Mensaje "skill: backup odoo rules/iconos"
```

No commitear `.cursor` dentro de addonsEP16 ni otros repos de addons.

Inventario SSH: skill `ssh-servidores`.
