# afterFileEdit: git add del archivo de skill tocado. No hace commit ni push.
$ErrorActionPreference = "SilentlyContinue"
$raw = [Console]::In.ReadToEnd()
try { $j = $raw | ConvertFrom-Json } catch { Write-Output '{"permission":"allow"}'; exit 0 }
$path = $j.file_path
if (-not $path) { $path = $j.path }
if (-not $path) { Write-Output '{"permission":"allow"}'; exit 0 }
$repo = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
if ($path -notmatch "skills-vbs|\.cursor\\skills|\\.cursor/skills") {
    Write-Output '{"permission":"allow"}'
    exit 0
}
Push-Location $repo
git add -- "$path" 2>$null | Out-Null
Pop-Location
Write-Output '{"permission":"allow"}'
exit 0
