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
    odoo/                    # Workspace Odoo: rules, iconos, ssh-infra
  extras/
    addyosmani/              # 25 skills de ingeniería (opt-in por repo)
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

## Extras Addy Osmani (en un repo que ya tiene skills)

```powershell
.\scripts\instalar-extras-en-repo.ps1 -Destino "C:\ruta\tu-app"
```

No pisa skills que ya existan. Licencia MIT del upstream en `docs/LICENSE-addyosmani.txt`.

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
