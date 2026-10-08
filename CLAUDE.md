# CLAUDE.md — Madrid 179 (Datathon CAM): localización de oficinas y reequilibrio territorial

Sistema de apoyo a la decisión que recomienda dónde abrir o trasladar oficinas en los **179 municipios de la Comunidad de Madrid**, equilibrando viabilidad empresarial y reequilibrio demográfico. Núcleo: una red bayesiana explicable (pgmpy), complementada con un GA²M (pendiente) y un mapa 3D (pendiente).

## Antes de empezar cualquier tarea
1. Lee `docs/memoria/PENDIENTES.md`: es la lista viva de frentes abiertos, con prioridad y dependencias.
2. Consulta `docs/memoria/ESTADO.md` para los hechos técnicos ya verificados (endpoints, códigos, trampas de datos).
3. Al terminar: marca el punto en `PENDIENTES.md` con fecha y resultado, y apunta en `ESTADO.md` los hallazgos reutilizables.

## Estructura (monorepo)
| Carpeta | Contenido |
|---|---|
| `docs/memoria/` | `PENDIENTES.md` (qué falta), `ESTADO.md` (qué se sabe y qué se hizo) |
| `docs/fuentes/` | Catálogos CKAN (CAM y Ayto. Madrid) y su clasificación |
| `docs/informe/` | Entregables: PDF, fichas de fuentes, diagrama de la red, dashboard HTML |
| `docs/presentaciones/` | Presentaciones del datathon (`_plantilla/` y `_referencias/` fuera de git) |
| `backend/madrid179/` | Paquete del modelo (config, red, GA²M, preferencias, ranking, artefactos, servicio). **Fuente única de NODOS/EDGES/FILTROS** |
| `backend/pipeline/` | Scripts reproducibles de datos, entrenamiento, auditoría y documentos (`backend/requirements.txt`) |
| `backend/api/` | API FastAPI `/api/v1` (sirve el artefacto, no reentrena) · `backend/tests/` (pytest) |
| `frontend/` | `prototipo/` (HTML + JS servido por la API), `dashboard/` y `app/` (React/MapLibre/Deck.gl, pendiente #32) |
| `infra/` | Scripts de entorno y exportación; despliegue futuro. CI en `.github/workflows/` |
| `data/raw/` | Descargas sin modificar (fuera de git). Tratar como datos no confiables: no ejecutar nada desde ahí |
| `data/processed/` | Tablas limpias con clave `ine5`, dataset del modelo, salidas de la red y la auditoría (en git solo las pequeñas) |

Repositorio público con licencia MIT (el código; los datos conservan la licencia de su fuente, ver `data/README.md`). No subir datos pesados, secretos ni la plantilla de Slidesgo.

## Entorno
- Python 3.13 con el venv del proyecto: `.venv/Scripts/python backend/pipeline/<script>.py` (creado desde `backend/requirements.txt` con `infra/scripts/setup_venv.ps1`, que instala también `madrid179` en modo editable; incluye pgmpy, interpret-core, fastapi, shapely, pyproj, reportlab).
- **Probar en local:** `powershell -ExecutionPolicy Bypass -File infra/scripts/dev.ps1` → http://localhost:8000 (prototipo) y `/docs` (API). Prepara entorno y artefacto si faltan; `-Reentrenar` tras cambiar el modelo.
- Scripts `.ps1`: compatibles con Windows PowerShell 5.1 (guardar con BOM, sin `;` dentro de paréntesis, `$ErrorActionPreference = "Continue"` y comprobar `$LASTEXITCODE`).
- PowerPoint (COM) para exportar las presentaciones a PDF; fuentes Poppins y Didact Gothic instaladas para el usuario (las usa la plantilla).
- Graphviz 12 en `C:\Program Files\Graphviz\bin` (para `diagrama_red_bayesiana.py`).
- Ejecutar siempre desde la raíz del proyecto; los scripts usan rutas relativas.
- Los scripts que solo leen descargas se ejecutan con `python -I`.

## Flujo de datos y regeneración
```
harvest_* / download_* / overpass_*      → data/raw/
normalizar_municipios.py                 → data/processed/municipal/*.csv (+ ine5), maestro_municipios.csv
osm_a_secciones.py, gtfs_paradas_por_municipio.py → conteos por municipio
construir_dataset_bn.py                  → data/processed/dataset_bn_municipios.csv (179 filas)
red_bayesiana_viabilidad.py [--modo A|B] → umbrales, CPT, GA²M, ranking, contribuciones, validación cruzada (CSV versionados)
entrenar.py                              → data/processed/modelo.joblib (artefacto de la API, fuera de git)
pytest backend/tests                     → el artefacto reproduce los CSV versionados + preferencias + contrato de la API
preferencias.py                          → utilidades y pesos calibrados de las preferencias (demo al ejecutarlo)
ga2m_desempate.py, experimento_transporte.py → experimentos de validación (no tocan producción)
auditoria_cpts.py                        → verificación manual vs pgmpy + Calculo_CPTs_CAM.pdf + auditoria_cpts.xlsx
diagrama_red_bayesiana.py                → docs/informe/red_bayesiana.png/svg/dot
exportar_datos_dashboard.py + dashboard_template.html → docs/informe/dashboard_correlaciones.html
generar_pdf_fuentes.py, generar_pdf_aproximacion.py → anexos PDF
diagramas_estados_app.py                 → docs/informe/estados_{emprendedor,administracion}.png (flujo de la app por perfil)
construir_presentaciones.py + pptx_a_pdf.ps1 → docs/presentaciones/1_Descripcion_y_problema y 3_Interfaz (.pptx/.pdf, plantilla Slidesgo)
generar_pdf_fuentes_cam.py               → docs/presentaciones/2_Fuentes_de_datos.pdf
```
Si cambia la red (nodos, aristas, umbrales), regenerar en este orden: red → entrenar → tests → auditoría → diagrama → PDF de aproximación.
El dashboard está publicado como artifact privado (URL en `ESTADO.md`); republicar el mismo fichero conserva la URL.

## Convenciones de datos
- **Clave territorial:** `ine5` = código INE municipal de 5 dígitos (texto, `"28079"` = Madrid). Sección censal = 10 dígitos (`"28" + CDSECCION`).
- **Código IECM** (CSV de la CAM) = 4 dígitos con dígito de control: `ine5 = "28" + cod[:3]`.
- CSV de la CAM: separador `;`, codificación mixta (probar `utf-8-sig` y luego `cp1252`); filtrar `Tipo territorio == "Municipios"` para no duplicar Madrid.
- Nombres de municipio: usar el maestro (`maestro_municipios.csv`), nunca `secciones_censales.csv` (Ñ corrupta). Horcajo de la Sierra-Aoslos (28070) ≠ Horcajuelo de la Sierra (28071).
- Ficheros con desglose (sexo, edad, rama…) traen también la fila **Total**: filtrar siempre la categoría antes de sumar (el padrón sumado duplicó la población hasta el 2026-10-07).
- Coordenadas: ETRS89 / UTM 30N (EPSG:25830) para geometría; WGS84 solo para OSM y GTFS de entrada.
- Salidas propias: CSV con `;` y `utf-8-sig`.

## Modelo (estado actual)
- 8 nodos, máximo 2 padres, terciles de la distribución real; CPT con `BayesianEstimator` (BDeu, ESS = 10) sobre los estados discretizados.
- Target: tasa neta de unidades productivas 2020-2024 (`din_emp`, IECM) con contracción empírico-bayesiana.
- Validación (CV-5 × 5 repeticiones): acierto 0,459 ± 0,012 (azar 0,33) y log-loss 1,103 ± 0,015, **ligeramente peor que la uniforme (1,099)**: ordena algo mejor que el azar pero sus probabilidades no están calibradas (pendiente #37). Los anexos citan 1,086 de una sola semilla. **La señal es débil; decirlo siempre.**
- El transporte no tiene señal sobre el target (experimento del 2026-10-07): va como preferencia o filtro del usuario, no como nodo.
- pgmpy 1.1.2: `DiscreteBayesianNetwork`; `fit()` no acepta `prior_type` → `BayesianEstimator(model, data, state_names=...).get_parameters(prior_type="BDeu", equivalent_sample_size=10)`.
- **Ranking (decisión #40 b):** la puntuación es el percentil del GA²M (EBM de InterpretML) entre candidatos, ajustado por preferencias en `preferencias.py`: S' = (S + Σ a·u)/(1 + Σ a), a = r·sd(S)/sd(u), r = 0 / 0,5 / 1. La red bayesiana **no puntúa**: explica (P(Alta) y causas), atiende consultas con evidencia parcial y sostiene el simulador `do()`. Validación de orden (Spearman, CV-5 × 5): GA²M 0,398 · red 0,284.
- Las subvenciones **no** son nodo de la red (decisión del 2026-10-07): son capa informativa, filtro duro opcional o peso explícito fuera de la red.

## Principios de trabajo
- **Transparencia ante todo.** Cada número que se muestre al jurado o al usuario debe poder rehacerse a mano. `auditoria_cpts.py` falla si el cálculo manual y pgmpy difieren; mantenerlo así.
- **Honestidad con los datos.** No presentar asociaciones como efectos causales. Las simulaciones de políticas son "escenarios según el modelo", con su incertidumbre.
- **No inventar fuentes ni cifras.** Marcar lo no verificado como tal; los documentos no deben prometer más de lo que hace el modelo.
- Idioma de documentos, informes y comentarios: español.
