# Catálogo maestro de fuentes — Comunidad de Madrid (CAM)

Estado de verificación: **[API✔]** probada y devuelve datos · **[URL✔]** HTTP 200 comprobado · **[DESCARGADO]** datos en `data/raw/` · **[SIN VERIFICAR]** conocida pero no comprobada en esta sesión (verificar antes de usar).
Fecha de rastreo: 2026-10-06. Clave de unión: código INE municipal (5 dígitos, 28xxx), sección censal (10 dígitos), coordenadas ETRS89/UTM30.

## A. Portales-catálogo (fuentes “madre”)
| ID | Fuente | URL | Acceso | Granularidad | Estado |
|---|---|---|---|---|---|
| A1 | Datos abiertos CAM (CKAN, 2.263 datasets) | https://datos.comunidad.madrid/catalogo | API CKAN `/catalogo/api/3/action/package_search`; CSV/JSON por recurso | municipal, distrito, sección, puntual | API✔ DESCARGADO (catálogo + 196 CSV municipales) |
| A2 | Datos abiertos Ayto. Madrid (CKAN, 674 datasets) | https://datos.madrid.es | `/api/3/action/package_search`, SPARQL | distrito, barrio, sección, puntual | API✔ DESCARGADO (catálogo) |
| A3 | Portal Estadístico CAM / Instituto de Estadística | https://www.madrid.org/iestadis/ | web + Banco de Datos Municipal | municipal, distrito | URL✔ |
| A4 | Banco de Datos Municipal (Almudena) | https://gestiona.comunidad.madrid/desvan/Inicio.icm?enlace=almudena | consulta web / export | municipal (series largas) | URL✔(vía búsqueda) |
| A5 | datos.gob.es (federado, filtro Admin. autonómica/local) | https://datos.gob.es/es/catalogo | API | todos | URL✔ |
| A6 | INE API Tempus | https://servicios.ine.es/wstempus/js/ES/ | JSON REST sin clave | municipio, distrito, sección | API✔ |
| A7 | CNIG Centro de Descargas | https://centrodedescargas.cnig.es | descarga | límites, MDT, CNIG, BTN | URL✔ |
| A8 | Nomecalles / Callejero (IECM) | https://www.madrid.org/iestadis/ (Nomenclátor) | web | calle/portal | SIN VERIFICAR |

