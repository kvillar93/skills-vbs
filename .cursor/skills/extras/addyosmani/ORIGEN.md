# Extras: Addy Osmani agent-skills

Upstream: https://github.com/addyosmani/agent-skills  
Licencia: MIT (copia en `docs/LICENSE-addyosmani.txt`).

Estas 25 skills **no** se instalan en `~/.cursor/skills` por defecto. Son ayuda de ingeniería (spec, TDD, review, frontend…) para repos de código que **ya** tienen skills locales.

Tras `git pull` (2026-09-09) **no hay skills nuevas** respecto a la copia inicial de 25. `instalar-extras-en-repo.ps1` copia todos los directorios de este pack excepto los que empiezan por `_` (p. ej. `_references`).

Instalar en un repo sin pisar lo existente (también instala el pack `ui-ux-pro-max` si está en extras):

```powershell
.\scripts\instalar-extras-en-repo.ps1 -Destino "C:\ruta\al\repo" -SkipExisting
```

Actualizar desde upstream: `.\scripts\actualizar-addyosmani.ps1`.

Referencias compartidas del upstream: `_references/`.
