---
name: mantener-skills-vbs
description: >-
  Actualizar, crear y publicar skills del repo kvillar93/skills-vbs. Úsala
  SIEMPRE al editar una skill VBS, al crear una carpeta de proyecto nueva
  (hermes-vbs, chatwoot-vbs, u otra), o cuando el usuario pida que el cambio
  quede en GitHub. Incluye el flujo para que Cursor, tras editar, haga commit
  y push al repo.
---

# Mantener skills-vbs

Repo: `C:\Users\kevin\Projects\skills-vbs` (o el clone local). Remoto: `https://github.com/kvillar93/skills-vbs.git`.

## Tras editar una skill (automático)

Si el PC usó `scripts/instalar.ps1`, los archivos en `~/.cursor/skills\...` **son** el repo (junction). No copies a mano.

1. Edita el `SKILL.md` / scripts.
2. En el clone de `skills-vbs`:

```powershell
.\scripts\publicar-cambios.ps1 -Mensaje "skill: describe el cambio en espanol"
```

Eso hace `git add`, commit y `git push origin HEAD`.

Si el usuario dijo “actualiza la skill” o “súbelo”, **el agente debe correr `publicar-cambios.ps1`** (o el equivalente git) **en el mismo turno**, sin esperar otro “haz commit”. No uses `--no-verify`. No cambies `git config`.

El hook `.cursor/hooks/after-skill-edit.ps1` solo hace `git add` del archivo tocado. El push lo hace el script o el agente.

## Crear una carpeta de proyecto nueva

```powershell
.\scripts\nueva-carpeta-proyecto.ps1 -Nombre "odoo-lifter"
```

Crea `.cursor/skills/proyectos/odoo-lifter/<nombre>/SKILL.md` plantilla. Luego:

1. Rellena `name`, `description` y el cuerpo (español).
2. `.\scripts\instalar.ps1` (recrea junctions).
3. `.\scripts\publicar-cambios.ps1 -Mensaje "skill: alta odoo-lifter"`.

Convención: carpeta de producto `proyectos/<slug>/` y dentro **una skill** cuyo folder coincide con `name` del frontmatter.

## Actualizar skills VBS desde GitHub (otro PC)

```powershell
cd $env:USERPROFILE\Projects\skills-vbs
git pull --ff-only
.\scripts\instalar.ps1
```

Si no hay clone: clona de nuevo y corre `instalar.ps1`.

## Actualizar extras Addy Osmani

```powershell
.\scripts\actualizar-addyosmani.ps1
```

Hace clone shallow de `addyosmani/agent-skills` y reemplaza `.cursor/skills/extras/addyosmani` (no toca `generales` ni `proyectos`). Luego `publicar-cambios.ps1`.

En un repo de aplicación que ya tenía extras:

```powershell
.\scripts\instalar-extras-en-repo.ps1 -Destino "C:\ruta\app" -ActualizarAddy
```

## Dónde no crear skills

- Nunca en `~/.cursor/skills-cursor/` (reservado por Cursor).
- No pongas secretos en `SKILL.md`.
- No commitees `diag-out/`, PEM ni `.env`.

## Frontmatter mínimo

```markdown
---
name: nombre-igual-a-la-carpeta
description: Qué hace y CUÁNDO usarla (disparadores en español o nombres de servidores).
---
```
