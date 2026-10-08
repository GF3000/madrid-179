# Frontend

## `dashboard/`

`dashboard_template.html` es la plantilla del dashboard de correlaciones. `backend/pipeline/exportar_datos_dashboard.py` genera `data/processed/dashboard_data.json`; el JSON se inyecta en el marcador `__DATA__` y el resultado se guarda como `docs/informe/dashboard_correlaciones.html`.

## `app/`

Aplicación pendiente (#32): React y TypeScript, MapLibre y Deck.gl para el mapa 3D, empaquetada con Tauri o Electron. Depende de la API (#28) y de los límites municipales en GeoJSON (#23).
