# Backend

## `pipeline/`

Scripts reproducibles, en orden de ejecución:

1. **Recolección:** `harvest_*`, `download_*`, `overpass_*` → `data/raw/`
2. **Procesado:** `normalizar_municipios.py`, `osm_a_secciones.py`, `gtfs_paradas_por_municipio.py`, `construir_dataset_bn.py`
3. **Modelo:** `red_bayesiana_viabilidad.py` (red bayesiana + GA²M + ranking), `preferencias.py` (pesos de las preferencias del usuario)
4. **Validación:** `auditoria_cpts.py` (cálculo manual frente a pgmpy), `ga2m_desempate.py`, `experimento_transporte.py`
5. **Documentación:** `diagrama_red_bayesiana.py`, `diagramas_estados_app.py`, `exportar_datos_dashboard.py`, `generar_pdf_*.py`, `construir_presentaciones.py`

Ejecuta siempre desde la raíz del repositorio: `.venv/Scripts/python backend/pipeline/<script>.py`.

Si cambia la red (nodos, aristas o umbrales), regenera en este orden: red → auditoría → diagrama → PDF de aproximación.

## `api/`

API pendiente (FastAPI, punto #28 de `docs/memoria/PENDIENTES.md`):

- puntuación de los 179 municipios según la evidencia y los filtros del usuario;
- explicación por municipio (aportaciones del GA²M y causas en la red);
- simulación de escenarios `do()`.

Los datos se servirán en Parquet, cargados en memoria.
