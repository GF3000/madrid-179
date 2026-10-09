# Memoria del proyecto — Datathon CAM (localización de oficinas / reequilibrio demográfico)

Última actualización: 2026-10-07

> Lo pendiente vive en `PENDIENTES.md`; este fichero guarda hechos técnicos verificados y el historial de sesiones. Las casillas `[ ]` antiguas de abajo se migraron allí.

## Estructura de carpetas (monorepo desde 2026-10-08)
- `docs/memoria/` estado, decisiones, hallazgos técnicos (este archivo) y `PENDIENTES.md`
- `docs/fuentes/` catálogos CSV de portales + `CATALOGO_FUENTES.md` (inventario maestro con estado de verificación)
- `docs/informe/` informes, anexos PDF, diagramas y dashboard HTML generado
- `docs/presentaciones/` entregables del datathon; `_plantilla/` y `_referencias/` quedan fuera de git (plantilla Slidesgo y `Interfaz.pdf`)
- `backend/pipeline/` scripts reproducibles (recolección, procesado, modelo, generadores de PDF); los de descarga con `python -I`
- `backend/madrid179/` paquete del modelo · `backend/api/` API FastAPI · `backend/tests/` · `backend/logs/` logs de descargas (fuera de git)
- `frontend/prototipo/` prototipo HTML + JS servido por la API · `frontend/dashboard/` plantilla del dashboard · `frontend/app/` app React (pendiente #32)
- `infra/` scripts de entorno y exportación (`pptx_a_pdf.ps1`), despliegue futuro; CI en `.github/workflows/`
- `data/raw/` descargas sin modificar (fuera de git, 1,6 GB) · `data/processed/` tablas limpias (en git solo las salidas pequeñas del modelo)

## Hechos técnicos verificados (reutilizables)
- CKAN CAM: `https://datos.comunidad.madrid/catalogo/api/3/action/package_search?rows=200&start=N` → 2.263 datasets (CSV 2.218, JSON, SHP 5…).
- CKAN Ayto. Madrid: `https://datos.madrid.es/api/3/action/package_search` → 674 datasets. La URL antigua `/egob/catalogo/...csv` da 404.
- BDNS API abierta sin clave: `https://www.infosubvenciones.es/bdnstrans/api/{convocatorias|concesiones}/busqueda?regiones=27&vpd=GE&page&pageSize`. Madrid = región id 27 (`regiones=30` NO es Madrid; devuelve Ávila). Lista: `/api/regiones`.
- INE API: `https://servicios.ine.es/wstempus/js/ES/…` sin clave pero lenta. Atlas Renta = operación 353 (540 tablas, una por territorio/indicador; el nombre no indica provincia → hay que mirar `SERIES_TABLA`). DIRCE = 43, Padrón = 22, Migraciones = 455.
- Catastro INSPIRE ATOM por municipio: https://www.catastro.hacienda.gob.es/webinspire/index.html
- mivau.gob.es / mitma.gob.es dan 403 por curl.
- El prompt completo (reenviado) define 7 bloques: 1 Ayudas, 2 Inmobiliario, 3 Demografía/talento, 4 Renta/paro/afiliación, 5 Empresas/OSM, 6 Movilidad/telecom, 7 Calidad de vida. Formato de salida = fichas de 8 campos → `docs/informe/FICHAS_FUENTES.md`. El catálogo antiguo (CATALOGO_FUENTES.md) usaba bloques extrapolados; la numeración válida es la de las fichas.
- CRTM: GTFS descargables vía `https://www.arcgis.com/sharing/rest/content/items/{id}/data`; ids en `data/raw/crtm/dcat.json`. El GTFS de Cercanías del CRTM pesa 6 KB (incompleto). `nap.transportes.gob.es` da 401.
- Overpass (overpass-api.de) da 504 con consultas grandes (restauración, sanidad); reintentar por partes/provincia-comarca o usar Geofabrik PBF.
- INE DIRCE tabla 4721 (toda España, 18 MB) descargada; Seg. Social por municipio y paro ya están en el CKAN CAM (`afiliados_seg_social_ultimo_dia_mes_municipio`, hasta 2026-M08).
- Los CSV del CKAN CAM vienen en latin-1/ISO (; separador); `Territorio` es nombre, no código INE.

## Estado de tareas
- [x] Catálogo CKAN CAM completo (docs/fuentes/cam_ckan_catalogo.csv)
- [x] Catálogo CKAN Ayto. Madrid (docs/fuentes/madrid_ckan_catalogo.csv)
- [x] BDNS convocatorias Madrid (6.567) → data/raw/bdns_convocatorias_madrid.json
- [x] BDNS concesiones Madrid: 299.853 filas (solo 2022-2026 aparecen; `fechaDesde` no filtró como se esperaba)
- [x] 621 CSV municipales CAM descargados (manifiesto en `_manifest.csv`)
- [ ] INE Atlas Renta: la API Tempus fragmenta por municipio/sección (540 tablas, lenta). Usar ficheros de INEbase o paquete ineAtlas.
- [~] Catastro BU: enlaces de 179 municipios en `data/raw/catastro/atom_BU_madrid.csv`; `backend/pipeline/download_catastro_bu.py` retoma lo que falte (salta existentes)
- [ ] SEPE / Seguridad Social por municipio (ficheros mensuales)
- [ ] Banda ancha, CRTM/GTFS, OSM
- [x] Informe inicial `docs/informe/INFORME.md` (actualizar al avanzar pendientes)
- [x] Fichas de 8 campos (`docs/informe/FICHAS_FUENTES.md`, ~40 fichas)
- [x] CRTM GTFS (6 zips) + EDM2018 viajes + catálogo dcat (280 ítems)
- [x] INE DIRCE 4721; secciones censales CSV+SHP; sanidad, farmacias, Portal del Suelo, deportes, aire (cam_geo/)
- [~] OSM Overpass: hechos coworking, guarderías, gimnasios, colegios_univ; fallan por 504 restauración, sanidad (y siguientes: transporte, oficinas, parques, industrial). Log en `backend/pipeline/overpass.log`
- [ ] Enlaces de fichero SEPE mensual, cobertura FTTH/5G, Atlas Renta (ficheros), IDEM WFS, ordenanzas IBI/IAE/ICIO

## Sesión 2 — normalización y OSM (2026-10-06)
- [x] Normalización a código INE (5 díg.): `backend/pipeline/normalizar_municipios.py` → `data/processed/municipal/*.csv` (columna `ine5` añadida), `maestro_municipios.csv` (179), `cobertura_normalizacion.csv`. 579 CSV con columna Territorio; 384 cubren ≥170 municipios. Sin código quedan solo agregados (10 comarcas, distritos de Madrid, otras CCAA, "Sin municipio").
  - Clave técnica: código IECM de 4 dígitos = INE3 + dígito de control → `ine5 = "28" + cod[:3]`. El maestro sale de `padron_por_sexo.csv` (nombres limpios); `secciones_censales.csv` tiene la Ñ corrupta (TAJU/A) → NO usarlo para nombres.
  - Alias manuales: San Lorenzo del Escorial, Paracuellos del Jarama, San Agustín de Guadalix, Navarredonda, Horcajo de la Sierra, Villavieja de Lozoya, Readueña, "Municipio de Madrid"→28079. Cuidado: Horcajo de la Sierra(-Aoslos, 28070) ≠ Horcajuelo de la Sierra (28071).
  - Los CSV con territorio=distrito de Madrid no llevan ine5 (son 28079 pero a nivel distrito).
- [x] Shapefile secciones 2019 en `data/raw/cam_geo/secciones_shp/` (UTM30N EPSG:25830; CDSECCION 8 díg. → sección INE = "28"+CDSECCION).
- [x] Venv con shapely/pyshp/pyproj fuera del proyecto (scratchpad); los scripts `osm_a_secciones.py` y `gtfs_paradas_por_municipio.py` requieren ese venv (`pip install pyshp shapely pyproj pandas`).
- [x] GTFS → `data/processed/gtfs_paradas_por_municipio.csv` (13.766 paradas; 179/179 municipios con ≥1). `urbanos.zip` e `interurbanos.zip` tienen stops.txt idéntico (md5) → contado una vez.
- [x] OSM: 18 categorías descargadas (2026-10-07, incl. fast_food, bares, sanidad×4, viaria alta capacidad, deporte). Falta relanzar `osm_a_secciones.py` → PENDIENTES #19.
- [x] Catastro BU: 179/179 ZIP descargados. Aún sin procesar (GML → m² por uso).

## Sesión 3 — Red bayesiana (2026-10-06)
- [x] `backend/pipeline/construir_dataset_bn.py` → `data/processed/dataset_bn_municipios.csv` (179×~35 vars, sin nulos). Filtrar `Tipo territorio == "Municipios"`: "Municipio de Madrid" aparece también como zona estadística y duplicaría 28079.
- [x] Target = `din_emp` (IECM Dinámica Empresarial: UP nacen/mueren/entran/salen 2015-2024) → tasa neta pooled 2020-24 con contracción EB (k=mediana UP-año).
- [x] `backend/pipeline/red_bayesiana_viabilidad.py` (pgmpy 1.1.2: `DiscreteBayesianNetwork`; `fit()` ya no acepta prior_type → usar `BayesianEstimator(model,data,state_names=).get_parameters(prior_type="BDeu", equivalent_sample_size=10)`; `TabularCPD.to_dataframe()` falla en nodos raíz). Informe en `docs/informe/RED_BAYESIANA.md`.
- Resultado CV: A acc 0.48 / logloss 1.086 (uniforme 1.099); B logloss 1.625. Señal débil; elegida A.

## Sesión 4 — Dashboard de correlaciones (2026-10-06)
- [x] Artifact privado: https://claude.ai/artifact/YEoSALr5BUsqS73Fj6mb2R (fichero `docs/informe/dashboard_correlaciones.html`).
- Regenerar: `backend/pipeline/exportar_datos_dashboard.py` (venv) → `data/processed/dashboard_data.json`; inyectar en `frontend/dashboard/dashboard_template.html` (placeholder `__DATA__`) → `docs/informe/dashboard_correlaciones.html`; republicar el mismo fichero para conservar la URL.
- Correlaciones calculadas en el navegador (Spearman/Pearson, opción excluir Madrid capital).

## Sesión 5 — Transparencia de CPTs (2026-10-07)
- [x] `backend/pipeline/auditoria_cpts.py`: recalcula las 8 CPT a mano (conteo + BDeu α = ESS/(q·r)), compara con pgmpy (dif. máx. 1e-16) y reproduce 4 inferencias por enumeración de la conjunta vs VariableElimination. Falla (assert) si algo difiere.
- Salidas: `data/processed/auditoria_cpts.xlsx` (Resumen, Inferencia, Datos_discretizados, Umbrales, 1 hoja por nodo) y `docs/informe/Calculo_CPTs_CAM.pdf` (anexo 3 págs.).
- Otros PDF: `docs/informe/Fuentes_de_datos_CAM.pdf`, `docs/informe/Aproximacion_tecnica_CAM.pdf`. pandas reciente: `to_excel(w, sheet_name=...)` obligatorio por nombre.

## Sesión 6 — #1, #19, #10, #5 (2026-10-07)
- `.venv` del proyecto operativo; usarlo siempre (`.venv/Scripts/python`). `.gitignore` excluye `.venv/` y `__pycache__/`.
- OSM: 153.517 POIs; `osm_a_secciones.py` recalculado. Dashboard v2 publicado (misma URL).
- `nivel_ayudas` por tramos de población en el dataset (informativo, fuera de la red).
- GA²M: interpret-core 0.7.8, `ExplainableBoostingRegressor(interactions=5, max_bins=32, min_samples_leaf=10, outer_bags=8, learning_rate=0.02, max_rounds=3000)`; `eval_terms(X)` da contribuciones por término; `term_importances()` la importancia global. Las interacciones aportan poco (GAM 0,396 frente a GA²M 0,398).

## Sesión 7 — Monorepo, backend v1 y prototipo (2026-10-08)
- Repositorio público https://github.com/GF3000/madrid-179 (MIT). Backend v1 en la rama `feat/backend-v1`.
- `madrid179` es la fuente única de NODOS/EDGES/FILTROS; `red_bayesiana_viabilidad.py` los reexporta. `experimento_transporte.py` cambia la estructura parcheando `madrid179.red` y `madrid179.discretizacion` (no `rb`).
- El artefacto reproduce exactamente los CSV versionados (orden, puntuación, P(Alta), aportaciones; tolerancia 1e-9). Reejecutar `red_bayesiana_viabilidad.py` da CSV idénticos: el EBM es determinista con `random_state=0`.
- La validación «0,459 ± 0,012 / 1,103 ± 0,015» usa la desviación poblacional (`np.std`, ddof = 0) de 5 repeticiones de CV-5 (semillas 0-4); `entrenar.py` la reproduce.
- `auditoria_cpts.py` reescribe el xlsx y el PDF con marca de tiempo aunque no cambie nada: si solo cambia eso, restaurar con `git checkout`.
- Windows PowerShell 5.1: no admite `;` dentro de `( )`; con `$ErrorActionPreference = "Stop"` la salida a stderr de programas nativos (pip, uvicorn) se convierte en excepción; lee los `.ps1` sin BOM como ANSI (tildes rotas).
- Captura de pantalla sin navegador visible: `msedge --headless=new --window-size=1500,1000 --virtual-time-budget=8000 --screenshot=<png> <url>`.
- Experimento de variables (#44): el EBM de producción tarda ~16 s por ajuste (24 s con `n_jobs=1`); un GAM sin interacciones con 4 bolsas y `n_jobs=1` tarda 1,4 s y sirve para cribar. El GAM ligero da Spearman 0,391 frente al 0,398 de producción.
- Variables por población con OSM (sanidad, deporte, amenidades) son mayores en pueblos pequeños (pocos habitantes): casi todo lo municipal va con el tamaño; controlar siempre por población y distancia (Spearman parcial sobre rangos).
- El equipo tiene ~15 GB de RAM y a menudo < 3 GB libres: Claude Code corta los procesos en segundo plano con poca memoria. Para trabajos largos, `n_jobs` bajo y guardar resultados parciales.
