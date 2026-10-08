# Pendientes — Datathon CAM

Lista viva de frentes abiertos. Se aborda poco a poco: al terminar un punto, márcalo `[x]`, añade la fecha y una línea con el resultado, y apunta en `ESTADO.md` cualquier hallazgo técnico reutilizable.

Prioridad: **P1** bloquea la entrega o invalida resultados · **P2** mejora clara · **P3** deseable.
Dependencias entre puntos: `→ requiere #N`.

Última revisión: 2026-10-08

---

## 0. Infraestructura (rápido, hacer primero)

- [x] **#1 P1 · Entorno Python dentro del proyecto.** El venv usado hasta ahora vive en la carpeta temporal de la sesión de Claude y puede desaparecer. Crear `.venv` en la raíz e instalar `requirements.txt` (ya generado con versiones exactas). Hecho cuando: `python backend/pipeline/auditoria_cpts.py` corre con `.venv`. · **Hecho 2026-10-07:** `.venv` en la raíz con `requirements.txt` (+ `interpret-core==0.7.8`); `auditoria_cpts.py` pasa con `.venv`. Si el Excel está abierto, la auditoría avisa y continúa.
- [x] **#2 P3 · Limpiar `backend/pipeline/`.** · **Hecho 2026-10-08:** logs en `backend/logs/` (fuera de git), `__pycache__` borrado.
- [x] **#42 P1 · Monorepo y repositorio público (2026-10-08).** Estructura `docs/` · `backend/` (`pipeline/`, `api/`) · `frontend/` (`dashboard/`, `app/`) · `infra/` · `data/` (`raw/`, `processed/`); rutas reescritas en scripts y documentos; `auditoria_cpts.py` y `preferencias.py` pasan. Git con licencia MIT, CI en `.github/workflows/ci.yml` (Windows: los PDF usan fuentes del sistema). Fuera de git: `data/raw/`, `data/processed/municipal/`, CSV de POIs/paradas con sección, plantilla Slidesgo e `Interfaz.pdf`.

## 1. Modelo — red bayesiana

