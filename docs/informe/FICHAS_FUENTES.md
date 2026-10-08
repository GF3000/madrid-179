# Fichas de fuentes — formato estricto (8 campos)

Fecha: 2026-10-06. Etiquetas de estado: **[DESCARGADO]** archivo local en `data/raw/`; **[API✔]** endpoint probado; **[URL✔]** página responde; **[A VERIFICAR]** no abierta/probada, columnas no confirmadas.
Utilidad: **V** = Viabilidad de la oficina · **C** = Coste operativo · **R** = Impacto de Reequilibrio demográfico.
Clave de unión: los CSV del CKAN de la CAM traen `Territorio` (nombre) y a menudo `Código territorio`; las secciones censales traen `municipio_codigo` de 3 dígitos (INE = 28 + código). Unir por nombre exige normalizar (“ACEBEDA, LA”).

---
## BLOQUE 1 — Ayudas, subvenciones e incentivos

### F1.1 BDNS — Convocatorias (ámbito Madrid)
1. Convocatorias de subvenciones y ayudas con ámbito geográfico Comunidad de Madrid
2. BDNS / Intervención General de la Administración del Estado (infosubvenciones.es)
3. `https://www.infosubvenciones.es/bdnstrans/api/convocatorias/busqueda?regiones=27&vpd=GE&page=0&pageSize=1000` (Madrid = región 27/ES300; catálogo de regiones `/api/regiones`) **[API✔][DESCARGADO]** 6.567 filas
4. id, numeroConvocatoria, descripcion, fechaRecepcion, nivel1 (ESTADO/AUTONOMICA/LOCAL/OTROS), nivel2, nivel3 (órgano). El detalle por convocatoria (finalidad, sector, instrumento, presupuesto) se obtiene con `/convocatorias?numConv=` (A VERIFICAR)
5. Convocatoria/órgano (el municipio solo se deduce de `nivel3` en convocatorias locales)
6. REST API JSON, sin clave
7. Continua (alta diaria); 2014-2026
8. R/V: intensidad de incentivos por territorio (empleo, digitalización, rural, polígonos); regex sobre `descripcion` da ~129 empleo, ~199 digitalización/I+D+i, ~77 autoempleo, 19 despoblación. Limitación: el filtro es ámbito, no concedente.

### F1.2 BDNS — Concesiones (ámbito Madrid)
1. Concesiones de ayudas con ámbito Madrid
2. BDNS
3. `.../api/concesiones/busqueda?regiones=27&vpd=GE&page=N&pageSize=1000` **[API✔][DESCARGADO]** 299.853 filas (≈10.190 M€; años 2022-2026)
4. codConcesion, fechaConcesion, beneficiario (NIF + nombre), instrumento, importe, ayudaEquivalente, numeroConvocatoria, idConvocatoria, convocatoria, nivel1-3, fechaAlta
5. Beneficiario (NIF); sin municipio → requiere cruce con DIRCE/Registro Mercantil
6. REST API JSON
7. Continua. Ojo: `fechaDesde` no recortó el rango como se esperaba
8. R: ayudas efectivamente captadas por tipo de beneficiario; V: ayudas a alquiler/digitalización.

### F1.3 Plan de Reequilibrio Territorial y Lucha contra la Despoblación / “Pueblos con Vida”
1. Planes 2023-2025 de reequilibrio (4,5 M€/año; municipios <20.000 hab.: 139-142; 73 <2.500 hab.) y programa Pueblos con Vida (>155 M€ hasta 2026)
2. Comunidad de Madrid (Consejería de Presidencia / Administración Local)
3. `https://www.comunidad.madrid/noticias/2025/06/25/comunidad-madrid-invierte-45-millones-ayudas-despoblacion-pequenos-municipios` · `http://sede.comunidad.madrid/node/281764` **[URL de búsqueda; A VERIFICAR]**
4. Municipio beneficiario, línea, importe (a extraer de acuerdos del Consejo de Gobierno / BOCM)
5. Municipio
6. Web scraping / PDF BOCM
7. Anual
8. R: define variable objetivo “municipio prioritario de reequilibrio”; C: incentivos locales.

