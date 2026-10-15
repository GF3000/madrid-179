# Arranca Madrid 179 en local: API + app en http://localhost:8000 (prototipo en /prototipo/)
#
# Uso (desde la raíz del repo):
#   powershell -ExecutionPolicy Bypass -File infra/scripts/dev.ps1              # prepara lo que falte y arranca
#   powershell -ExecutionPolicy Bypass -File infra/scripts/dev.ps1 -Reentrenar  # fuerza reentrenar el modelo
#   powershell -ExecutionPolicy Bypass -File infra/scripts/dev.ps1 -Compilar    # recompila la app (frontend/app)
#   powershell -ExecutionPolicy Bypass -File infra/scripts/dev.ps1 -Puerto 8080 -SinNavegador
# Para trabajar en la app con recarga en caliente: este script en una consola y "npm run dev" en frontend/app
# (http://localhost:5173, reenvía /api a este servidor).
param([switch]$Reentrenar, [switch]$Compilar, [int]$Puerto = 8000, [switch]$SinNavegador)
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

# 3. App (React + MapLibre + deck.gl): se compila si falta; sin Node.js se sirve el prototipo
if ($Compilar -or -not (Test-Path "frontend/app/dist/index.html")) {
    if (Get-Command npm -ErrorAction SilentlyContinue) {
        Write-Host "== Compilando la app (frontend/app)" -ForegroundColor Cyan
        Push-Location frontend/app
        $global:LASTEXITCODE = 0
        if (-not (Test-Path "node_modules")) { npm ci }
        if ($LASTEXITCODE -eq 0) { npm run build }
        $ok = ($LASTEXITCODE -eq 0)
        Pop-Location
        if (-not $ok) { throw "Falló la compilación de la app" }
    } else {
        Write-Host "== Sin Node.js: se sirve el prototipo (instala Node 20+ para la app)" -ForegroundColor Yellow
    }
}

# 4. API + app
$url = "http://localhost:$Puerto"
Write-Host "== Madrid 179 en $url  (API: $url/docs)  · Ctrl+C para parar" -ForegroundColor Green
if (-not $SinNavegador) { Start-Job { Start-Sleep 3; Start-Process $using:url } | Out-Null }
& $py -m uvicorn api.main:app --app-dir backend --port $Puerto --reload --reload-dir backend
