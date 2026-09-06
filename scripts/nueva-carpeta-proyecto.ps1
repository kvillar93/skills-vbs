param(
    [Parameter(Mandatory = $true)][string]$Nombre
)
$ErrorActionPreference = "Stop"
$Repo = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$slug = $Nombre.Trim().ToLower() -replace "[^a-z0-9]+", "-"
$skillDir = Join-Path $Repo ".cursor\skills\proyectos\$slug\$slug"
if (Test-Path "$skillDir\SKILL.md") { throw "Ya existe $skillDir" }
New-Item -ItemType Directory -Force -Path $skillDir | Out-Null
@"
---
name: $slug
description: >-
  TODO: describe que hace y CUANDO usarla (nombres de servidor, producto).
---

# $slug

Inventario SSH: skill ``ssh-servidores``.

## Conexion

Local: ``ssh -o BatchMode=yes <alias> "whoami && hostname"``

Cloud Agent: ``python3 ~/.cursor/skills/ssh-servidores/scripts/ssh_via_op.py <alias> -- whoami``
"@ | Set-Content -Path (Join-Path $skillDir "SKILL.md") -Encoding utf8
Write-Host "Creada $skillDir"
Write-Host "1) Edita SKILL.md  2) .\scripts\instalar.ps1  3) .\scripts\publicar-cambios.ps1"
