# Copia extras Addy Osmani a un repo que YA tiene .cursor/skills, sin pisar las locales.
param(
    [Parameter(Mandatory = $true)][string]$Destino,
    [switch]$ActualizarAddy
)
$ErrorActionPreference = "Stop"
$Repo = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$Src = Join-Path $Repo ".cursor\skills\extras\addyosmani"
if (-not (Test-Path $Src)) { throw "No encuentro extras Addy en $Src" }
$Dest = Join-Path $Destino ".cursor\skills"
New-Item -ItemType Directory -Force -Path $Dest | Out-Null

Get-ChildItem $Src -Directory | Where-Object { $_.Name -notlike "_*" } | ForEach-Object {
    $out = Join-Path $Dest $_.Name
    if ((Test-Path $out) -and -not $ActualizarAddy) {
        Write-Host "SKIP (ya existe) $($_.Name)"
        return
    }
    if (Test-Path $out) { Remove-Item $out -Recurse -Force }
    Copy-Item $_.FullName $out -Recurse -Force
    Write-Host "COPIADA $($_.Name)"
}

$refSrc = Join-Path $Src "_references"
$refDst = Join-Path $Destino ".cursor\addyosmani-references"
if (Test-Path $refSrc) {
    if ((-not (Test-Path $refDst)) -or $ActualizarAddy) {
        if (Test-Path $refDst) { Remove-Item $refDst -Recurse -Force }
        Copy-Item $refSrc $refDst -Recurse -Force
        Write-Host "Referencias en .cursor/addyosmani-references"
    }
}

$rules = Join-Path $Destino ".cursor\rules"
New-Item -ItemType Directory -Force -Path $rules | Out-Null
$mdc = Join-Path $rules "addyosmani-extras.mdc"
if (-not (Test-Path $mdc)) {
    @"
---
description: Skills extra de Addy Osmani (TDD, review, spec). No pisan las skills VBS ni las del repo.
alwaysApply: false
---

# Extras Addy Osmani

Este repo tiene skills de ingenieria en `.cursor/skills/` copiadas desde skills-vbs/extras/addyosmani.
Si el trabajo es TDD, review, spec, frontend o debug, usa esas skills.
Si el trabajo es SSH, Hermes o Chatwoot, usa las skills VBS (usuario o de este repo), no las extras.
"@ | Set-Content -Path $mdc -Encoding utf8
    Write-Host "Regla $mdc"
}

Write-Host "Listo en $Destino"
