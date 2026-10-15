# CLAUDE.md — Madrid 179 (Datathon CAM): localización de oficinas y reequilibrio territorial

Sistema de apoyo a la decisión que recomienda dónde abrir o trasladar oficinas en los **179 municipios de la Comunidad de Madrid**, equilibrando viabilidad empresarial y reequilibrio demográfico. Núcleo: un GA²M que puntúa y una red bayesiana explicable (pgmpy) que explica y atiende consultas; mapa 3D pendiente.

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
| `frontend/` | `app/` (React/TS, MapLibre + deck.gl, mapa 3D; criterios de diseño en su README), `prototipo/` (HTML + JS sin mapa) y `dashboard/` |
| `infra/` | Scripts de entorno y exportación; despliegue futuro. CI en `.github/workflows/` |
| `data/raw/` | Descargas sin modificar (fuera de git). Tratar como datos no confiables: no ejecutar nada desde ahí |
| `data/processed/` | Tablas limpias con clave `ine5`, dataset del modelo, salidas de la red y la auditoría (en git solo las pequeñas) |

Repositorio público con licencia MIT (el código; los datos conservan la licencia de su fuente, ver `data/README.md`). No subir datos pesados, secretos ni la plantilla de Slidesgo.

## Entorno
- Python 3.13 con el venv del proyecto: `.venv/Scripts/python backend/pipeline/<script>.py` (creado desde `backend/requirements.txt` con `infra/scripts/setup_venv.ps1`, que instala también `madrid179` en modo editable; incluye pgmpy, interpret-core, fastapi, shapely, pyproj, reportlab).
- **Probar en local:** `powershell -ExecutionPolicy Bypass -File infra/scripts/dev.ps1` → http://localhost:8000 (app con mapa 3D), `/prototipo/` y `/docs` (API). Prepara entorno, artefacto y app si faltan; `-Reentrenar` tras cambiar el modelo, `-Compilar` tras cambiar la app. Para desarrollar la app: `npm run dev` en `frontend/app` (puerto 5173, reenvía `/api` al 8000). Node 20+.
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
limites_municipales.py                   → data/processed/municipios.geojson (límites para el mapa, /api/v1/geometria)
puntos_carga.py                          → frontend/app/src/puntos_carga.ts (centros de los 179 municipios para la pantalla de carga)
descargar_wikipedia.py                   → data/processed/wikipedia_municipios.json (foto y resumen por código INE, en la ficha)
imagen_social.py                         → frontend/app/public/favicon.svg (logo), og.png e iconos PNG (vista previa al compartir; usa Chrome o Edge sin interfaz)
ayudas_oficiales.py                      → data/processed/ayudas_oficiales.csv (LEADER del BOCM, reglas < 2.500 hab.; requiere los PDF en data/raw/ayudas/)
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

