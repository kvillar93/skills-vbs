# Instala skills VBS en este Windows: junctions a este clone.
# No instala extras Addy (eso es por repo de codigo).
$ErrorActionPreference = "Stop"
$Repo = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$SkillsSrc = Join-Path $Repo ".cursor\skills"
$DestRoot = Join-Path $env:USERPROFILE ".cursor\skills"
$RulesDest = Join-Path $env:USERPROFILE ".cursor\rules"

function Set-Junction {
    param([string]$Link, [string]$Target)
    if (-not (Test-Path $Target)) { throw "No existe destino: $Target" }
    if (Test-Path $Link) {
        $item = Get-Item $Link -Force
        if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) {
            cmd /c "rmdir `"$Link`""
        } elseif ($item.PSIsContainer) {
            $bak = "$Link.bak.pre-skills-vbs"
            if (Test-Path $bak) { Remove-Item $bak -Recurse -Force }
            Move-Item $Link $bak
            Write-Host "Backup $Link -> $bak"
        } else {
            Remove-Item $Link -Force
        }
    }
    $parent = Split-Path $Link -Parent
    if (-not (Test-Path $parent)) { New-Item -ItemType Directory -Path $parent | Out-Null }
    New-Item -ItemType Junction -Path $Link -Target $Target | Out-Null
    Write-Host "OK $Link -> $Target"
}

New-Item -ItemType Directory -Force -Path $DestRoot, $RulesDest | Out-Null

Set-Junction (Join-Path $DestRoot "generales") (Join-Path $SkillsSrc "generales")
Set-Junction (Join-Path $DestRoot "proyectos") (Join-Path $SkillsSrc "proyectos")
Set-Junction (Join-Path $DestRoot "usar-skills-vbs") (Join-Path $SkillsSrc "usar-skills-vbs")
Set-Junction (Join-Path $DestRoot "mantener-skills-vbs") (Join-Path $SkillsSrc "mantener-skills-vbs")

# Compat: rutas planas que ya usan las skills
Set-Junction (Join-Path $DestRoot "ssh-servidores") (Join-Path $SkillsSrc "generales\ssh-servidores")
Set-Junction (Join-Path $DestRoot "hermes-setup-and-maintenance") (Join-Path $SkillsSrc "proyectos\hermes-vbs\hermes-setup-and-maintenance")
Set-Junction (Join-Path $DestRoot "chatwoot-vbs") (Join-Path $SkillsSrc "proyectos\chatwoot-vbs\chatwoot-vbs")
Set-Junction (Join-Path $DestRoot "odoo") (Join-Path $SkillsSrc "proyectos\odoo\odoo")
Set-Junction (Join-Path $DestRoot "odoo-module-icon") (Join-Path $SkillsSrc "proyectos\odoo\odoo-module-icon")

Get-ChildItem (Join-Path $Repo ".cursor\rules\*.mdc") -ErrorAction SilentlyContinue | ForEach-Object {
    Copy-Item $_.FullName (Join-Path $RulesDest $_.Name) -Force
    Write-Host "Regla de usuario: $($_.Name)"
}

Write-Host ""
Write-Host "Listo. git pull en $Repo actualiza las skills de este PC."
Write-Host "Cloud: Settings -> Agents -> Sync Skills for Cloud Agents."
