# Frontend

## `prototipo/`

Interfaz mínima, sin mapa, para probar el modelo: HTML, CSS y JavaScript sin dependencias ni compilación. La sirve la propia API en http://localhost:8000/prototipo/ (en la raíz si la app no está compilada).

- **Ranking:** preferencias (transporte, ayudas), filtros «imprescindible» y puntuación desglosada (modelo + preferencias).
- **Ficha:** al pulsar un municipio, aportaciones del GA²M, probabilidades de la red, padres de la viabilidad y aviso si los dos modelos discrepan. Enlace directo: `/prototipo/#28149`.
- **Consulta a la red:** evidencia parcial (p. ej. talento alto y lejos de Madrid) frente a la probabilidad a priori.

Solo habla con la API (`/api/v1`), igual que lo hará la app definitiva: prueba el contrato, no solo el modelo.

## `dashboard/`

`dashboard_template.html` es la plantilla del dashboard de correlaciones. `backend/pipeline/exportar_datos_dashboard.py` genera `data/processed/dashboard_data.json`; el JSON se inyecta en el marcador `__DATA__` y el resultado se guarda como `docs/informe/dashboard_correlaciones.html`.

## `app/`

App de escritorio con mapa 3D (React + TypeScript, MapLibre y deck.gl), servida por la API en http://localhost:8000 cuando está compilada (`infra/scripts/dev.ps1` la compila si hace falta). Muestra grupos y razones en lugar de cifras del modelo. Detalles, arranque y criterios de diseño en [`app/README.md`](app/README.md). Pendiente: empaquetado de escritorio (Tauri o Electron) y simulador de la Administración.
