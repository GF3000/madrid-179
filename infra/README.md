# Infraestructura

| Fichero | Uso |
|---|---|
| `scripts/setup_venv.ps1` | Crea `.venv` en la raíz e instala `backend/requirements.txt` |
| `scripts/pptx_a_pdf.ps1` | Exporta un `.pptx` a PDF con PowerPoint (COM). Requiere las fuentes Poppins y Didact Gothic |
| `../.github/workflows/ci.yml` | CI: instala dependencias, compila el pipeline y pasa la auditoría de las CPT |

Pendiente: contenedor de la API (#28) y despliegue del frontend (#32).