### F1.4 Rebajas fiscales en municipios <2.500 hab.
1. Deducción autonómica IRPF por residencia en municipios en riesgo de despoblación
2. Comunidad de Madrid / BOCM
3. Noticia: `https://www.telemadrid.es/noticias/madrid/La-Comunidad-de-Madrid-hara-rebajas-fiscales-a-quien-se-mude-a-municipios-de-menos-de-2500-habitantes-0-2601339842--20230929072903.html`; norma exacta en `https://www.bocm.es` **[A VERIFICAR]**
4. Lista de municipios elegibles, porcentaje/importe de deducción
5. Municipio
6. Scraping BOCM
7. Anual
8. R/C: incentivo fiscal a la persona (no a la empresa); útil como covariable de atracción.

### F1.5 Ordenanzas fiscales municipales (IBI, IAE, ICIO)
1. Tipos de gravamen y bonificaciones locales
2. 179 ayuntamientos; agregado parcial en Ministerio de Hacienda (Haciendas Locales)
3. Webs municipales / `https://www.hacienda.gob.es` (Entidades Locales) **[A VERIFICAR]**
4. IBI urbano (tipo %), coeficiente IAE, bonificaciones por creación de empleo, ICIO (%), bonificación por interés municipal
5. Municipio
6. Scraping/PDF (sin dataset unificado; en el CKAN de la CAM solo hay recaudación, no tipos)
7. Anual
8. C: variable central de coste operativo fiscal por municipio.

### F1.6 CKAN CAM — Hacienda/Sector público (51+58 datasets) y recaudación
1. Recaudación tributaria, presupuestos, impuesto de matriculación, etc.
2. Consejería de Economía, Hacienda y Empleo
3. `https://datos.comunidad.madrid/catalogo/api/3/action/package_search?fq=groups:hacienda` **[API✔]** catálogo en `docs/fuentes/cam_ckan_catalogo.csv`
4. Según dataset (ver CSV)
5. Mayormente CAM; algunos municipales
6. CSV/JSON
7. Anual/trimestral
8. C: contexto fiscal.

### F1.7 BOCM
1. Boletín Oficial de la CAM
2. Comunidad de Madrid
3. `https://www.bocm.es` **[URL✔]**
4. Texto normativo (incentivos, exenciones, convocatorias, listados de beneficiarios)
5. CAM / municipal según disposición
6. Web scraping (sin API verificada; PDF/HTML)
7. Diaria
8. R/C: trazabilidad normativa.

---
## BLOQUE 2 — Mercado inmobiliario terciario y suelo

### F2.1 Catastro INSPIRE — Edificios (BU)
1. Edificios catastrales por municipio (huella, uso dominante, plantas)
2. Dirección General del Catastro
3. Índice: `https://www.catastro.hacienda.gob.es/INSPIRE/Buildings/28/ES.SDGC.BU.atom_28.xml` **[API✔]** · enlaces ZIP de 179 municipios en `data/raw/catastro/atom_BU_madrid.csv` · **[DESCARGADO parcial: descarga en curso]**
4. currentUse (residential/industrial/office/retail/publicServices/agriculture), numberOfFloorsAboveGround, officialArea / grossFloorArea, dateOfConstruction, condición, referencia catastral, geometría
5. Edificio (polígono GML ETRS89)
6. ATOM → ZIP GML
7. Semestral (último 2026-08)
8. V/C: m² construidos por uso (oferta terciaria, antigüedad del parque), base para el 3D (extrusión por plantas).

### F2.2 Catastro INSPIRE — Parcelas (CP) y Direcciones (AD)
1. Parcelas catastrales y direcciones por municipio
2. DGC
3. `https://www.catastro.hacienda.gob.es/INSPIRE/CadastralParcels/28/ES.SDGC.CP.atom_28.xml` **[API✔]** enlaces en `atom_CP_madrid.csv`; no descargado
4. nationalCadastralReference, areaValue, geometría; AD: dirección, coordenadas
5. Parcela / portal (X,Y)
6. ATOM → ZIP GML
7. Semestral
8. V: suelo disponible/ocupación; geocodificación.

### F2.3 Catastro — Fichero masivo CAT / estadísticas
1. Difusión de datos catastrales (uso, superficie, valor por unidad urbana)
2. DGC (Sede Electrónica)
3. `https://www.sedecatastro.gob.es/Accesos/SECAccDescargaDatos.aspx` **[URL✔]**
4. Superficie construida por uso y destino (oficinas, comercial, industrial, almacén), año construcción, valor catastral
5. Unidad urbana / parcela
6. Fichero CAT de texto de ancho fijo (requiere procesado)
7. Anual
8. V/C: m² por uso terciario (oficinas/comercio/industria) por municipio.

