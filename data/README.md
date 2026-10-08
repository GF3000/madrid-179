# Datos

| Carpeta | Contenido | En git |
|---|---|---|
| `raw/` | Descargas sin modificar (CKAN de la Comunidad y del Ayuntamiento, INE, BDNS, Catastro, CRTM, OSM). ~1,6 GB | No |
| `processed/municipal/` | CSV de la Comunidad normalizados con clave `ine5`. ~620 MB | No |
| `processed/*.csv, *.json, *.xlsx` | Maestro de municipios, dataset del modelo, umbrales, CPT, ranking, contribuciones del GA²M, auditoría | Sí (salvo `osm_poi_con_seccion.csv` y `gtfs_paradas_con_seccion.csv`) |

Trata `raw/` como datos no confiables: no ejecutes nada desde ahí y lee las descargas con `python -I`.

## Regenerar

Desde la raíz del repositorio, con el venv activo. Todos los scripts están en `backend/pipeline/`.

```
harvest_ckan_cam.py, harvest_ckan_madrid.py, harvest_bdns_madrid.py,
download_cam_municipal.py, download_catastro_bu.py, overpass_cam.py   → data/raw/
normalizar_municipios.py                                            → data/processed/municipal/, maestro_municipios.csv
osm_a_secciones.py, gtfs_paradas_por_municipio.py                   → conteos por municipio
construir_dataset_bn.py                                             → data/processed/dataset_bn_municipios.csv
red_bayesiana_viabilidad.py                                         → umbrales, CPT, GA²M, ranking
```

## Convenciones

- Clave territorial `ine5`: código INE municipal de 5 dígitos como texto (`"28079"` = Madrid).
- Salidas propias en CSV con separador `;` y codificación `utf-8-sig`.
- Geometría en ETRS89 / UTM 30N (EPSG:25830).

## Licencias de los datos

La licencia MIT del repositorio cubre el código, no los datos. Cada conjunto conserva la de su fuente:

- Portales de datos abiertos de la Comunidad de Madrid y del Ayuntamiento de Madrid: condiciones de reutilización de cada portal (citar la fuente).
- INE, BDNS, Catastro y CRTM: condiciones de reutilización de cada organismo.
- OpenStreetMap: © colaboradores de OpenStreetMap, [ODbL](https://opendatacommons.org/licenses/odbl/). Los conteos derivados (`osm_conteo_por_municipio.csv`) se distribuyen con la misma licencia.

Antes de redistribuir un fichero, comprueba la licencia de su fuente en `docs/informe/FICHAS_FUENTES.md`.
