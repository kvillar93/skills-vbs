# Extras: UI/UX Pro Max

Upstream: https://github.com/nextlevelbuilder/ui-ux-pro-max-skill  
Licencia: MIT (copia en `LICENSE` de este pack y en `docs/LICENSE-ui-ux-pro-max.txt`).  
Aviso de autoría: `NOTICE`.

Estas skills **no** se instalan en `~/.cursor/skills` por defecto. Son ayuda de diseño UI/UX (páginas, componentes, design system, accesibilidad, slides, brand) para repos de código que **ya** tienen skills locales.

Cada carpeta de skill contiene `SKILL.md` (requisito de Cursor):

| Skill | Para qué |
|---|---|
| `ui-ux-pro-max` | Diseño e implementación de interfaces (pack principal) |
| `design` | Diseño visual, logos, CIP |
| `design-system` | Tokens y sistema de diseño |
| `ui-styling` | Estilos de UI |
| `brand` | Identidad y marca |
| `banner-design` | Banners |
| `slides` | Presentaciones |

Instalar en un repo sin pisar lo existente (VBS u otras skills):

```powershell
.\scripts\instalar-extras-en-repo.ps1 -Destino "C:\ruta\al\repo" -SkipExisting
```

El script copia los directorios de este pack (excepto `_` y archivos sueltos como `ORIGEN.md` / `LICENSE`) a `<repo>/.cursor/skills/`. No toca `generales`, `proyectos`, `usar-skills-vbs` ni `mantener-skills-vbs`.
