# Copia extras (addyosmani + ui-ux-pro-max) a un repo que YA tiene .cursor/skills.
# No pisa skills VBS ni otras que ya existan. -SkipExisting es el comportamiento por defecto.
param(
    [Parameter(Mandatory = $true)][string]$Destino,
    [switch]$SkipExisting,
    [switch]$ActualizarAddy,
    [switch]$ActualizarExtras
)
$ErrorActionPreference = "Stop"
$Repo = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$ExtrasRoot = Join-Path $Repo ".cursor\skills\extras"
$Dest = Join-Path $Destino ".cursor\skills"
New-Item -ItemType Directory -Force -Path $Dest | Out-Null

# Nombres que nunca se sobrescriben (skills VBS del repo destino o del usuario).
$Protegidas = @(
    "generales",
    "proyectos",
    "usar-skills-vbs",
    "mantener-skills-vbs",
    "ssh-servidores",
    "hermes-setup-and-maintenance",
    "hermes-vbs",
    "chatwoot-vbs",
    "odoo",
    "odoo-module-icon"
)

# Por defecto no pisa. -SkipExisting lo deja explícito.
# -ActualizarAddy / -ActualizarExtras solo refrescan extras, nunca las protegidas.
$SaltarExistentes = $true
if ($ActualizarAddy -or $ActualizarExtras) { $SaltarExistentes = $false }
if ($SkipExisting) { $SaltarExistentes = $true }

$Packs = @(
    @{
        Nombre = "addyosmani"
        ActualizarEste = ($ActualizarAddy -or $ActualizarExtras)
    },
    @{
        Nombre = "ui-ux-pro-max"
        ActualizarEste = $ActualizarExtras
    }
)

foreach ($pack in $Packs) {
    $Src = Join-Path $ExtrasRoot $pack.Nombre
    if (-not (Test-Path $Src)) {
        Write-Host "AVISO: no encuentro extras $($pack.Nombre) en $Src"
        continue
    }

    Get-ChildItem $Src -Directory | Where-Object { $_.Name -notlike "_*" } | ForEach-Object {
        if ($Protegidas -contains $_.Name) {
            Write-Host "SKIP (protegida VBS) $($_.Name)"
            return
        }
        $out = Join-Path $Dest $_.Name
        $existe = Test-Path $out
        if ($existe -and ($SaltarExistentes -or -not $pack.ActualizarEste)) {
            Write-Host "SKIP (ya existe) $($_.Name)"
            return
        }
        if ($existe) { Remove-Item $out -Recurse -Force }
        Copy-Item $_.FullName $out -Recurse -Force
        Write-Host "COPIADA $($pack.Nombre)/$($_.Name)"
    }
}

$refSrc = Join-Path $ExtrasRoot "addyosmani\_references"
$refDst = Join-Path $Destino ".cursor\addyosmani-references"
if (Test-Path $refSrc) {
    if ((-not (Test-Path $refDst)) -or ($ActualizarAddy -or $ActualizarExtras)) {
        if ((Test-Path $refDst) -and -not $SaltarExistentes) {
            Remove-Item $refDst -Recurse -Force
            Copy-Item $refSrc $refDst -Recurse -Force
            Write-Host "Referencias en .cursor/addyosmani-references"
        } elseif (-not (Test-Path $refDst)) {
            Copy-Item $refSrc $refDst -Recurse -Force
            Write-Host "Referencias en .cursor/addyosmani-references"
        } else {
            Write-Host "SKIP (ya existe) addyosmani-references"
        }
    }
}

$rules = Join-Path $Destino ".cursor\rules"
New-Item -ItemType Directory -Force -Path $rules | Out-Null
$mdc = Join-Path $rules "skills-vbs-extras.mdc"
if (-not (Test-Path $mdc)) {
    @"
---
description: Skills extra (Addy Osmani + UI/UX Pro Max). No pisan las skills VBS ni las del repo.
alwaysApply: false
---

# Extras skills-vbs

Este repo puede tener skills de ingenieria y de UI/UX en `.cursor/skills/` copiadas desde skills-vbs/extras (addyosmani y ui-ux-pro-max).
Si el trabajo es TDD, review, spec, frontend o debug, usa las extras de Addy.
Si el trabajo es diseño de interfaces, design system, brand o slides, usa ui-ux-pro-max.
Si el trabajo es SSH, Hermes, Chatwoot u Odoo, usa las skills VBS (usuario o de este repo), no las extras.
"@ | Set-Content -Path $mdc -Encoding utf8
    Write-Host "Regla $mdc"
}

# Compat: deja la regla vieja si ya existía; si no, no la creamos de nuevo.
Write-Host "Listo en $Destino"
