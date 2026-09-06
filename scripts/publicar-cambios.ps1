# Commit y push de cambios de skills en este repo.
param(
    [string]$Mensaje = "skill: actualizar skills-vbs"
)
$ErrorActionPreference = "Stop"
$Repo = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Repo

git add -A
$status = git status --porcelain
if (-not $status) {
    Write-Host "Nada que publicar."
    exit 0
}

# HEREDOC no es nativo en Windows PowerShell 5; -m es suficiente aqui.
git commit -m $Mensaje
if ($LASTEXITCODE -ne 0) { throw "commit fallo" }
git push -u origin HEAD
if ($LASTEXITCODE -ne 0) { throw "push fallo" }
Write-Host "Publicado en origin: $Mensaje"
