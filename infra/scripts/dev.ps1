# Arranca Madrid 179 en local: API + prototipo en http://localhost:8000
#
# Uso (desde la raíz del repo):
#   powershell -ExecutionPolicy Bypass -File infra/scripts/dev.ps1              # prepara lo que falte y arranca
#   powershell -ExecutionPolicy Bypass -File infra/scripts/dev.ps1 -Reentrenar  # fuerza reentrenar el modelo
#   powershell -ExecutionPolicy Bypass -File infra/scripts/dev.ps1 -Puerto 8080 -SinNavegador
param([switch]$Reentrenar, [int]$Puerto = 8000, [switch]$SinNavegador)
# "Continue": uvicorn y pip escriben en stderr y PowerShell 5.1 lo trataría como error; se comprueba $LASTEXITCODE
$ErrorActionPreference = "Continue"
Set-Location (Resolve-Path "$PSScriptRoot/../..")
$env:PYTHONIOENCODING = "utf-8"
$py = ".venv/Scripts/python.exe"

# 1. Entorno
$listo = $false
if (Test-Path $py) {
    & $py -c "import importlib.util as u, sys; sys.exit(0 if u.find_spec('fastapi') and u.find_spec('madrid179') else 1)"
    $listo = ($LASTEXITCODE -eq 0)
}
if (-not $listo) {
    Write-Host "== Preparando el entorno (solo la primera vez)" -ForegroundColor Cyan
    & "$PSScriptRoot/setup_venv.ps1"
    if ($LASTEXITCODE -ne 0) { throw "Falló la preparación del entorno" }
}

# 2. Modelo
if ($Reentrenar -or -not (Test-Path "data/processed/modelo.joblib")) {
    if (-not (Test-Path "data/processed/dataset_bn_municipios.csv")) {
        throw "Falta data/processed/dataset_bn_municipios.csv (está en git: haz git pull)."
    }
    Write-Host "== Entrenando el modelo (~1 min)" -ForegroundColor Cyan
    & $py backend/pipeline/entrenar.py
    if ($LASTEXITCODE -ne 0) { throw "Falló el entrenamiento" }
}

# 3. API + prototipo
$url = "http://localhost:$Puerto"
Write-Host "== Madrid 179 en $url  (API: $url/docs)  · Ctrl+C para parar" -ForegroundColor Green
if (-not $SinNavegador) { Start-Job { Start-Sleep 3; Start-Process $using:url } | Out-Null }
& $py -m uvicorn api.main:app --app-dir backend --port $Puerto --reload --reload-dir backend
