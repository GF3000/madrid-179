# Infraestructura

| Fichero | Uso |
|---|---|
| `scripts/dev.ps1` | Arranque local en un comando: prepara el entorno si falta, entrena el modelo si falta y lanza API + prototipo en http://localhost:8000 |
| `scripts/setup_venv.ps1` | Crea `.venv` en la raíz, instala `backend/requirements.txt` y el paquete `madrid179` (editable) |
| `scripts/pptx_a_pdf.ps1` | Exporta un `.pptx` a PDF con PowerPoint (COM). Requiere las fuentes Poppins y Didact Gothic |
| `../.github/workflows/ci.yml` | CI: instala, entrena el artefacto, pasa los tests y la auditoría de las CPT |
| `Dockerfile` (+ `Dockerfile.dockerignore`) | Imagen de producción: compila la app React, entrena el modelo y pasa los tests **dentro del build** (Linux), y sirve API + app + prototipo con uvicorn en `$PORT` |
| `../.github/workflows/deploy.yml` | CD: cuando la CI de un push a `main` termina en verde, construye la imagen, la sube a Artifact Registry y la despliega en Cloud Run (también a mano: `gh workflow run deploy.yml --ref main`) |
| `cloudrun/configurar_gcp.sh` | Configuración **única** de GCP y GitHub para el CD (idempotente) |

Los scripts funcionan con Windows PowerShell 5.1 y PowerShell 7 (guardados con BOM para que 5.1 lea bien las tildes).

## Despliegue continuo en Cloud Run (#45)

Un solo contenedor (API + app en el mismo origen, sin CORS) en Cloud Run, región `europe-southwest1` (Madrid), escala a cero.

**Probar la imagen en local** (Docker Desktop):
```bash
docker build -f infra/Dockerfile --build-arg COMMIT=$(git rev-parse --short HEAD) -t madrid179 .
docker run --rm -p 8080:8080 madrid179                     # http://localhost:8080 (sin asistente)
# con asistente: añadir -e DEEPSEEK_API_KEY=<clave> (--env-file no admite "CLAVE = valor" con espacios)
```

**Configuración única** (Git Bash, con `gcloud` y `gh` autenticados; el proyecto necesita facturación activa):
```bash
bash infra/cloudrun/configurar_gcp.sh <PROJECT_ID>        # región y servicio opcionales: [REGION] [SERVICIO]
```
Crea:
- las APIs, el repositorio de Artifact Registry `madrid179` y dos cuentas de servicio (`madrid179-deploy` para desplegar y `madrid179-run` como identidad del servicio);
- el secreto `deepseek-api-key` en Secret Manager, leído de `.env` sin mostrarlo;
- la Workload Identity Federation, que solo admite este repositorio y la rama `main`, de modo que GitHub no guarda ninguna clave;
- las variables del repositorio (`GCP_PROJECT_ID`, `GCP_REGION`, `CLOUD_RUN_SERVICE`, `GCP_DEPLOY_SA`, `GCP_RUNTIME_SA`, `GCP_WIF_PROVIDER`).

**Recursos del servicio:** 1 vCPU, 1 GiB, 0-3 instancias, acceso público. Para la demo ante el jurado conviene evitar el arranque en frío: `gcloud run services update madrid179 --region europe-southwest1 --min-instances 1` (y volver a 0 después).

**URL personalizada sin dominio propio (Firebase Hosting):** `infra/firebase/` reenvía todo el tráfico de `https://madrid179.web.app` al servicio de Cloud Run. Se despliega una sola vez; las revisiones nuevas de Cloud Run se sirven sin tocarlo:
```bash
cd infra/firebase && firebase deploy --only hosting --project madrid179
```

**Cambiar la clave del asistente:** `printf '%s' "<clave>" | gcloud secrets versions add deepseek-api-key --data-file=-` y volver a desplegar.
