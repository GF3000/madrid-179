# Crea .venv en la raíz e instala las dependencias del backend y el paquete madrid179 (editable).
# Uso (desde la raíz del repo): powershell -File infra/scripts/setup_venv.ps1
$ErrorActionPreference = "Continue"  # pip escribe avisos en stderr; se comprueba $LASTEXITCODE
function Comprobar($paso) { if ($LASTEXITCODE -ne 0) { throw "Falló: $paso" } }
if (-not (Test-Path ".venv")) { py -3.13 -m venv .venv; Comprobar "crear .venv (¿está instalado Python 3.13?)" }
& .venv/Scripts/python -m pip install --upgrade pip
Comprobar "actualizar pip"
& .venv/Scripts/python -m pip install -r backend/requirements.txt
Comprobar "instalar backend/requirements.txt"
& .venv/Scripts/python -m pip install -e backend
Comprobar "instalar el paquete madrid179"
& .venv/Scripts/python -c "import pgmpy, interpret, fastapi, madrid179; print('Entorno listo')"