## B. Bloque 1 — Ayudas, subvenciones, incentivos
| ID | Fuente | URL / endpoint | Notas | Estado |
|---|---|---|---|---|
| B1 | BDNS convocatorias (API abierta, sin clave) | `https://www.infosubvenciones.es/bdnstrans/api/convocatorias/busqueda?regiones=27&vpd=GE&page=N&pageSize=1000` | **Madrid = región id 27 (ES300)** (id 25=ES3, 26=ES30). 6.567 convocatorias con ámbito Madrid (5.460 locales, 971 estado, 120 autonómicas). Filtro = ámbito geográfico, NO órgano concedente; para CAM como concedente filtrar `nivel2`. | API✔ DESCARGADO |
| B2 | BDNS concesiones | `.../concesiones/busqueda?regiones=27&vpd=GE&fechaDesde=01/01/2019` | beneficiario (NIF), importe, convocatoria. Tamaño grande; descarga en curso/ver `docs/memoria/ESTADO.md` | API✔ |
| B3 | BDNS otros endpoints (minimis, grandes beneficiarios, sanciones, planes estratégicos) | https://www.infosubvenciones.es/bdnstrans | | SIN VERIFICAR |
| B4 | Plan de Reequilibrio Territorial y Lucha contra la Despoblación (2023, 2024, 2025) — 4,5 M€/año, municipios <20.000 hab. (139-142), 73 <2.500 | https://www.comunidad.madrid/noticias/2025/06/25/comunidad-madrid-invierte-45-millones-ayudas-despoblacion-pequenos-municipios ; http://sede.comunidad.madrid/node/281764 | Lista de beneficiarios en BOCM/Consejo de Gobierno | URL (búsqueda) |
| B5 | “Pueblos con Vida” (>155 M€ hasta 2026; 142 municipios <20.000 hab.) | https://www.comunidad.madrid (buscar “Pueblos con vida”) | variable binaria “municipio objetivo” | URL (búsqueda) |
| B6 | Rebajas fiscales para residentes en municipios <2.500 hab. (IRPF autonómico, anunciado 2023) | https://www.telemadrid.es/noticias/madrid/La-Comunidad-de-Madrid-hara-rebajas-fiscales-a-quien-se-mude-a-municipios-de-menos-de-2500-habitantes-0-2601339842--20230929072903.html | verificar norma en BOCM | URL (búsqueda) |
| B7 | Ayudas estatales contra la despoblación (96 municipios de Madrid elegibles, 80 M€) | https://madridinforma.eldiario.es/municipios-madrid-ayudas-despoblacion-80-millones/ | contrastar con fuente oficial MITECO/Reto Demográfico | URL (búsqueda) |
| B8 | BOCM (normativa, incentivos, ordenanzas publicadas) | https://www.bocm.es | búsqueda por texto; sin API abierta verificada | URL✔ |
| B9 | Ordenanzas fiscales municipales (IBI, IAE, ICIO): tipos y bonificaciones | webs de cada ayuntamiento + Dirección General de Tributos (Haciendas Locales) | requiere scraping/recopilación; 179 municipios | SIN VERIFICAR |
| B10 | Hacienda – Presupuestos y liquidaciones de EELL (tipos IBI por municipio, recaudación) | https://www.hacienda.gob.es (Entidades Locales: consulta de presupuestos/liquidaciones; “Tipos de gravamen IBI”) | SIN VERIFICAR |
| B11 | CAM CKAN: “Recaudación tributaria de impuestos”, “Impuesto matriculación” etc. | ver `cam_ckan_catalogo.csv` grupo Hacienda (51) | | DESCARGADO (catálogo) |
| B12 | Portal del Suelo 4.0 (parcelas publicadas) | CKAN dataset `parcelas_portal_suelo` | suelo industrial/terciario disponible | DESCARGADO |
| B13 | Fondos europeos / Madrid Digital / CDTI / Enisa / IMADE (Fundación Madri+d, Madrid Emprende) | webs respectivas; BDNS cubre parte | | SIN VERIFICAR |

## C. Bloque 2 — Mercado inmobiliario terciario y suelo
| ID | Fuente | URL | Notas | Estado |
|---|---|---|---|---|
| C1 | Catastro INSPIRE ATOM (parcelas CP, edificios BU con uso dominante: oficinas/comercial/industrial, direcciones AD) por municipio | https://www.catastro.hacienda.gob.es/webinspire/index.html | descarga gratuita por municipio, 2 actualizaciones/año | URL✔ |
| C2 | Catastro: difusión datos (fichero masivo CAT, estadísticas) | https://www.sedecatastro.gob.es/Accesos/SECAccDescargaDatos.aspx | CAT = superficie construida por uso por unidad urbana | URL✔ |
| C3 | CAM CKAN Catastro Inmobiliario municipal: `valor_catastral_urbano_por_uso`, `parcelas_urbanas_por_edificacion`, recibos catastro | datos.comunidad.madrid | por municipio | DESCARGADO |
| C4 | CAM CKAN transacciones inmobiliarias y valor tasado por municipio (`transacciones_*`, `valor_tasado_vivienda_municipio_antiguedad`) | datos.comunidad.madrid | vivienda (no terciario) — proxy de coste | DESCARGADO |
| C5 | MIVAU/MITMA Observatorio de Vivienda y Suelo; valor tasado y precio suelo urbano (municipios >25.000 hab.) | https://www.mivau.gob.es (403 a curl; probar navegador) | SIN VERIFICAR |
| C6 | Notarios / Registradores (compraventas, precio) | https://www.notariado.org (Portal estadístico) ; https://www.registradores.org | SIN VERIFICAR |
| C7 | Portales: Idealista (informes y API restringida), Fotocasa, Habitaclia, pisos.com; consultoras (CBRE, JLL, Colliers, Cushman, Savills: mercado oficinas, vacancia, rentas prime por submercado) | webs respectivas | datos agregados en informes PDF trimestrales; scraping sujeto a ToS | SIN VERIFICAR |
| C8 | Ayto. Madrid: Censo de locales y actividades (abiertos/cerrados), licencias urbanísticas, agencia de actividades | https://datos.madrid.es (buscar “locales”, “licencias”) | ver `madrid_ckan_catalogo.csv` | DESCARGADO (catálogo) |
| C9 | Planeamiento: Visor urbanístico CAM (clasificación y calificación del suelo, SIGUM), SIOSE, Corine | CAM Cartografía / CNIG | SIN VERIFICAR |
| C10 | Polígonos industriales y áreas empresariales (Madrid Emprende / IMADE / Consejería Economía) | CKAN CAM (buscar “polígono”, “suelo industrial”) | 0 títulos con “polígono” en CKAN → buscar en Cartografía/IMADE | SIN VERIFICAR |

