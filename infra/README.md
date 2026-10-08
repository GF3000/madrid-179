# Infraestructura

| Fichero | Uso |
|---|---|
| `scripts/dev.ps1` | Arranque local en un comando: prepara el entorno si falta, entrena el modelo si falta y lanza API + prototipo en http://localhost:8000 |
| `scripts/setup_venv.ps1` | Crea `.venv` en la raíz, instala `backend/requirements.txt` y el paquete `madrid179` (editable) |
| `scripts/pptx_a_pdf.ps1` | Exporta un `.pptx` a PDF con PowerPoint (COM). Requiere las fuentes Poppins y Didact Gothic |
| `../.github/workflows/ci.yml` | CI: instala, entrena el artefacto, pasa los tests y la auditoría de las CPT |

Los scripts funcionan con Windows PowerShell 5.1 y PowerShell 7 (guardados con BOM para que 5.1 lea bien las tildes).

Pendiente: contenedor de la API y despliegue del frontend (#32).