### F2.4 CKAN CAM — Catastro inmobiliario municipal
1. Valor catastral urbano por uso; parcelas urbanas por edificación; recibos
2. DG Catastro vía Instituto de Estadística CAM
3. `https://datos.comunidad.madrid/catalogo/dataset/valor_catastral_urbano_por_uso` **[DESCARGADO]**
4. Año, Tipo territorio, Código territorio, Territorio, Uso (Residencial, …), Valor (miles €)
5. Municipio
6. CSV
7. Anual (desde 2003)
8. C: valor catastral no residencial como proxy de coste de suelo/inmueble.

### F2.5 CKAN CAM — Alquiler y valor tasado por municipio
1. Alquiler medio mensual y €/m² de viviendas arrendadas (valor catastral, municipios >20.000 hab.); valor tasado vivienda por municipio y antigüedad; transacciones inmobiliarias por municipio; precio medio suelo urbano
2. Ministerio (MIVAU/Catastro/Registradores) vía CAM
3. `https://datos.comunidad.madrid/catalogo/dataset/alquiler_metro_cuadrado_mensual_viviendas_arrendadas_valor_catastral_municipios_`, `.../transacciones_inmobiliarias_municipio`, `.../valor_tasado_vivienda_municipio_antiguedad`, `.../precio_medio_suelo_urbano` **[DESCARGADO]**
4. Año, Periodo, Territorio, Indicador, Valor, Unidad (ej. precio medio suelo urbano: €/m², CM = 187,8 €/m² 2026-T1)
5. Municipio (suelo: por tamaño de municipio)
6. CSV/JSON
7. Trimestral/anual
8. C: coste residencial (retención de talento) y de suelo; **no es oficina**.

### F2.6 Portal del Suelo 4.0 (parcelas publicadas)
1. Parcelas de suelo público ofertadas (uso terciario, industrial, dotacional)
2. Dirección General de Suelo (CAM)
3. `https://datos.comunidad.madrid/catalogo/dataset/parcelas_portal_suelo` **[DESCARGADO]**
4. referencia_codigo, gestor, municipio_codigo/descripcion, localizacion (actuación), régimen, clase, uso_principal_codigo, urbanizacion, superficie_registrada, superficie_edificable, descripción, observaciones, referencia_catastral
5. Parcela (referencia catastral → geocodificable)
6. CSV
7. Continua
8. V/R: oferta concreta de suelo terciario en municipios (ej. “Móstoles Tecnológico” junto a la URJC).

### F2.7 Informes de mercado de oficinas (consultoras) y portales
1. Rentas prime/medias (€/m²/mes), vacancia, absorción por submercado (CBD, Periferia, A-1, A-2…)
2. CBRE, JLL, Colliers, Cushman & Wakefield, Savills; Idealista/Fotocasa (locales/oficinas)
3. Webs de consultoras; **no hay API abierta** **[A VERIFICAR]**
4. Renta €/m²/mes, vacancia %, stock m², absorción, pipeline
5. Submercado (no municipal salvo corredores)
6. PDF trimestrales / scraping sujeto a ToS
7. Trimestral
8. C/V: único origen realista de renta y vacancia de oficinas.

### F2.9 Ayto. Madrid — Censo de locales y actividades; licencias
1. Locales y actividades económicas (abiertos/cerrados), licencias urbanísticas
2. Ayuntamiento de Madrid
3. `https://datos.madrid.es/api/3/action/package_search?q=locales` **[API✔]** catálogo en `docs/fuentes/madrid_ckan_catalogo.csv`; datasets concretos A VERIFICAR
4. Epígrafe IAE, situación (abierto/cerrado), superficie, dirección, coordenadas
5. Local / distrito / barrio
6. CSV/JSON
7. Anual/continua
8. V: vacancia comercial en la capital.

---
## BLOQUE 3 — Demografía y talento