## D. Bloque 3 — Demografía, talento, brecha territorial
| ID | Fuente | URL | Notas | Estado |
|---|---|---|---|---|
| D1 | INE Padrón continuo / Cifras oficiales de población (op. DPOP id 22, ECP 450) | API Tempus `TABLAS_OPERACION/22` | municipal, sexo, edad | API✔ |
| D2 | INE Atlas de Distribución de Renta de los Hogares (op. 353, 2015-2023): renta media/mediana, Gini, P80/P20, % <40% mediana, fuentes de ingreso, **sección censal/distrito/municipio** | https://www.ine.es/dynt3/inebase/index.htm?padre=12385 ; API `TABLAS_OPERACION/353` (540 tablas; tabla 30656 = indicadores renta) | clave para renta por sección | API✔ (lista de tablas en `data/raw/ine/`) |
| D3 | INE Censo de Población y Viviendas 2021 (sección censal: nivel formativo, edad, hogares, nacionalidad, vivienda) op. 8 / 463 | https://www.ine.es/censos2021 | SIN VERIFICAR en detalle |
| D4 | INE Estadística de Migraciones y Cambios de Residencia (op. 455/71): altas/bajas residenciales entre municipios | API Tempus | tasa de fuga, saldo migratorio municipal | API✔ (listado) |
| D5 | INE Movimiento Natural de la Población (nacimientos/defunciones → saldo vegetativo) op. 311 | API Tempus | | API✔ (listado) |
| D6 | CAM CKAN Demografía (146 datasets): `padron_por_sexo`, `edad_media_por_nacionalidad_y_sexo`, censo anual municipios, migraciones | datos.comunidad.madrid | | DESCARGADO |
| D7 | Ayto. Madrid: Padrón por distrito/barrio/sección, Panel de indicadores de distritos y barrios, estudios sociodemográficos | https://www.madrid.es/go/DatosAbiertos/PanelIndicadores ; datos.madrid.es | | URL✔ |
| D8 | Distribución renta hogares – Ayto. Madrid (barrio/distrito) | madrid.es Estadística > Renta | | URL (búsqueda) |
| D9 | Universidades (en CAM: UCM, UAM, UAH, UPM, URJC, UC3M, UNED, privadas): matrícula y egresados por centro (CKAN “universitarias”, 43 datasets); Ministerio de Universidades (SIIU) | datos.comunidad.madrid ; https://www.universidades.gob.es | localiza oferta de talento | DESCARGADO (parcial) |
| D10 | Formación Profesional: centros y matrícula (Consejería Educación) | CKAN CAM Educación (217) | | catálogo |
| D11 | Observatorio de Educación / PIAAC, nivel formativo por municipio (Censo 2021 + Padrón) | INE | | SIN VERIFICAR |

