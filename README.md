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
│   ├── pipeline/        # descarga, normalización, dataset, red bayesiana, GA²M, auditoría, generadores de PDF
│   ├── api/             # API FastAPI (en preparación)
│   └── requirements.txt
├── frontend/
│   ├── dashboard/       # plantilla del dashboard de correlaciones
│   └── app/             # aplicación web con mapa (en preparación)
├── infra/
│   └── scripts/         # entorno y exportación de presentaciones
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

## Puesta en marcha

Requisitos: Python 3.13 y Windows (los generadores de PDF usan fuentes del sistema). Graphviz solo para los diagramas.

```powershell
powershell -File infra/scripts/setup_venv.ps1          # crea .venv e instala backend/requirements.txt
.venv/Scripts/python backend/pipeline/red_bayesiana_viabilidad.py
.venv/Scripts/python backend/pipeline/auditoria_cpts.py
```

Ejecuta siempre desde la raíz del repositorio: los scripts usan rutas relativas. El flujo completo de regeneración, desde las descargas hasta los anexos, está en [`CLAUDE.md`](CLAUDE.md) y en [`data/README.md`](data/README.md).

## Documentación

- [Hoja de ruta y pendientes](docs/memoria/PENDIENTES.md)
- [Hechos técnicos y decisiones](docs/memoria/ESTADO.md)
- [Red bayesiana: método y validación](docs/informe/RED_BAYESIANA.md)
- [Fichas de fuentes](docs/informe/FICHAS_FUENTES.md)

## Licencia

El código se publica con licencia [MIT](LICENSE). Los datos derivados conservan la licencia de su fuente original (ver [`data/README.md`](data/README.md)).
