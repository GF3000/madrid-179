# Backend

Arquitectura y decisiones: [`docs/arquitectura/BACKEND.md`](../docs/arquitectura/BACKEND.md). Para arrancarlo en local, ver el README de la raíz (`infra/scripts/dev.ps1`).

## `madrid179/`: el modelo como paquete

Lógica pura, importable desde el pipeline, la API y los tests (instalado en modo editable: `pip install -e backend`).

| Módulo | Qué hace |
|---|---|
| `config.py` | Nodos, DAG, filtros duros, hiperparámetros, rutas, aviso de señal débil |
| `discretizacion.py` | Terciles sobre los 179 municipios |
| `red.py` | Red bayesiana (BDeu, ESS = 10), validación cruzada, inferencia |
| `ga2m.py` | EBM de InterpretML: predicción y aportaciones por término |
| `preferencias.py` | Utilidades de transporte y ayudas, pesos calibrados por dispersión |
| `ranking.py` | Filtros → percentil del GA²M entre candidatos → preferencias → orden |
| `artefactos.py` | Entrena y guarda/carga `data/processed/modelo.joblib` |
| `servicio.py` | Lo que expone la API (meta, municipios, ranking, ficha, consulta), sin depender de FastAPI |

## `api/`: FastAPI

`main.py` (rutas, carga del artefacto al arrancar, CORS para `localhost`, sirve el prototipo en `/`) y `esquemas.py` (contrato Pydantic).

| Endpoint | Qué devuelve |
|---|---|
| `GET /api/v1/meta` | Versión del modelo, validación, aviso, nodos y estados |
| `GET /api/v1/municipios` | Los 179 municipios con estados y si son candidatos |
| `POST /api/v1/ranking` | Ranking según preferencias y filtros «imprescindible» |
| `GET /api/v1/municipios/{ine5}` | Ficha: aportaciones del GA²M, red bayesiana, discrepancias |
| `POST /api/v1/consulta` | P(Viabilidad) con evidencia parcial y municipios que la cumplen |

La API no reentrena: sirve el artefacto. Variable de entorno opcional `MADRID179_MODELO` para usar otro artefacto.

## `pipeline/`: scripts reproducibles

1. **Recolección:** `harvest_*`, `download_*`, `overpass_*` → `data/raw/`
2. **Procesado:** `normalizar_municipios.py`, `osm_a_secciones.py`, `gtfs_paradas_por_municipio.py`, `construir_dataset_bn.py`
3. **Modelo:** `entrenar.py` (artefacto para la API), `red_bayesiana_viabilidad.py` (salidas CSV versionadas), `preferencias.py` (demo)
4. **Validación:** `auditoria_cpts.py` (cálculo manual frente a pgmpy), `ga2m_desempate.py`, `experimento_transporte.py`
5. **Documentación:** `diagrama_red_bayesiana.py`, `diagramas_estados_app.py`, `exportar_datos_dashboard.py`, `generar_pdf_*.py`, `construir_presentaciones.py`

Ejecuta siempre desde la raíz: `.venv/Scripts/python backend/pipeline/<script>.py`.

Si cambia el modelo (nodos, aristas, umbrales, hiperparámetros): `red_bayesiana_viabilidad.py` → `entrenar.py` → `pytest backend/tests` → auditoría → diagrama → PDF de aproximación. `test_equivalencia.py` falla si el artefacto y los CSV versionados no coinciden.

## `tests/`

```powershell
.venv/Scripts/python -m pytest backend/tests
```

Necesitan el artefacto (`entrenar.py`). Cubren la equivalencia con las salidas versionadas, los pesos de las preferencias documentados en `PENDIENTES.md` y el contrato de la API.
