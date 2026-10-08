# Red bayesiana de viabilidad empresarial municipal (CAM)

Scripts: `backend/pipeline/construir_dataset_bn.py` → `data/processed/dataset_bn_municipios.csv` (179 municipios) → `backend/pipeline/red_bayesiana_viabilidad.py [--modo A|B]`.
Salidas: `data/processed/bn_umbrales.json`, `bn_dataset_discretizado.csv`, `bn_cpts.txt`, `bn_ranking_municipios.csv`. Probado con pgmpy 1.1.2.

## Target: `Viabilidad_Empresarial`
Fuente: `din_emp` (IECM, Dinámica Empresarial base 2015: unidades productivas que nacen, mueren, entran y salen), agregado 2020-2024:

  tasa_neta = (nacen + entran − mueren − salen) / Σ unidades al inicio de cada año

Con contracción empírico-bayesiana hacia la media regional (r̄ = 0,72 % anual; k = 1.965 unidades-año, la mediana): `(neto + k·r̄)/(Σinicio + k)`. Sin ella, pueblos con 26 unidades-año salen en los extremos por puro ruido. Spearman entre la tasa bruta y la contraída = 0,91. Efecto secundario: los municipios muy pequeños tienden al tercil "Media".
No uso la supervivencia a 3-5 años porque no hay cohortes por municipio; la mortalidad anual (`tasa_mortalidad_emp`) está en el dataset por si se quiere.

## Variables
| Variable | Tipo | Estados | Columna y criterio (cortes reales, n=179) |
|---|---|---|---|
| Excluir Madrid capital | Filtro duro | — | ine5 ≠ 28079 (objetivo: descongestionar) |
| Oferta terciaria mínima | Filtro duro | — | `uu_oficinas` ≥ 1 (Catastro). Quedan 139 de 179 municipios |
| Elegibilidad despoblación | Filtro opcional | — | población < 20.000 (se activa según las preferencias del negocio) |
| Distancia_Madrid | Nodo BN | Cerca/Media/Lejos | `dist_sol_km` (centroide a la Puerta del Sol); terciles 31,78 / 45,18 km |
| Talento | Nodo BN | Bajo/Medio/Alto | `pct_estudios_superiores` (2024); terciles 30,64 / 39,49 % |
| Acceso_Ferroviario | Nodo BN | No/Si | `paradas_ferro` (Metro, Metro Ligero y Cercanías del GTFS del CRTM) > 0 → 34 Sí / 145 No |
| Coste_Inmobiliario | Nodo BN | Bajo/Medio/Alto | `vc_residencial_por_uu` (valor catastral residencial por unidad urbana, 2026, miles €); terciles 69,78 / 95,65 |
| Renta | Nodo BN | Baja/Media/Alta | `rdb_per_capita` (2023); terciles 17.065 / 19.992 € |
| Especializacion_Servicios | Nodo BN | Baja/Media/Alta | `pct_up_servicios_prof` (% de unidades productivas en "Información y servicios profesionales", 2025); terciles 12,74 / 18,25 % |
| Dinamismo_Demografico | Nodo BN | Bajo/Medio/Alto | `crec_pob_5a` (padrón 2020→2025); terciles 6,76 / 12,91 % |
| Viabilidad_Empresarial | Nodo objetivo | Baja/Media/Alta | `tasa_neta_emp`; terciles 0,60 / 0,98 % anual |

Descartadas por colinealidad o señal nula frente al target: paro (ρ = −0,70 con la renta), paradas por cada 1.000 habitantes (premian a los pueblos pequeños con muchas paradas interurbanas), amenidades OSM por cada 1.000 habitantes (ρ ≈ 0 con el target) y densidad (ρ = −0,86 con la distancia).

## DAG (máx. 2 padres)
```
edges = [("Distancia_Madrid","Acceso_Ferroviario"), ("Distancia_Madrid","Coste_Inmobiliario"), ("Talento","Coste_Inmobiliario"),
         ("Talento","Renta"), ("Talento","Especializacion_Servicios"), ("Distancia_Madrid","Especializacion_Servicios"),
         ("Distancia_Madrid","Dinamismo_Demografico"), ("Coste_Inmobiliario","Dinamismo_Demografico"),
         ("Dinamismo_Demografico","Viabilidad_Empresarial"), ("Especializacion_Servicios","Viabilidad_Empresarial")]
```
Los padres del target son las dos variables con más asociación y casi independientes entre sí (ρ = −0,16).

## Elección de la opción A (BDeu, ESS = 10)
- Hay cobertura completa (179/179 sin nulos), y cada celda de la CPT del target tiene entre 11 y 25 municipios.
- Validación cruzada de 5 particiones prediciendo Viabilidad:

| Opción | Accuracy | Log-loss |
|---|---|---|
| A | 0,480 | 1,086 |
| B (utilidad ponderada) | 0,469 | 1,625 |
| Referencia | 0,333 (azar) | 1,099 (uniforme) |

- **La señal es débil:** A apenas mejora la log-loss de la distribución uniforme. B ordena casi igual, pero está mal calibrada (sobreconfiada).

## Limitaciones
- Con la evidencia completa, la probabilidad del target depende solo de sus 2 padres: el ranking tiene 9 niveles de probabilidad y muchos empates. Para desempatar hacen falta GA²M o la puntuación continua.
- Renta, Acceso_Ferroviario y Talento solo influyen a través de evidencia parcial; es el uso previsto para las preferencias de negocio: fijar solo lo que pide la empresa.
- El dataset no tiene cobertura de fibra ni precio de oficinas; Coste_Inmobiliario es un proxy residencial.

## Actualización 2026-10-07 · El GA²M puntúa, la red explica

- **Validación corregida** (CV-5 repetida 5 veces): la red acierta el 45,9 % ± 1,2 (azar 33,3 %), pero su log-loss medio es 1,103 ± 0,015, ligeramente peor que la uniforme (1,099). El 1,086 de arriba salió de una sola partición favorable. Sus probabilidades no se presentan como probabilidad literal de éxito.
- **Ranking:** un GA²M (`ExplainableBoostingRegressor` de InterpretML) sobre las mismas 7 variables continuas ordena mejor. Spearman fuera de muestra con la tasa neta: GA²M 0,398 · lineal 0,383 · media de rangos 0,369 · red 0,284. Precisión en el tercio superior: 51,7 % frente a 49,1 % (azar 33,5 %). Ver `backend/pipeline/ga2m_desempate.py` y `data/processed/ga2m_cv.csv`.
- **Decisión (PENDIENTES #40, opción b):** puntuación = percentil del GA²M entre candidatos (0-100), sin empates. La red se mantiene para explicar, para consultas con evidencia parcial y para el simulador `do()`. `bn_ranking_municipios.csv` incluye ambas cosas: `puntuacion` y `P_Alta`.
- **Preferencias del usuario** (transporte, ayudas): `backend/pipeline/preferencias.py`, puntuación final (S + Σ a·u)/(1 + Σ a) con pesos calibrados por dispersión.
- **Transporte:** sin señal sobre el objetivo, ni a igual distancia de Madrid (`experimento_transporte.py`); entra como preferencia (`dist_ferro_km`), no como nodo.
- **Explicación por municipio:** `data/processed/ga2m_contribuciones.csv` (contribución exacta de cada término del GA²M) y `ga2m_importancias.csv`.
