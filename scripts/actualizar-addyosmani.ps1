# Sustituye extras/addyosmani con un clone fresco del upstream.
$ErrorActionPreference = "Stop"
$Repo = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$Tmp = Join-Path $env:TEMP ("agent-skills-" + [guid]::NewGuid().ToString("N"))
$Dest = Join-Path $Repo ".cursor\skills\extras\addyosmani"
git clone --depth 1 https://github.com/addyosmani/agent-skills.git $Tmp
if (Test-Path $Dest) { Remove-Item $Dest -Recurse -Force }
New-Item -ItemType Directory -Force -Path $Dest | Out-Null
Copy-Item (Join-Path $Tmp "skills\*") $Dest -Recurse -Force
if (Test-Path (Join-Path $Tmp "references")) {
    Copy-Item (Join-Path $Tmp "references") (Join-Path $Dest "_references") -Recurse -Force
}
Copy-Item (Join-Path $Tmp "LICENSE") (Join-Path $Repo "docs\LICENSE-addyosmani.txt") -Force
@"
# Extras: Addy Osmani agent-skills

Upstream: https://github.com/addyosmani/agent-skills
Actualizado: $(Get-Date -Format "yyyy-MM-dd")
Licencia: MIT (docs/LICENSE-addyosmani.txt).
"@ | Set-Content (Join-Path $Dest "ORIGEN.md") -Encoding utf8
Remove-Item $Tmp -Recurse -Force
Write-Host "extras/addyosmani actualizado. Corre publicar-cambios.ps1"