## E. Bloque 4 (extrapolado; el prompt llega cortado) — Empleo y tejido empresarial
| ID | Fuente | URL | Notas | Estado |
|---|---|---|---|---|
| E1 | SEPE: paro registrado y contratos por municipio (mensual) | https://www.sepe.es/HomeSepe/que-es-el-sepe/estadisticas/datos-estadisticos/municipios.html | municipal | URL✔ |
| E2 | Seguridad Social: afiliados por municipio (estadísticas por municipios, EST8) | https://www.seg-social.es/wps/portal/wss/internet/EstadisticasPresupuestosEstudios/Estadisticas/EST8 | municipal, régimen | URL✔ |
| E3 | INE DIRCE (op. 43): empresas por municipio, CNAE, estrato de asalariados | API Tempus `TABLAS_OPERACION/43` | densidad empresarial | API✔ (listado) |
| E4 | CAM CKAN Empleo (186) y Economía (299): afiliados, paro registrado, contratos, colectivo empresarial por distrito y rama | datos.comunidad.madrid | | DESCARGADO (parcial) |
| E5 | Renta Disponible Bruta Municipal (IECM) | https://gestiona.comunidad.madrid/desvan/AccionDatosTemaMunicipal.icm?codTema=1930406 | municipal | URL✔ |
| E6 | Agencia Tributaria: estadísticas IRPF por municipio (>1.000 hab.) | https://sede.agenciatributaria.gob.es (Estadísticas) | SIN VERIFICAR |
| E7 | Registro Mercantil / SABI / Informa / Axesor (empresas por sede) | privado | de pago | SIN VERIFICAR |

## F. Conectividad, movilidad, servicios, entorno (variables de localización)
| ID | Fuente | Notas | Estado |
|---|---|---|---|
| F1 | Cobertura banda ancha (fibra/FTTH, 5G) — SETID / Ministerio Transformación Digital “Cobertura de banda ancha” | por unidad poblacional/municipio; https://avancedigital.mineco.gob.es | SIN VERIFICAR |
| F2 | CRTM (Consorcio Transportes): paradas, líneas, GTFS, zonas tarifarias, demanda | https://www.crtm.es (portal de datos; `data.crtm.es` no respondió) | SIN VERIFICAR |
| F3 | Cercanías Renfe/Adif GTFS, estaciones | https://data.renfe.com ; adif.es | SIN VERIFICAR |
| F4 | DGT / Ministerio Transportes: IMD tráfico, red viaria (accesibilidad a M-30/M-40/M-50/R-x) | https://www.mitma.gob.es | SIN VERIFICAR |
| F5 | CAM CKAN Transporte (86) e Infraestructuras (49) | datos.comunidad.madrid | catálogo |
| F6 | Sanidad (303 datasets: centros, camas) y Educación (centros) georreferenciados | CKAN CAM | catálogo |
| F7 | Medio ambiente: calidad del aire (Ayto./CAM), ruido, zonas verdes, riesgo (CKAN 89) | CKAN CAM / datos.madrid.es | catálogo |
| F8 | Turismo (27), Cultura (74), Seguridad (24): atractivo/calidad de vida | CKAN CAM | catálogo |
| F9 | OpenStreetMap (Geofabrik Madrid): POIs, coworkings, cafés, comercio | https://download.geofabrik.de/europe/spain/madrid.html | SIN VERIFICAR |
| F10 | Medio Rural (94 datasets CAM): explotaciones, ayudas PAC, turismo rural | CKAN CAM | catálogo |
| F11 | Elecciones, participación (clima político local) | CKAN CAM | catálogo |

## G. Geometrías para el dashboard 3D
| ID | Fuente | Notas |
|---|---|---|
| G1 | CNIG límites municipales / secciones censales (INE cartografía) https://www.ine.es/ss/Satellite?L=es_ES&c=Page&cid=1259952026632&p=1259952026632&pagename=ProductosYServicios%2FPYSLayout | SIN VERIFICAR |
| G2 | Catastro edificios BU (huella + nº plantas) → extrusión 3D | URL✔ (C1) |
| G3 | MDT05/MDT25 CNIG, LiDAR PNOA | URL✔ (A7) |
| G4 | Distritos y barrios Madrid (shapefile en datos.madrid.es) | catálogo |

## Limitaciones conocidas
- Buscador `WebSearch` es US-only y devuelve resúmenes: las URLs marcadas “(búsqueda)” provienen de resultados, no de apertura directa.
- `mivau.gob.es` / `mitma.gob.es` devuelven 403 a curl; pueden funcionar en navegador.
- La capa BDNS filtrada por región id 27 incluye convocatorias que *afectan* a Madrid, no solo las concedidas por la CAM.
- El prompt original está truncado tras “estudios universitarios y…”; los bloques E–G son una extrapolación razonable, no un encargo explícito.