- [ ] **#3 P1 · Monotonía en las CPT.** Hoy abaratar el coste puede *bajar* la viabilidad (Cercedilla −3,9 puntos en la simulación), porque la tabla del objetivo no es monótona (Dinamismo Medio 0,46 > Alto 0,28 con Especialización Media) y hay casillas con 4-5 municipios. Opciones: CPT ordinal parametrizada, isotonic sobre los conteos, o fusionar estados escasos. Validar con la misma CV de 5 particiones (acc 0,48 / log-loss 1,086 de referencia).
- [x] **#4 P1 · Acceso Ferroviario desconectado.** 2026-10-07 · Resuelto como hallazgo, sin cambiar la red. Con evidencia completa solo influyen los padres directos del objetivo, así que el transporte solo contaría como padre de Viabilidad. `backend/pipeline/experimento_transporte.py` (CV-5 × 5 repeticiones): ninguna métrica de transporte se asocia con la tasa neta (ρ entre −0,09 y +0,15; distancia a estación vs Distancia a Sol ρ = 0,86). Todas las estructuras con transporte empeoran: S0 actual acc 0,459 / ll 1,103; Viab ← Dinamismo+Transporte 0,375 / 1,128; Viab ← Especialización+Transporte 0,371 / 1,141; 3 padres con Transporte 0,448 / 1,291; 3 padres con Acceso Ferroviario 0,391 / 1,179. Conclusión: el transporte entra como preferencia o filtro del usuario (#38), no como causa aprendida.
- [ ] **#37 P1 · Calibración: el log-loss medio no supera a la uniforme.** Con 5 repeticiones de CV-5, la red actual da acc 0,459 ± 0,012 (mejor que azar) pero log-loss 1,103 ± 0,015, peor que la uniforme (1,099). El 1,086 citado en los anexos era una sola semilla favorable. Acciones: (a) ~~reportar media ± desviación~~ hecho 2026-10-07 en `RED_BAYESIANA.md`, `Aproximacion_tecnica_CAM.pdf` y `CLAUDE.md`; (b) probar ESS mayor (#7) y monotonía (#3), que suavizan probabilidades extremas; (c) valorar un target alternativo (#39).
- [ ] **#38 P2 · Transporte como preferencia o filtro del usuario** (avance 2026-10-07: utilidad y pesos implementados en `preferencias.py`; falta el filtro «imprescindible» y la integración en la app), fuera de la red, igual que las ayudas. Métricas ya calculadas en `data/processed/experimento_transporte_metricas.csv`: distancia del centroide a la estación ferroviaria más cercana (km) y paradas de bus por km². Filtro duro tipo "estación a ≤ X km" o peso explícito; mostrar en la ficha y como capa del mapa. Mejora futura: tiempo en transporte público a Atocha, Chamartín, Moncloa y Plaza de Castilla con el GTFS.
  - **Decisión 2026-10-07: el transporte queda como preferencia, no como nodo.** Análisis a igual distancia de Madrid (sin la capital): Cerca, con tren 0,66 %/año (n = 26) frente a sin tren 0,84 % (n = 34), p = 0,12; Media y Lejos, con tren 1,38 % frente a 0,83 % y 0,72 %, pero solo 7 municipios con tren (Alpedrete, Aranjuez, Cercedilla, Collado Mediano, Collado Villalba, Meco, Los Molinos), p = 0,15. Correlación parcial tren-tasa neta controlando distancia = −0,02. Cerca de Madrid el tren marca ciudades grandes y maduras (mediana 87.871 hab.: Móstoles, Alcalá, Leganés…) frente a municipios en expansión sin tren (mediana 9.802: Arroyomolinos, Navalcarnero…): es confusión por tipo de ciudad. La regla experta "a igual distancia, mejor con tren" es razonable pero no demostrable con n = 179. Opción descartada por ahora: meterla como prior experto en la red, reservada para el simulador de la Administración y siempre marcada como supuesto.
  - **Calibración de la importancia (propuesta 2026-10-07, aplicable también a ayudas #12 y coste #36).** Puntuación = (1 − w)·P(Alta) + w·u, con u ∈ [0, 1] la utilidad del atributo (tren: 1 si la estación está a ≤ 2 km, 0 a ≥ 15 km, lineal entre ambos) y w calibrado por dispersión: w = r·sd(P) / (sd(u) + r·sd(P)), con r = 0 (me da igual), 0,5 (poco importante) o 1 (muy importante). Con los 139 candidatos: sd(P) = 0,159, sd(u) = 0,398 → w = 0 / 0,166 / 0,285. Lectura para el usuario: "poco importante" = tener estación compensa hasta ~20 puntos de viabilidad; "muy importante" = hasta ~40 (w / (1 − w)). Añadir "Imprescindible" (filtro duro: estación a ≤ X km) y "No lo sé" (w = 0, marcado para volver a preguntar). Hallazgo: como la red solo da 9 niveles, cualquier w > 0 ya reordena el top (desempata); "poco" y "muy" difieren más abajo en el ranking. Validar r más adelante con usuarios (elección entre pares).
- [ ] **#39 P2 · Target alternativo.** Probar un objetivo que mida atracción de empleo, como el crecimiento de afiliados por ubicación del centro de trabajo, que sí podría depender del transporte. Comparar con la misma CV.
- [x] **#5 P1 · Empates en el ranking.** Con evidencia completa solo hay 9 puntuaciones posibles (2 padres × 3 estados). Implementar el GA²M (o puntuación continua) para desempatar y combinarlo con la BN de forma explicable. · **Hecho 2026-10-07:** `ga2m_desempate.py` (CV-5 × 5, Spearman con la tasa neta fuera de muestra): GA²M 0,398 ± 0,037 · GAM 0,396 · lineal 0,383 · media de rangos BN+GA²M 0,369 · lexicográfico 0,291 · BN sola 0,284. Precisión en el tercio superior: GA²M 0,517 · media de rangos 0,510 · BN 0,491 (azar 0,335). Implementado en `red_bayesiana_viabilidad.py` con `COMBINACION = "media_rangos"` (puntuación = media del percentil de la red y del GA²M, 0-100): 122 puntuaciones distintas entre 139 candidatos (antes 9). Salidas nuevas: `ga2m_contribuciones.csv` (contribución por término y municipio, base de #31) y `ga2m_importancias.csv`. Hallazgo: el GA²M solo ordena mejor que la red; la discretización en terciles pierde información. Decisión abierta (#40).
- [x] **#40 P1 · Decidir el papel de la red frente al GA²M.** El GA²M ordena mejor (Spearman 0,398 frente a 0,284). Opciones: (a) mantener la media de rangos (actual); (b) GA²M como puntuación principal y red para explicación, preferencias parciales y simulación `do()`; (c) volver a la red sola. Consecuencias: la puntuación ya no es 100 × P(Alta), así que hay que recalibrar los pesos de preferencias de #12/#38 (usaban sd(P) = 0,159) y actualizar diagrama, PDF de aproximación, `RED_BAYESIANA.md` y `CLAUDE.md` (#35). · **Hecho 2026-10-07: opción (b).** `COMBINACION = "ga2m"`: puntuación = percentil del GA²M entre candidatos (139 valores distintos). La red queda para explicar (P(Alta) y causas; aviso si discrepa del GA²M, p. ej. Torrejón de la Calzada 8.º con P(Alta) = 0,28), consultas con evidencia parcial y simulador `do()`. Preferencias recalibradas en `backend/pipeline/preferencias.py` con S' = (S + Σ a·u)/(1 + Σ a), a = r·sd(S)/sd(u); con sd(S) = 0,289: transporte w = 0,267 (poco) / 0,421 (muy) → compensa hasta 36 / 73 puntos; ayudas w = 0,291 / 0,450 → 41 / 82 puntos (tras corregir el padrón). `dist_ferro_km` ya está en el dataset. Actualizados diagrama de flujo, diagramas de estados, `Aproximacion_tecnica_CAM.pdf` (validación con media ± desviación) y `RED_BAYESIANA.md`.
- [ ] **#6 P2 · Intervalos de incertidumbre.** Bootstrap de los 179 municipios → reaprender CPT → intervalo del 90 % para cada puntuación y cada simulación.
- [ ] **#7 P2 · Sensibilidad.** ESS (1, 5, 10, 20) y discretización (terciles vs cuartiles vs umbrales de mercado). Documentar en `RED_BAYESIANA.md`.
- [ ] **#8 P2 · Sesgo de la contracción del target.** La contracción empírico-bayesiana lleva los municipios diminutos al tercil "Media". Valorar un estado "Sin datos suficientes" o ponderar por tamaño.
- [ ] **#9 P3 · Validación experta** del grafo y umbrales con técnicos de desarrollo local de la CAM.

## 2. Subvenciones e incentivos

Decisión tomada (2026-10-07): las ayudas **no** son nodo de la red. Por defecto son información visible (capa del mapa y ficha); solo afectan al ranking si el usuario lo pide (filtro duro o peso explícito fuera de la red).

- [x] **#10 P1 · Variable `Nivel_Ayudas` por elegibilidad normativa.** Bajo (≥ 20.000 hab., 37 municipios) / Medio (2.500-20.000, 72) / Alto (< 2.500, 70). Añadir a `construir_dataset_bn.py` y al dataset. · **Hecho 2026-10-07:** columnas `nivel_ayudas` (Bajo 37 · Medio 72 · Alto 70, tras corregir el padrón) y `nivel_ayudas_num` (0 / 0,5 / 1) en `dataset_bn_municipios.csv`; también en `bn_ranking_municipios.csv` como dato informativo. Pendiente afinar con listas oficiales (#11).
- [ ] **#11 P1 · Verificar listas oficiales** en BOCM/BOE: Plan de Reequilibrio Territorial, rebaja fiscal en municipios < 2.500 hab., Pueblos con Vida, grupos LEADER, ayudas estatales al reto demográfico. Afinar #10 con ellas. → requiere #10
- [ ] **#12 P2 · Filtro duro y peso opcional.** (avance 2026-10-07: peso implementado en `preferencias.py` con la calibración nueva; los w 0 / 0,15 / 0,30 de abajo quedan obsoletos; falta el filtro) Filtro "necesito ayudas" (excluye nivel Bajo) y puntuación combinada `100 × [(1 − w)·P(Alta) + w·nivel]`, con w = 0 / 0,15 / 0,30 según la respuesta del usuario (nada, algo o muy importante). Mostrar las dos partes por separado en la explicación. → requiere #10
- [ ] **#13 P2 · Convocatorias aplicables por perfil.** Clasificar las convocatorias BDNS vigentes (regionales, estatales y locales) por perfil de negocio: empleo, autónomos, digitalización, I+D, alquiler. Palabras clave primero, LLM después.
- [ ] **#14 P1 · Corregir los PDF.** `Fuentes_de_datos_CAM.pdf` y `Aproximacion_tecnica_CAM.pdf` presentan la BDNS como si alimentara el modelo. Reescribir para describir el uso real (#10-#13). → requiere #10
- [ ] **#36 P2 · Calculadora de coste operativo neto (€/año)**, fuera de la red. Para el perfil del usuario (m², empleados): alquiler estimado + IBI repercutido (valor catastral × tipo del municipio) + IAE (solo si factura > 1 M€) − ayudas a las que puede optar. Mostrar cada término en la ficha; usarla como filtro (presupuesto máximo) o como peso explícito. **No** fusionar en el nodo Coste Inmobiliario: ese nodo es coste residencial y actúa vía Dinamismo, y restar ayudas por elegibilidad metería la población en el nodo. Reconsiderar como nodo `Coste_Neto` solo si hay importes reales de ayudas y tipos impositivos por municipio, comparándolo por CV. → requiere #10, #25 (tipos IBI); alquiler de oficinas mejora con #27
- [ ] **#15 P3 · Revisar `fechaDesde` de la BDNS.** Las concesiones descargadas solo cubren 2022-2026 aunque se pidió desde 2019.

## 3. Simulador de políticas (perfil Administración)

- [ ] **#16 P2 · Módulo what-if con `do()`.** Fijar la palanca intervenida, re-predecir sus descendientes y mantener los no descendientes. Prototipo ya calculado (mediana +4,5 puntos al bajar el coste en 119 municipios). → requiere #3, #4, #6
- [ ] **#17 P2 · Catálogo política → palanca**, con la hipótesis visible y editable: ayuda al alquiler o bonificación del IBI → Coste; viveros y atracción de servicios → Especialización; nueva estación → Acceso Ferroviario (requiere #4).
- [ ] **#18 P3 · Efecto real de las subvenciones.** Cruzar concesiones BDNS con `din_emp` año a año (diferencias en diferencias). Hoy solo hay 24 municipios con concesiones locales: bajo potencial a corto plazo.

## 4. Datos pendientes

- [x] **#19 P1 · Recalcular los conteos OSM** con las 18 categorías ya descargadas (`osm_a_secciones.py`). Después reconstruir el dataset, regenerar el dashboard y republicarlo. Hoy `amenidades_osm` excluye bares, sanidad y deporte. · **Hecho 2026-10-07:** 153.517 POIs en 18 categorías (antes 65.322). `amenidades_osm` añade bares; nuevas `sanidad_osm` y `deporte_osm` (+ por 1.000 hab). Las columnas de la red no cambian (verificado). Dashboard republicado (versión 2) con 21 variables.
- [ ] **#20 P2 · Procesar Catastro BU** (179 ZIP GML descargados): m² construidos por uso (oficinas, comercial, industrial) por municipio. Candidato a sustituir el proxy residencial de Coste y base del 3D.
- [ ] **#21 P2 · Atlas de Distribución de Renta (INE)** por sección censal: ficheros de INEbase o paquete `ineAtlas`; la API Tempus es lenta y fragmentada.
- [ ] **#22 P2 · Cobertura FTTH/5G por municipio** (Ministerio para la Transformación Digital). Candidata a filtro duro de conectividad.
- [ ] **#23 P2 · Límites municipales simplificados (GeoJSON)** para el mapa: disolver `Seccionado_2019.shp` por municipio, o descargar de IDEM.
- [ ] **#24 P3 · GTFS de Cercanías completo** (Renfe). El del CRTM pesa 6 KB.
- [ ] **#25 P3 · Ordenanzas fiscales IBI/IAE/ICIO** de los 179 municipios (recopilación manual o scraping).
- [ ] **#26 P3 · SEPE mensual.** Baja prioridad: el CKAN de la CAM ya trae paro municipal.
- [ ] **#27 P3 · Fuentes privadas** (rentas de oficinas de consultoras, portales): solo si hay acceso o licencia.

## 5. Aplicación

- [ ] **#28 P2 · Backend FastAPI.** Endpoints: puntuación de los 179 municipios dada evidencia y filtros, explicación por municipio, simulación `do()`. Datos en Parquet en memoria. → requiere #5
- [ ] **#29 P2 · Esquema de salida estructurada del LLM** para el onboarding (filtros duros, evidencias blandas, variables inciertas) y su mapeo a los estados de los nodos.
- [ ] **#30 P2 · Preguntas por valor de la información:** elegir la pregunta que más reduce la entropía esperada del ranking entre candidatos.
- [ ] **#31 P2 · Descomposición XAI por municipio:** (avance: `data/processed/ga2m_contribuciones.csv` ya da la contribución de cada término del GA²M por municipio) contribución de cada evidencia y atributo (cambio en log-odds), más la parte de ayudas si se activa #12.
- [ ] **#32 P3 · Frontend:** React/TypeScript, MapLibre y Deck.gl, empaquetado con Tauri o Electron. → requiere #23, #28

## 6. Documentación y entregables

- [x] **#41 P1 · Entregables del datathon (2026-10-07).** En `docs/presentaciones/`:
  - `1_Descripcion_y_problema.pptx/.pdf` (13 diapositivas) y `3_Interfaz.pptx/.pdf` (10), sobre la plantilla de Slidesgo de la raíz del proyecto (`backend/pipeline/construir_presentaciones.py`; reutiliza portada, índice, diagramas de ciclo y cierre, y añade diapositivas en su layout TITLE_ONLY). La de interfaz usa las capturas de `Interfaz.pdf` y avisa de que sus cifras son ilustrativas.
  - `2_Fuentes_de_datos.pdf` (3 págs., sobrio, `backend/pipeline/generar_pdf_fuentes_cam.py`): fuentes oficiales de la Comunidad primero (8 de 8 variables del modelo llegan por canales de la Comunidad; el Instituto de Estadística es el canal de 6), origen de cada variable, otras públicas, privadas y criterios.
  - PDF exportados con PowerPoint por COM: `powershell -File infra/scripts/pptx_a_pdf.ps1 <pptx> <pdf>`. Se instalaron Poppins y Didact Gothic solo para el usuario (sin admin) para que se incrusten.
  - **Revisión 2026-10-07 para la fase de presentación de ideas:** la presentación 1 (11 diapositivas) quita validación, ficha real de Buitrago, indicador de reequilibrio y límites; añade «Cómo razona el sistema» y dos ejemplos de entrada y salida con datos simulados (empresa y administración), marcados como tales. La presentación 3 (9 diapositivas) quita «real frente a ilustrativo» y los indicadores de estado. Las versiones con datos reales del modelo siguen en `docs/informe/Aproximacion_tecnica_CAM.pdf`.
  - Añadida diapositiva «Explicable de forma nativa» (GA²M aditivo con aportaciones simuladas + red bayesiana causal, frente a caja negra con explicación a posteriori); el GA²M vuelve a aparecer con su nombre en la solución y en «Cómo razona». Presentación 1: 12 diapositivas.
  - Nombre del proyecto: **Madrid 179** (portada de las dos presentaciones, cierre y cabecera/pie del documento de fuentes).
  - El artifact de Slides anterior (https://claude.ai/artifact/HGbA9mjGd4HFkbcwY3BCtW) queda obsoleto.

- [ ] **#33 P2 · Actualizar `docs/informe/INFORME.md`.** Está anterior a la red bayesiana.
- [ ] **#34 P3 · Consolidar `docs/fuentes/CATALOGO_FUENTES.md`** con `docs/informe/FICHAS_FUENTES.md`. El primero usa los bloques antiguos, extrapolados de un prompt cortado.
- [ ] **#35 P2 · Regenerar anexos** (diagrama, `Calculo_CPTs_CAM.pdf`, `Aproximacion_tecnica_CAM.pdf`) cada vez que cambie la red (#3, #4). Los scripts ya lo hacen; solo hay que ejecutarlos.

---

## Hechos

- 2026-10-07 · **Error corregido: población duplicada.** `padron_por_sexo` trae Hombres, Mujeres y Total por municipio y `construir_dataset_bn.py` sumaba las tres (CAM 14,3 M en vez de 7,14 M). Ahora filtra `Sexo == "Total"` con un assert. Modelos y ranking idénticos (no usan la población); cambian `poblacion`, las variables por 1.000 hab., la densidad y `nivel_ayudas`. Corregidos PDF de aproximación, dashboard, diagrama y estas notas. Cifras buenas: CAM 7.137.031 hab.; capital 3.506.730 (49,1 %), 56,3 % de las unidades productivas y 64,3 % del empleo afiliado; 142 municipios < 20.000 hab. (8,8 % de la población) y 70 < 2.500.
- 2026-10-07 · `Aproximacion_tecnica_CAM.pdf` ampliado a 7 páginas: tabla de origen de cada variable (fuente primaria, publicador, conjunto, año), UX de Administración (ámbito, diagnóstico, simulador, informe), ejemplo de ficha diagnóstica (Buitrago del Lozoya), sección «Valor para la Administración» con indicador de reequilibrio (corregido: top 20 con 13 de 20 municipios < 20.000 hab. sin preferencias; 20 de 20 con ayudas «poco importantes») y diagrama de estados a 300 ppp. svglib descartado: se cuelga al cargar el SVG en Windows.
- 2026-10-07 · Hecho #40 (opción b: el GA²M puntúa, la red explica).
- 2026-10-07 · Hechos #1, #19, #10 y #5 (ver cada punto). Nuevo #40.
- 2026-10-07 · Creado este fichero, `CLAUDE.md` y `requirements.txt`. Descarga OSM completada (18 categorías, incluidas sanidad, deporte y viaria de alta capacidad).
