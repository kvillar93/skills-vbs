# Sube PEM a SSH-Infra usando `op` en ESTE proceso (app integration de Windows).
# No imprime material de claves ni tokens.
$ErrorActionPreference = "Stop"
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

$scripts = Split-Path -Parent $MyInvocation.MyCommand.Path
$vault = "SSH-Infra"
$tmp = Join-Path $env:TEMP ("op-ssh-tpl-" + [guid]::NewGuid().ToString("N"))

function Invoke-Op {
    param([string[]]$OpArgs)
    & op @OpArgs
    if ($LASTEXITCODE -ne 0) { throw "op $($OpArgs -join ' ') fallo con codigo $LASTEXITCODE" }
}

Write-Host "Iniciando sesion CLI (acepta el prompt de 1Password si aparece)..."
op signin --account my.1password.com | Out-Null
if ($LASTEXITCODE -ne 0) { throw "No pude hacer op signin" }
Write-Host "Sesion:"
op whoami

$vaultsJson = op vault list --format=json
$nombres = ($vaultsJson | ConvertFrom-Json).name
if ($nombres -notcontains $vault) {
    Write-Host "Creando vault $vault..."
    Invoke-Op @("vault","create",$vault,"--description","Claves SSH de servidores (Cursor)") | Out-Null
} else {
    Write-Host "Vault listo: $vault"
}

$existentes = @()
try {
    $existentes = @( (op item list --vault $vault --format=json | ConvertFrom-Json).title )
} catch {
    $existentes = @()
}
Write-Host ("Items ya en vault: " + ($existentes -join ", "))

New-Item -ItemType Directory -Path $tmp | Out-Null
try {
    python (Join-Path $scripts "subir_a_1password.py") --preparar-plantillas $tmp
    if ($LASTEXITCODE -ne 0) { throw "Fallo al preparar plantillas" }

    Get-ChildItem $tmp -Filter *.json | ForEach-Object {
        $titulo = $_.BaseName
        if ($existentes -contains $titulo) {
            Write-Host "YA EXISTE item $titulo"
            return
        }
        Write-Host "Importando $titulo..."
        $created = op item create --template $_.FullName --vault $vault --format=json 2>&1
        if ($LASTEXITCODE -ne 0) {
            Write-Host "FALLO $titulo : importa a mano en la app (Nuevo item -> SSH Key -> Importar archivo)"
        } else {
            $obj = $created | ConvertFrom-Json
            Write-Host ("IMPORTADA " + $obj.title + " categoria=" + $obj.category)
        }
        $created = $null
        $obj = $null
    }
} finally {
    if (Test-Path $tmp) {
        Get-ChildItem $tmp -Force | ForEach-Object { Set-Content -Path $_.FullName -Value "{}" -NoNewline }
        Remove-Item $tmp -Recurse -Force
    }
}

Write-Host "`nTitulos finales:"
op item list --vault $vault --format=json | ConvertFrom-Json | ForEach-Object { "$($_.title)  $($_.category)" }
