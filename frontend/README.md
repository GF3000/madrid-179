# Frontend

## `prototipo/`

Interfaz mínima, sin mapa, para probar el modelo: HTML, CSS y JavaScript sin dependencias ni compilación. La sirve la propia API en http://localhost:8000 (ver `infra/scripts/dev.ps1`), así que no hay que arrancar nada más.

- **Ranking:** preferencias (transporte, ayudas), filtros «imprescindible» y puntuación desglosada (modelo + preferencias).
- **Ficha:** al pulsar un municipio, aportaciones del GA²M, probabilidades de la red, padres de la viabilidad y aviso si los dos modelos discrepan. Enlace directo: `/prototipo/#28149`.
- **Consulta a la red:** evidencia parcial (p. ej. talento alto y lejos de Madrid) frente a la probabilidad a priori.

Solo habla con la API (`/api/v1`), igual que lo hará la app definitiva: prueba el contrato, no solo el modelo.

## `dashboard/`

`dashboard_template.html` es la plantilla del dashboard de correlaciones. `backend/pipeline/exportar_datos_dashboard.py` genera `data/processed/dashboard_data.json`; el JSON se inyecta en el marcador `__DATA__` y el resultado se guarda como `docs/informe/dashboard_correlaciones.html`.

## `app/`

Aplicación pendiente (#32): React y TypeScript, MapLibre y Deck.gl para el mapa 3D, empaquetada con Tauri o Electron. Usará la misma API que el prototipo. Depende también de los límites municipales en GeoJSON (#23).
