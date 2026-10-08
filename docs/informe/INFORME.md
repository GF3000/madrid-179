# Informe de catalogación de datos — Comunidad de Madrid (2026-10-06)

## Resumen
Se ha inventariado y descargado el grueso de fuentes abiertas accesibles por API/descarga directa. Detalle completo y estado de verificación por fuente: `docs/fuentes/CATALOGO_FUENTES.md`.

| Activo | Cantidad | Ubicación |
|---|---|---|
| Datasets catálogo CAM (CKAN) | 2.263 (22 temas; 2.218 con CSV) | `docs/fuentes/cam_ckan_catalogo.csv`, clasificado por bloque en `cam_ckan_clasificado_por_bloque.csv` |
| Datasets catálogo Ayto. Madrid | 674 | `docs/fuentes/madrid_ckan_catalogo.csv` |
| CSV municipales/distritales CAM descargados | 621 (≈661 MB), 0 errores | `data/raw/cam_municipal/` + `_manifest.csv` |
| BDNS convocatorias con ámbito Madrid | 6.567 (5.460 locales, 971 estatales, 120 autonómicas) | `data/raw/bdns_convocatorias_madrid.json` |
| BDNS concesiones con ámbito Madrid | 299.853 (≈10.190 M€; años 2022-2026 en la muestra) | `data/raw/bdns_concesiones_madrid.json` |
| Catastro INSPIRE edificios (uso, plantas, huella) | 179 municipios listados; descarga ZIP en curso | `data/raw/catastro/` |

Cobertura temática del catálogo CAM por palabras clave (un dataset puede estar en varios bloques): demografía/talento 737, empleo/economía 346, servicios/entorno 266, inmobiliario/suelo 218, conectividad/movilidad 104, ayudas/fiscalidad 79; 853 sin clasificar (clasificación heurística por título, a revisar).

## Hallazgos por bloque
1. **Ayudas**: BDNS tiene API abierta y se descargó completa para Madrid. En convocatorias: ~129 mencionan empleo, ~199 digitalización/I+D+i, ~77 autoempleo/emprendimiento, ~75 locales/alquiler/oficina, 19 despoblación/rural, 11 polígonos/industrial (búsqueda por regex en descripción). Los planes de reequilibrio/“Pueblos con Vida” (municipios <20.000 hab., 142; 73 <2.500) están en notas de prensa y sede CAM; la lista oficial de municipios beneficiarios debe extraerse del BOCM. Ordenanzas fiscales (IBI/IAE/ICIO) **no** tienen dataset unificado: requieren recopilación municipio a municipio (179).
2. **Inmobiliario**: no existe fuente abierta oficial de alquiler/venta de oficinas por municipio. Opciones: Catastro (superficie y uso, abierta), Portal del Suelo 4.0 (descargado), valores catastrales y transacciones de vivienda por municipio (CAM, descargados) y consultoras/portales (privado, informes PDF o scraping con ToS).
3. **Demografía/talento**: CAM CKAN + INE + Ayto. Madrid cubren padrón, migraciones, edad, universidades. Renta por sección censal: Atlas INE (op. 353); su API Tempus fragmenta por territorio y es lenta → usar la descarga de ficheros de INEbase o el paquete `ineAtlas` (pendiente).
4. **Empleo/empresa, conectividad, servicios**: ver secciones E-F del catálogo; muchas son SIN VERIFICAR.

## Limitaciones y cautelas
- El filtro de región de BDNS indica ámbito geográfico, no órgano concedente; el importe total incluye ayudas estatales con ámbito Madrid. El parámetro `fechaDesde` no pareció limitar el rango (solo aparecen 2022-2026): validar antes de usar series largas.
- La clasificación por bloques es por palabras clave del título: sobreinclusiva (p. ej. “vivienda”) y sin leer metadatos.
- No se ha validado la calidad, cobertura temporal ni unión por código INE de los 621 CSV; es recolección masiva, la criba va después.
- El prompt original estaba truncado; los bloques de empleo, conectividad y servicios son extrapolación.

## Pendiente
Atlas de Renta INE (ficheros), Padrón/Censo 2021 por sección, SEPE y Seguridad Social por municipio, DIRCE, banda ancha, CRTM/GTFS, OSM, ordenanzas fiscales, BOCM de planes de despoblación, geometrías de secciones censales, consultoras de oficinas.
