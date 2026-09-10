# skills-vbs

Catálogo de **Agent Skills** de VB Solutions para Cursor (PCs locales y Cloud Agents).

Repo: https://github.com/kvillar93/skills-vbs

## Qué hay

```
.cursor/skills/
  usar-skills-vbs/           # cómo usar este repo
  mantener-skills-vbs/       # updates, carpetas nuevas, push
  generales/
    ssh-servidores/          # SSH, Odoo, 1Password, Cloud Agents
  proyectos/
    hermes-vbs/              # Hermes en EC2
    chatwoot-vbs/            # Chatwoot VBS
    odoo/                    # Workspace Odoo: rules + odoo-module-icon
    trek-vbs/                # Host Docker + TREK (trek.vbsolutions.app)
  extras/
    addyosmani/              # 25 skills de ingeniería (opt-in por repo)
    ui-ux-pro-max/           # pack UI/UX (opt-in por repo; cada carpeta tiene SKILL.md)
.cursor/rules/
  using-agent-skills.mdc     # user-rule: enrutar si la tarea es compleja
```

## En otro PC

```powershell
git clone https://github.com/kvillar93/skills-vbs.git $env:USERPROFILE\Projects\skills-vbs
cd $env:USERPROFILE\Projects\skills-vbs
.\scripts\instalar.ps1
```

Crea junctions en `~/.cursor\skills`. Un `git pull` en el clone actualiza Cursor.

Cloud Agents: **Settings → Agents → Context and Tools → Sync Skills for Cloud Agents**, o commitea las skills que haga falta en el repo de trabajo.

## Extras (en un repo que ya tiene skills)

Copia **addyosmani** (25 skills de ingeniería) y **ui-ux-pro-max** (diseño UI/UX) al repo destino. No pisa skills VBS ni otras que ya existan (`-SkipExisting` por defecto).

```powershell
.\scripts\instalar-extras-en-repo.ps1 -Destino "C:\ruta\tu-app" -SkipExisting
```

Licencias MIT: `docs/LICENSE-addyosmani.txt` y `docs/LICENSE-ui-ux-pro-max.txt`. Origen de cada pack: `.cursor/skills/extras/<pack>/ORIGEN.md`.

## Crear un proyecto nuevo de skills

```powershell
.\scripts\nueva-carpeta-proyecto.ps1 -Nombre "mi-producto"
.\scripts\instalar.ps1
.\scripts\publicar-cambios.ps1 -Mensaje "skill: alta mi-producto"
```

## Publicar un cambio de skill

```powershell
.\scripts\publicar-cambios.ps1 -Mensaje "skill: describe el cambio"
```
