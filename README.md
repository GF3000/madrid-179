# Madrid 179

Sistema de apoyo a la decisión para elegir dónde abrir o trasladar oficinas en los **179 municipios de la Comunidad de Madrid**, equilibrando la viabilidad empresarial y el reequilibrio territorial. Proyecto del Datathon de la Comunidad de Madrid.

- **Puntuación:** un GA²M (EBM de InterpretML) ordena los municipios candidatos, ajustado por las preferencias del usuario (transporte, ayudas).
- **Explicación:** una red bayesiana de 8 nodos (pgmpy) da P(viabilidad alta), las causas y las consultas con evidencia parcial, y sostiene un simulador de escenarios `do()`.
- **Transparencia:** cada probabilidad de la red puede rehacerse a mano; `backend/pipeline/auditoria_cpts.py` falla si el cálculo manual y pgmpy no coinciden.

> **Limitación conocida.** La señal es débil: en validación cruzada (CV-5 × 5) la red acierta el 45,9 % ± 1,2 % de las veces (azar: 33 %), pero su log-loss (1,103) no mejora a la distribución uniforme (1,099). Los resultados son asociaciones, no efectos causales, y las simulaciones son escenarios según el modelo.

## Estructura del monorepo

```
.
├── backend/
│   ├── madrid179/       # paquete del modelo: red bayesiana, GA²M, preferencias, ranking, servicio
│   ├── api/             # API FastAPI (/api/v1)
│   ├── pipeline/        # descarga, normalización, dataset, entrenamiento, auditoría, generadores de PDF
│   ├── tests/
│   └── requirements.txt
├── frontend/
│   ├── prototipo/       # prototipo sin mapa para probar el modelo (HTML + JS, lo sirve la API)
│   ├── dashboard/       # plantilla del dashboard de correlaciones
│   └── app/             # aplicación web con mapa (en preparación)
├── infra/
│   └── scripts/         # dev.ps1 (arranque local), entorno y exportación de presentaciones
├── data/
│   ├── raw/             # descargas (no versionadas)
│   └── processed/       # tablas limpias; solo las salidas pequeñas del modelo están en git
├── docs/
│   ├── memoria/         # PENDIENTES.md (hoja de ruta) y ESTADO.md (hechos verificados)
│   ├── fuentes/         # catálogos de datos abiertos
│   ├── informe/         # informe técnico, anexos PDF y diagramas
│   └── presentaciones/  # entregables del datathon
└── .github/workflows/   # CI
```

## Probar en local

Requisitos: Windows con Python 3.13 (`py -3.13`). Desde la raíz del repositorio:

```powershell
powershell -ExecutionPolicy Bypass -File infra/scripts/dev.ps1
```

La primera vez crea `.venv`, instala las dependencias y entrena el modelo (unos 2-3 minutos); después arranca en segundos. Se abre el navegador en:

- **http://localhost:8000**: prototipo (ranking con preferencias y filtros, ficha explicada de cada municipio, consultas a la red);
- **http://localhost:8000/docs**: la API, documentada y ejecutable desde el navegador.

Opciones: `-Reentrenar` (tras cambiar el modelo o los datos), `-Puerto 8080`, `-SinNavegador`. `Ctrl+C` para parar.

Sin el script, paso a paso:

```powershell
powershell -File infra/scripts/setup_venv.ps1                       # entorno (una vez)
.venv/Scripts/python backend/pipeline/entrenar.py                   # modelo -> data/processed/modelo.joblib
.venv/Scripts/python -m uvicorn api.main:app --app-dir backend      # API + prototipo
.venv/Scripts/python -m pytest backend/tests                        # tests
```

## Regenerar datos e informes

Los scripts de `backend/pipeline/` se ejecutan desde la raíz (usan rutas relativas). Los generadores de PDF usan fuentes de Windows y Graphviz para los diagramas. El flujo completo, desde las descargas hasta los anexos, está en [`CLAUDE.md`](CLAUDE.md) y en [`data/README.md`](data/README.md).

## Documentación

- [Hoja de ruta y pendientes](docs/memoria/PENDIENTES.md)
- [Hechos técnicos y decisiones](docs/memoria/ESTADO.md)
- [Arquitectura del backend](docs/arquitectura/BACKEND.md)
- [Red bayesiana: método y validación](docs/informe/RED_BAYESIANA.md)
- [Fichas de fuentes](docs/informe/FICHAS_FUENTES.md)

## Autores

- **Gregorio García Velasco** · Universidad Carlos III de Madrid (UC3M)
- **Guillermo Franco Gimeno** · Universidad Politécnica de Madrid (UPM)

## Licencia

El código se publica con licencia [MIT](LICENSE). Los datos derivados conservan la licencia de su fuente original (ver [`data/README.md`](data/README.md)).