### F3.1 CKAN CAM — Padrón, censo, migraciones, movimiento natural
1. Población por sexo/edad/nacionalidad; edad media; migraciones; nacimientos/defunciones; censo 2021
2. Instituto de Estadística CAM / INE
3. `https://datos.comunidad.madrid/catalogo/dataset/padron_por_sexo` (+ `edad_media_por_nacionalidad_y_sexo`, `migraciones_*`, `mnp_*`) **[DESCARGADO]**
4. Año, Tipo territorio, Código territorio, Territorio, Sexo, Valor, Unidad (padrón desde 1996)
5. Municipio (a veces distrito/sección en Madrid)
6. CSV/JSON
7. Anual
8. R: población, pirámide, saldo, envejecimiento, dependencia, fuga (cálculo derivado).

### F3.2 INE — Cifras de población / Estadística Continua de Población / Migraciones
1. Series municipales de población, ECP, estadística de migraciones y cambios de residencia
2. INE
3. `https://servicios.ine.es/wstempus/js/ES/TABLAS_OPERACION/22` (también 450, 455, 311) **[API✔]**; lista en `data/raw/ine/tablas_operaciones.json`
4. Población por sexo/edad/nacionalidad, flujos de altas/bajas residenciales entre municipios
5. Municipio
6. REST JSON (lenta)
7. Anual/semestral
8. R: saldo migratorio interno (fuga hacia/desde la capital).

### F3.3 INE — Censo de Población y Viviendas 2021 (sección censal)
1. Nivel formativo, edad, hogares, nacionalidad, viviendas por sección censal
2. INE
3. `https://www.ine.es/censos2021` **[A VERIFICAR]**; en CAM: `censo_2021_*` **[DESCARGADO]** (viviendas por tipo/tenencia/consumo eléctrico, municipal)
4. % estudios superiores, tamaño de hogar, tenencia, etc.
5. Sección censal / municipio
6. CSV/Excel/API
7. 2021 (estático)
8. R/V: % población universitaria/postgrado (talento).

### F3.4 Universidades y estudiantes
1. Oferta de plazas, grados por universidad, becas, PDI de universidades
2. Consejería de Educación / Ministerio de Universidades
3. CKAN CAM: `1921001` (grados por universidad y rama), `502002` (plazas), `centros_universitarios_privados_*` **[DESCARGADO parcial]**; campus georreferenciados: usar OSM `colegios_univ` (en curso)
4. Universidad, rama, plazas, matrícula, becas
5. Universidad/centro (no por alumno-residencia)
6. CSV
7. Anual
8. V/R: distancia candidato-municipio↔campus; egresados por rama.

### F3.5 Ayto. Madrid — Padrón y panel de indicadores por distrito/barrio
1. Padrón y panel sociodemográfico (21 distritos, 131 barrios)
2. Ayuntamiento de Madrid
3. `https://www.madrid.es/go/DatosAbiertos/PanelIndicadores` **[URL✔]**; `https://datos.madrid.es` **[API✔]**
4. Población por edad/sexo/nacionalidad, indicadores de envejecimiento, estudios
5. Barrio / distrito / sección
6. CSV/XLSX
7. Anual
8. R: granularidad intraurbana de la capital.

---
## BLOQUE 4 — Socioeconomía y renta