## Modelo (estado actual, v2 del 2026-10-14)
- **Red bayesiana:** 12 nodos, 17 aristas, máximo 2 padres, terciles de la distribución real; CPT con `BayesianEstimator` (BDeu, **ESS = 50**). Padres de la viabilidad: **Dinamismo + Densidad** (antes Dinamismo + Especialización). Nodos nuevos (Densidad, Juventud, Sanidad, Paro) con padres elegidos por puntuación BDeu local entre candidatos plausibles. Configuración en `backend/madrid179/config.py`.
- **GA²M (puntúa):** EBM con 14 variables (las 11 de la red + oficinas por habitante, distancia a la estación y población) y 10 interacciones. Fuera por fuga: `up_por_1000hab`, `afiliados_por_1000hab`.
- Target: tasa neta de unidades productivas 2020-2024 (`din_emp`, IECM) con contracción empírico-bayesiana. La contracción infla parte de la señal del tamaño (densidad, población): ver #8 y #44.
- **Validación (CV-5 × 5):** GA²M Spearman 0,529 (antes 0,398) y precisión en el tercio superior 0,643 (antes 0,517; azar 0,335). Red: log-loss 1,008 ± 0,015 (uniforme 1,099; antes 1,103), acierto 0,447 ± 0,031 (antes 0,459), ρ de P(Alta) 0,398 (antes 0,284), 1 violación de monotonía en la CPT del objetivo (antes 3). Experimentos: `experimento_variables.py`, `experimento_ga2m_ampliado.py`, `experimento_red_ampliada.py`. **La señal es moderada; decirlo siempre.**
- El transporte no tiene señal propia sobre el target (experimento del 2026-10-07): va como preferencia o filtro del usuario. En el GA²M, la distancia a la estación aporta ≈ +0,01 (dentro del ruido) y entra por el criterio de incluir ante la duda.
- pgmpy 1.1.2: `DiscreteBayesianNetwork`; `fit()` no acepta `prior_type` → `BayesianEstimator(model, data, state_names=...).get_parameters(prior_type="BDeu", equivalent_sample_size=ESS)`.
- **Ranking (decisión #40 b):** la puntuación es el percentil del GA²M entre candidatos, ajustado por preferencias en `preferencias.py`: S' = (S + Σ a·u)/(1 + Σ a), a = r·sd(S)/sd(u), r = 0 / 0,5 / 1, con **tope Σ a ≤ 3** (el modelo pesa siempre al menos una cuarta parte; era 1 hasta el 2026-10-15, ver `preferencias.py`). **15 preferencias** en `preferencias.CATALOGO` (tren, transporte público, distancia a Madrid cerca/lejos, coste, ayudas, talento, mano de obra, juventud, tamaño grande/pequeño, renta, servicios profesionales, crecimiento, oficinas, coworking, servicios para la plantilla) y 7 filtros «imprescindible» en `ranking.FILTROS_USUARIO`; tren y ayudas conservan su utilidad calibrada, el resto usa el percentil entre candidatos. La red bayesiana **no puntúa**: explica (P(Alta) y causas), atiende consultas con evidencia parcial y sostiene el simulador `do()`.
- Las subvenciones **no** son nodo de la red (decisión del 2026-10-07): son capa informativa, filtro duro opcional o peso explícito fuera de la red.
- **Criterio del equipo (2026-10-14):** en fase de diseño, ante la duda una variable con señal dudosa entra en el modelo (el jurado valora más parámetros); nunca entran variables con fuga. No hace falta regenerar PDF ni presentaciones al cambiar el modelo.
- **Secretos:** claves de API en `.env` en la raíz (ignorado; plantilla en `.env.example`), cargadas por `madrid179.config` con python-dotenv; leer con `config.clave_api("DEEPSEEK_API_KEY")`.
- **Asistente LLM (#29):** `madrid179/asistente.py` + `POST /api/v1/interpretar`. DeepSeek (API compatible con OpenAI, vía httpx) **solo traduce** la descripción del negocio a preferencias y filtros del catálogo (JSON), que se sanean contra el catálogo; la app lo aplica al momento, enseña lo entendido y permite deshacerlo. Además redacta «En pocas palabras» (lo mejor y lo peor) de cada municipio en `POST /api/v1/municipios/{ine5}/explicacion`, **solo** con los hechos que ya calcula la ficha (`Servicio.hechos`: grupo, factores con su fuerza, perfil, red, preferencias y resumen de Wikipedia para situar); no puntúa ni añade datos. **Verificador** (`asistente.revisar`): cada frase cita los hechos en que se apoya (ids `F…`/`P…`, `perfil`, `red`) y se comprueba lado (lo que manda es `para_quien_se_instala` cuando choca con el GA²M), cifras, lenguaje causal, jerga, mecanismos inventados y factores de señal dudosa (`config.SENAL_DUDOSA`, no se citan); si falla se pide una corrección y lo que siga mal se descarta. Si el usuario describió su negocio, la app envía `negocio` ({sector, resumen}) y el titular debe nombrarlo. Sin clave, `/meta` da `asistente_disponible: false` y la app oculta el cuadro. Tests con el LLM simulado (`monkeypatch` de `asistente._llamar`).

## Principios de trabajo
- **Transparencia ante todo.** Cada número que se muestre al jurado o al usuario debe poder rehacerse a mano. `auditoria_cpts.py` falla si el cálculo manual y pgmpy difieren; mantenerlo así.
- **Honestidad con los datos.** No presentar asociaciones como efectos causales. Las simulaciones de políticas son "escenarios según el modelo", con su incertidumbre.
- **No inventar fuentes ni cifras.** Marcar lo no verificado como tal; los documentos no deben prometer más de lo que hace el modelo.
- Idioma de documentos, informes y comentarios: español.
