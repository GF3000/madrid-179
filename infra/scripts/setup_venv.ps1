# Crea .venv en la raíz e instala las dependencias del backend.
# Uso (desde la raíz del repo): powershell -File infra/scripts/setup_venv.ps1
$ErrorActionPreference = "Stop"
if (-not (Test-Path ".venv")) { py -3.13 -m venv .venv }
& .venv/Scripts/python -m pip install --upgrade pip
& .venv/Scripts/python -m pip install -r backend/requirements.txt
& .venv/Scripts/python -c "import pgmpy, interpret; print('Entorno listo')"