### F4.1 INE — Atlas de Distribución de Renta de los Hogares (ADRH)
1. ADRH 2015-2023: renta neta media por persona y por hogar, mediana, Gini, P80/P20, % por debajo de 40/50/60% mediana, fuentes de ingreso
2. INE (con datos de AEAT y haciendas forales)
3. `https://www.ine.es/dynt3/inebase/index.htm?padre=12385&capsel=12384` **[URL✔]**; API Tempus op. 353, 540 tablas, p.ej. tabla 30656 `https://servicios.ine.es/wstempus/js/ES/DATOS_TABLA/30656` **[API✔]**
4. Renta neta media persona/hogar, renta bruta media, mediana, Gini, P80/P20, % fuentes (salario, pensiones, prestaciones…), % población <60% mediana
5. Sección censal, distrito, municipio
6. API fragmentada por territorio (lenta) / descargas CSV en INEbase; paquete R `ineAtlas` (https://pablogguz.github.io/ineAtlas/) **[A VERIFICAR descarga masiva]**
7. Anual (último 2023)
8. R/C: poder adquisitivo local, demanda y coste salarial.

### F4.2 Renta Disponible Bruta Municipal (IECM) y PIB municipal
1. RDBM per cápita; PIB municipal
2. Instituto de Estadística CAM
3. `https://gestiona.comunidad.madrid/desvan/AccionDatosTemaMunicipal.icm?codTema=1930406` **[URL✔]**; CKAN `pib_municipal_porcentaje_2015` **[DESCARGADO]**
4. Euros/hab., índice base
5. Municipio
6. Web / CSV
7. Anual
8. V/R.

### F4.3 SEPE — Paro registrado y contratos por municipio
1. Paro registrado, demandantes, contratos por municipio, sexo, edad, sector
2. SEPE
3. `https://www.sepe.es/HomeSepe/que-es-el-sepe/estadisticas/datos-estadisticos/municipios.html` **[URL✔]**; hay páginas mensuales (2005-ago 2026); enlaces de fichero no confirmados **[A VERIFICAR]**. Alternativa CAM: `paro_registrado_*` **[DESCARGADO]** (CM, no municipal)
4. Paro por sexo/edad/sector, contratos por tipo
5. Municipio
6. XLS/CSV por mes (scraping de enlaces)
7. Mensual
8. V/R: bolsa de empleo disponible local.

### F4.4 Seguridad Social — Afiliados por municipio y sector
1. Afiliados por municipio de residencia y de ubicación de cuenta de cotización
2. TGSS / Instituto de Estadística CAM
3. CKAN: `afiliados_seg_social_ultimo_dia_mes_municipio` (hasta 2026-M08), `afiliados_por_residencia_y_{sexo,edad,rama,grupo,contrato,jornada,nacionalidad,empleo}`, `afiliados_por_ubicacion_y_{rama,regimen}` **[DESCARGADO]**; origen: `https://www.seg-social.es/wps/portal/wss/internet/EstadisticasPresupuestosEstudios/Estadisticas/EST8` y PX-Web `https://w6.seg-social.es/PXWeb` **[URL✔]**
4. Año, Periodo, Territorio, Indicador, Valor (personas); desagregación sexo/edad/rama CNAE/régimen/contrato
5. Municipio (residencia vs. lugar de trabajo → **flujos de commuting implícitos**)
6. CSV
7. Mensual
8. V/R: diferencia residentes–empleos por municipio = índice de dormitorio; sector por municipio.

---
## BLOQUE 5 — Tejido empresarial y ecosistema

### F5.1 INE DIRCE — Empresas por municipio, CNAE y estrato
1. Directorio Central de Empresas (2025)
2. INE
3. `https://servicios.ine.es/wstempus/js/ES/DATOS_TABLA/4721?nult=1` **[API✔][DESCARGADO]** `data/raw/ine/dirce_4721.json` (toda España, 18 MB; filtrar Madrid por nombre)
4. Empresas por municipio × CNAE × (estrato en otras tablas de la op. 43)
5. Municipio
6. REST JSON
7. Anual (1-ene-2025)
8. V: densidad empresarial y especialización (servicios, tech, logística, industria).

### F5.2 IECM — Colectivo empresarial y unidades económicas (Nomecalles)
1. Unidades productivas y ocupados por rama, estrato y distrito; ficheros de unidades económicas con CNAE-4 y coordenadas ETRS89-30
2. Instituto de Estadística CAM
3. CKAN: `col_emp_ramas`, `col_emp_estratos`, `col_emp_manufact`, `colectivo_empresarial_base_2015_por_distrito_*` **[DESCARGADO]**; micro-fichero de unidades: `https://web.comunidad.madrid/iestadis/fijas/estructu/economicas/ocupacion/colectivo_empresarial_intedatos.htm` **[A VERIFICAR]**
4. Unidades productivas, ocupados, rama R12/R66, estrato de empleo; (micro: denominación, municipio, CNAE-4, X/Y)
5. Municipio/distrito (micro: coordenadas)
6. CSV / ficheros descargables
7. Anual
8. V: clústeres sectoriales; coordenadas permiten densidad por celda.

### F5.3 Nomecalles — Nomenclátor y callejero
1. Callejero, entidades de población, secciones censales, códigos postales
2. Instituto de Estadística CAM
3. `https://hub.arcgis.com/datasets/crtm::nomecalles-nomenclator-y-callejero-de-la-comunidad-de-madrid` **[URL✔]**; `https://gestiona.comunidad.madrid/iestadis/gazeta/publicaciones/nomecallesno.htm`
4. Vía, portal, código postal, sección, coordenadas
5. Portal / sección
6. Shapefile/FeatureService (ArcGIS Hub)
7. Anual
8. Geocodificación y unión sección↔municipio↔CP.

### F5.4 Parques tecnológicos, científicos, polígonos y viveros
1. Inventario de parques científicos/tecnológicos (≈1.100 ha: Getafe, Leganés, Móstoles, Alcalá, Colmenar Viejo…), polígonos industriales, viveros
2. Comunidad de Madrid (Madrid Emprende / Innova), APTE, ayuntamientos
3. `https://www.comunidad.madrid/inversion/innova/espacios-innovacion` · `https://www.apte.org` **[URL de búsqueda; A VERIFICAR]**. En CKAN no hay datasets con “polígono/vivero/coworking” (0 resultados).
4. Nombre, municipio, superficie, empresas alojadas, servicios
5. Municipio / puntual (geocodificar)
6. Scraping; capa OSM `landuse=industrial/commercial` **[DESCARGA EN CURSO]**; Portal del Suelo (F2.6) cubre parte
7. Estático / ocasional
8. V: aglomeración tecnológica; R: polos periféricos.

### F5.5 OpenStreetMap vía Overpass — servicios auxiliares
1. POIs: coworking, guarderías, gimnasios, restauración, colegios/universidades, sanidad, transporte, oficinas, parques, uso de suelo
2. OpenStreetMap contributors (ODbL)
3. `https://overpass-api.de/api/interpreter` (área `ISO3166-2=ES-MD`) **[API✔]**; script `backend/pipeline/overpass_cam.py`; descargados hasta ahora: coworking (23 KB), guarderías (665 KB), gimnasios (487 KB) — el resto en curso (504 en consultas grandes) **[DESCARGADO parcial]**. Alternativa completa: `https://download.geofabrik.de/europe/spain/madrid-latest.osm.pbf` **[URL✔]**
4. tags (name, amenity/leisure/office, opening_hours…) + lat/lon (`out center`)
5. Coordenadas X/Y
6. REST JSON / PBF
7. Tiempo casi real
8. V: amenidades por trabajador; calidad desigual por municipio rural. Google Places queda descartado salvo presupuesto (API de pago).

---
## BLOQUE 6 — Conectividad, movilidad, transporte

### F6.1 CRTM — GTFS (Metro, Metro Ligero, Cercanías, EMT, urbanos, interurbanos)
1. GTFS estático de todos los modos
2. Consorcio Regional de Transportes de Madrid
3. Portal `https://data-crtm.opendata.arcgis.com/`; descarga por ítem `https://www.arcgis.com/sharing/rest/content/items/{id}/data` **[API✔][DESCARGADO]** `data/raw/crtm/{metro,metroligero,cercanias,emt,urbanos,interurbanos}.zip` (interurbanos 74 MB). Ojo: `cercanias.zip` pesa solo 6 KB → incompleto; usar Renfe/NAP (`nap.transportes.gob.es` da 401 sin cuenta)
4. stops (stop_id, nombre, lat, lon, zone_id), routes, trips, stop_times, **frequencies** (headway_secs), calendar, shapes
5. Parada (X/Y) → agregable a municipio por punto-en-polígono
6. GTFS (ZIP/CSV)
7. Actualización por temporada; EMT 2023-
8. V/R: densidad de paradas, frecuencias, tiempo a intercambiadores (con RAPTOR/OpenTripPlanner); C: coste de commuting.

### F6.2 CRTM — Redes de Metro/Metro Ligero (FeatureServer), aparcamientos disuasorios, zonas tarifarias, EDM2018
1. Estaciones/andenes/tramos, aparcamientos de disuasión, coronas tarifarias, zonificación de transporte (ZT84/208/1172/1259), Encuesta Domiciliaria de Movilidad 2018 (hogares, individuos, viajes, etapas)
2. CRTM
3. `https://data-crtm.opendata.arcgis.com/api/feed/dcat-us/1.1.json` (280 ítems) **[API✔]** guardado en `data/raw/crtm/dcat.json`; EDM2018 viajes **[DESCARGADO]** `edm2018_viajes.zip` (XLSX/diccionario, 23 MB; parece contener libro Excel)
4. Origen/destino por zona, motivo, modo, duración (EDM); corona tarifaria por municipio
5. Zona de transporte / municipio / estación
6. ArcGIS FeatureServer, SHP, CSV, XLSX
7. EDM: 2018; redes: continua
8. V/C: matriz origen-destino domicilio-trabajo y tiempos de viaje; corona tarifaria = coste del abono.

### F6.3 Red viaria de alta capacidad (M-30/M-40/M-50/A-1…A-6)
1. Red de carreteras, IMD de tráfico, velocidades
2. Ministerio de Transportes (Mapa de tráfico), CAM Carreteras, CNIG BTN/BCN
3. `https://mapas.transportes.gob.es` / `https://centrodedescargas.cnig.es` **[URL✔ CNIG][A VERIFICAR resto]**; alternativa: OSM `highway=motorway/trunk` (vía Overpass) 
4. Geometría de ejes, clase, IMD, velocidad máx.
5. Tramo (línea)
6. SHP/GeoJSON/CSV
7. Anual (IMD)
8. V/C: distancia/tiempo a M-30/M-40/M-50 y radiales por municipio.

### F6.4 Cobertura de banda ancha fija y móvil (FTTH, 5G)
1. Cobertura por tecnología (FTTH, HFC, FWA, 5G NSA/SA, 5G 3,5 GHz) y velocidad; serie desde 2013
2. Secretaría de Estado de Telecomunicaciones e Infraestructuras Digitales (digital.gob.es) / CNMC
3. `https://digital.gob.es/en/telecomunicaciones-infraestructuras-digitales/areas-interes/banda-ancha/informacion-cobertura` **[URL✔]**; mapas agregados `.../informacion-cobertura/mapas-cobertura-agregada` **[URL de búsqueda]**
4. % hogares con FTTH ≥ 100 Mbps/1 Gbps, % cobertura 5G, por municipio/entidad singular de población; visor a nivel de referencia catastral
5. Municipio / entidad de población / ref. catastral
6. Descarga CSV/Excel anual (enlaces exactos A VERIFICAR); visor web
7. Anual (informe 2024 publicado; más reciente A VERIFICAR)
8. V: requisito crítico de oficina (teletrabajo/híbrido); R: brecha digital rural.

---
## BLOQUE 7 — Calidad de vida y servicios

### F7.1 Sanidad — centros, servicios y establecimientos sanitarios (+ farmacias)
1. Registro de centros sanitarios (hospitales, centros de salud, clínicas) y oficinas de farmacia
2. Consejería de Sanidad
3. `https://datos.comunidad.madrid/catalogo/dataset/centros_servicios_establecimientos_sanitarios` · `.../oficinas_farmacia` **[DESCARGADO]**
4. centro_nro_registro, centro_tipo, dependencia funcional/patrimonial, oferta asistencial, municipio, dirección, CP, **localizacion_coordenada_x/y** (UTM), NIF
5. Coordenadas X/Y
6. CSV
7. Continua
8. V/R: acceso a hospitales/centros por municipio.

### F7.2 Educación — centros, alumnado, FP
1. Centros docentes, alumnos por tipo de enseñanza, infantil, conexión a Internet
2. Consejería de Educación
3. CKAN grupo Educación (217 datasets); p.ej. `alumnos_no_universitarios_general_por_tipo_y_ensenanza` **[DESCARGADO]**; directorio de centros georreferenciado: A VERIFICAR (OSM `colegios_univ` en curso)
4. Alumnos, centros, titularidad, ciclo
5. Municipio (centros: X/Y si existe directorio)
6. CSV
7. Anual
8. V/R: oferta educativa para familias (atracción de talento).

### F7.3 Deporte e instalaciones
1. Entidades deportivas (registro CAM) y equipamientos municipales de Madrid ciudad (543 en total: 71 centros + 472 básicas)
2. CAM (Registro de Entidades Deportivas); Ayto. Madrid
3. `https://datos.comunidad.madrid/catalogo/dataset/spacm_entidades_deportivas` **[DESCARGADO]** (TIPO_ENTIDAD, NUMERO, DENOMINACION, MUNICIPIO); `https://datos.madrid.es/dataset/200186-0-polideportivos` **[URL de búsqueda]**. El censo regional de instalaciones deportivas del CSD (2005) es PDF; no hay censo regional abierto reciente → usar OSM `leisure=sports_centre`
4. Nombre, tipo, municipio (+ coordenadas en Madrid ciudad)
5. Municipio / puntual (ciudad)
6. CSV/ZIP
7. Continua
8. V: calidad de vida (gimnasios/instalaciones por habitante).

### F7.4 Zonas verdes, aire, ruido, medio ambiente
1. Red de calidad del aire (estaciones), parques, riesgos
2. CAM / Ayto. Madrid / OSM
3. `calidad_aire_estaciones` **[DESCARGADO]**; OSM `parques` (en curso); Medio ambiente 89 datasets en CKAN
4. Estación, contaminante, coordenadas; superficie verde
5. Estación / puntual / polígono
6. CSV/JSON
7. Horaria-anual
8. V/R: calidad ambiental.

---
## GEOMETRÍAS Y CATÁLOGOS ESPACIALES (IDEM)

### F8.1 Secciones censales (CAM)
1. Secciones censales con superficie
2. Instituto de Estadística CAM
3. `https://datos.comunidad.madrid/catalogo/dataset/secciones_censales` **[DESCARGADO]** CSV + SHP (`data/raw/cam_geo/`)
4. seccion_codigo, distrito_codigo/nombre, municipio_codigo/nombre, superficie_km2 (+ geometría en SHP)
5. Sección censal
6. CSV, Shapefile
7. Anual
8. Base territorial para agregar todo por INE; densidad = población/superficie.

### F8.2 IDEM — Geoportal de la Comunidad de Madrid
1. Catálogo geográfico oficial (unidades administrativas, cartografía, planeamiento)
2. Comunidad de Madrid (IDEM)
3. `https://www.comunidad.madrid/geoportal/idem` · `https://www.madrid.org/cartografia/idem/` **[URL✔]**; servicios CSW/WMS/WMTS/WFS/ATOM (URLs concretas de WFS: A VERIFICAR en el catálogo)
4. Capas de unidades administrativas, usos del suelo, planeamiento, etc.
5. Municipio → puntual
6. WFS/WMS/ATOM/SHP
7. Variable
8. Límites, clasificación del suelo (urbano/urbanizable), base 3D.

### F8.3 CNIG — Centro de Descargas
1. MDT, BTN/BCN, límites, PNOA/LiDAR, SIOSE
2. IGN/CNIG
3. `https://centrodedescargas.cnig.es/CentroDescargas/index.jsp` **[URL✔]**
4. Altimetría, usos del suelo, hidrografía
5. Malla/hojas
6. Descarga ficheros (TIFF/SHP/LAZ)
7. Variable
8. Terreno para el 3D; cobertura de suelo (SIOSE).

### F8.4 Ayto. Madrid — Geoportal y datos abiertos
1. Distritos y barrios (shapefiles), callejero, equipamientos
2. Ayuntamiento de Madrid
3. `https://datos.madrid.es/api/3/action/package_search` **[API✔]**; `https://wpgeoportal.madrid.es` **[URL de búsqueda]**
4. Geometrías, equipamientos
5. Distrito/barrio/puntual
6. SHP/GeoJSON/CSV
7. Variable
8. Nivel intramunicipal de la capital.

---
## Catálogo CKAN completo (referencia transversal)
CKAN CAM: 2.263 datasets (Salud 303, Economía 299, Educación 217, Empleo 186, Sociedad y bienestar 153, Demografía 146, Legislación 108, Vivienda 98, Medio Rural 94, Medio ambiente 89, Transporte 86, Cultura 74, Sector público 58, Hacienda 51, Urbanismo 49, Comercio 28, Turismo 27, Ciencia y tec. 26, Seguridad 24, Energía 19, Industria 12, Deporte 8). Ayto. Madrid: 674. Ver `docs/fuentes/*.csv`.

## Huecos reales (sin dataset abierto verificado)
Renta y vacancia de oficinas · tipos IBI/IAE/ICIO unificados · lista oficial de municipios Pueblos con Vida · inventario único de polígonos/viveros/coworkings (solo OSM) · tiempos de viaje a intercambiadores (hay que calcularlos desde GTFS+viaria) · cobertura FTTH/5G descargable por municipio (hay que confirmar fichero) · ficheros SEPE por municipio (enlaces mensuales sin confirmar).
