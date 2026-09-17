---
name: usar-skills-vbs
description: >-
  Cómo usar el repo kvillar93/skills-vbs: inventario de skills generales
  (SSH/servidores), por proyecto (hermes-vbs, chatwoot-vbs, odoo), extras de
  Addy Osmani y UI/UX Pro Max, instalación en PCs locales, Cloud Agents y
  repos que ya tienen skills. Úsala al clonar el repo, al cambiar de PC, o
  cuando pregunten cómo se instalan o se eligen estas skills.
---

# Usar el repo skills-vbs

Origen: https://github.com/kvillar93/skills-vbs  
En disco (esta máquina): `C:\Users\kevin\Projects\skills-vbs` (u otro clone).

## Mapa

| Carpeta | Qué hay | Dónde vive en Cursor |
|---|---|---|
| `.cursor/skills/generales/` | Conexión y servers (`ssh-servidores`); manuales PDF (`manual-pdf-cliente`) | Usuario: `~/.cursor/skills/generales/` |
| `.cursor/skills/proyectos/<nombre>/` | Skill de un producto (Hermes, Chatwoot, …) | Usuario: `~/.cursor/skills/proyectos/` |
| `.cursor/skills/extras/addyosmani/` | Skills de [addyosmani/agent-skills](https://github.com/addyosmani/agent-skills) (25; sin altas nuevas tras el pull de 2026-09-09) | **No** se instalan en el usuario. Solo en un repo de código, a pedido |
| `.cursor/skills/extras/ui-ux-pro-max/` | Pack [ui-ux-pro-max-skill](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill) (`ui-ux-pro-max`, `design`, `design-system`, `ui-styling`, `brand`, `banner-design`, `slides`) | **No** se instalan en el usuario. Solo en un repo de código, a pedido |
| `.cursor/skills/usar-skills-vbs` | Esta guía | Usuario |
| `.cursor/skills/mantener-skills-vbs` | Updates, carpetas nuevas, push automático | Usuario |

Cursor descubre cualquier `SKILL.md` bajo `.cursor/skills/` (también anidado).

## Instalar en un PC local (todas tus sesiones de ese Windows)

```powershell
git clone https://github.com/kvillar93/skills-vbs.git $env:USERPROFILE\Projects\skills-vbs
cd $env:USERPROFILE\Projects\skills-vbs
.\scripts\instalar.ps1
```

Eso crea **junctions** (no copias) desde `~/.cursor/skills\` hacia este clone. Un solo origen. Luego `git pull` en el clone actualiza todas las sesiones locales.

Opcional: Settings → Agents → Context and Tools → **Sync Skills for Cloud Agents** para que la nube reciba `~/.cursor/skills`.

## Cloud Agent si no hay Sync Skills

1. Runtime Secret `OP_SERVICE_ACCOUNT_TOKEN` (ya en el dashboard).
2. En el **repo de trabajo** (Hermes, Chatwoot, etc.) commitea las skills que ese proyecto necesita bajo `.cursor/skills/` (el Cloud Agent clona el repo).
3. O en el snapshot/install: `git clone` de `skills-vbs` y copia `generales` + el proyecto.

No copies `extras/addyosmani` ni `extras/ui-ux-pro-max` a un Cloud Agent a menos que el repo de código las pida: son extras de ingeniería/UI, no de infra VBS.

## Añadir extras a un repo que YA tiene skills

Desde este clone, sin pisar skills locales (VBS u otras):

```powershell
.\scripts\instalar-extras-en-repo.ps1 -Destino "C:\Users\kevin\Projects\mi-app" -SkipExisting
```

Copia los directorios de `extras/addyosmani/*` y `extras/ui-ux-pro-max/*` (excepto los que empiezan por `_`) → `mi-app/.cursor/skills/`. `-SkipExisting` (por defecto) no sobrescribe. Nunca toca `generales`, `proyectos`, `usar-skills-vbs` ni `mantener-skills-vbs`. Añade una regla corta `skills-vbs-extras.mdc`.

Actualizar extras más adelante (sí puede sobrescribir las extras, no las VBS):

```powershell
.\scripts\instalar-extras-en-repo.ps1 -Destino "C:\ruta\mi-app" -ActualizarAddy
.\scripts\instalar-extras-en-repo.ps1 -Destino "C:\ruta\mi-app" -ActualizarExtras
```

## Qué skill abrir

| Tarea | Skill |
|---|---|
| SSH, Odoo, clientes, 1Password, Cloud SSH | `ssh-servidores` |
| Servidor Hermes en EC2 | `hermes-setup-and-maintenance` (carpeta `hermes-vbs`) |
| Chatwoot VBS | `chatwoot-vbs` |
| Workspace Odoo (rules, iconos, restaurar en otra PC) | `odoo` (carpeta `proyectos/odoo`) |
| Icono de módulo Odoo 16 | `odoo-module-icon` |
| PEM de SSH-Infra en Linux (`~/.ssh/infra`, nunca en git) | `ssh-infra` |
| Host TREK / trek.vbsolutions.app / addons Gemini | `trek-vbs` |
| Manual PDF para el cliente (pasos, capturas) | `manual-pdf-cliente` |
| TDD, review, spec, frontend… | extras Addy, si están instaladas en ese repo |
| UI/UX, design system, brand, slides | extras `ui-ux-pro-max`, si están instaladas en ese repo |
| Cambiar/crear/subir skills | `mantener-skills-vbs` |

## Reglas

- Cadenas al usuario en español.
- Nunca PEM, tokens, `.ppk` ni `config.yaml` de Tabby en el chat o en git.
- Drive `.ppk` no se toca.
