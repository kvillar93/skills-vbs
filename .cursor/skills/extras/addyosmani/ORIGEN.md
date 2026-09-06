# Extras: Addy Osmani agent-skills

Upstream: https://github.com/addyosmani/agent-skills  
Licencia: MIT (copia en `docs/LICENSE-addyosmani.txt`).

Estas 25 skills **no** se instalan en `~/.cursor/skills` por defecto. Son ayuda de ingeniería (spec, TDD, review, frontend…) para repos de código que **ya** tienen skills locales.

Instalar en un repo sin pisar lo existente:

```powershell
.\scripts\instalar-extras-en-repo.ps1 -Destino "C:\ruta\al\repo"
```

Actualizar desde upstream: `.\scripts\actualizar-addyosmani.ps1`.

Referencias compartidas del upstream: `_references/`.
