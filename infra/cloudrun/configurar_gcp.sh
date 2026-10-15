#!/usr/bin/env bash
# Configuración ÚNICA de Google Cloud y GitHub para el despliegue continuo de main en Cloud Run
# (.github/workflows/deploy.yml). Idempotente: se puede relanzar; lo que ya existe se deja como está.
#
# Requisitos: gcloud autenticado con permisos de propietario en el proyecto, facturación activa,
#             gh autenticado con permisos de administración en el repositorio.
# Uso (Git Bash, desde la raíz del repo):
#   bash infra/cloudrun/configurar_gcp.sh <PROJECT_ID> [REGION] [SERVICIO]
# La clave del asistente se lee de DEEPSEEK_API_KEY en .env (o del entorno) y se guarda en Secret Manager
# sin mostrarla. Si no hay clave, el secreto queda en blanco (Secret Manager no admite vacíos) y la app oculta el asistente.
set -euo pipefail

PROYECTO="${1:?Uso: configurar_gcp.sh <PROJECT_ID> [REGION] [SERVICIO]}"
REGION="${2:-europe-southwest1}"          # Madrid
SERVICIO="${3:-madrid179}"
REPO_GH="$(gh repo view --json nameWithOwner -q .nameWithOwner)"   # p. ej. GF3000/madrid-179
POOL="github"; PROVEEDOR="github"
SA_DEPLOY="madrid179-deploy@${PROYECTO}.iam.gserviceaccount.com"
SA_RUN="madrid179-run@${PROYECTO}.iam.gserviceaccount.com"
SECRETO="deepseek-api-key"

gc() { gcloud --project "$PROYECTO" --quiet "$@"; }
existe() { "$@" >/dev/null 2>&1; }

echo "== Proyecto $PROYECTO · región $REGION · servicio $SERVICIO · repositorio $REPO_GH"
NUM="$(gcloud projects describe "$PROYECTO" --format='value(projectNumber)')"

echo "== APIs"
gc services enable run.googleapis.com artifactregistry.googleapis.com iamcredentials.googleapis.com \
  secretmanager.googleapis.com sts.googleapis.com

echo "== Artifact Registry (imágenes)"
existe gc artifacts repositories describe madrid179 --location "$REGION" ||
  gc artifacts repositories create madrid179 --repository-format docker --location "$REGION" \
    --description "Imágenes de Madrid 179"

echo "== Cuentas de servicio"
existe gc iam service-accounts describe "$SA_DEPLOY" ||
  gc iam service-accounts create madrid179-deploy --display-name "Madrid 179: despliegue desde GitHub Actions"
existe gc iam service-accounts describe "$SA_RUN" ||
  gc iam service-accounts create madrid179-run --display-name "Madrid 179: identidad del servicio Cloud Run"

for ROL in roles/run.admin roles/artifactregistry.writer; do
  gc projects add-iam-policy-binding "$PROYECTO" --member "serviceAccount:$SA_DEPLOY" --role "$ROL" \
    --condition None >/dev/null
done
# el despliegue actúa en nombre de la cuenta de ejecución
gc iam service-accounts add-iam-policy-binding "$SA_RUN" --member "serviceAccount:$SA_DEPLOY" \
  --role roles/iam.serviceAccountUser >/dev/null

echo "== Secreto del asistente (Secret Manager)"
CLAVE="${DEEPSEEK_API_KEY:-}"
if [ -z "$CLAVE" ] && [ -f .env ]; then
  # admite "CLAVE=valor" y "CLAVE = valor", con o sin comillas, como python-dotenv
  CLAVE="$(grep -E '^DEEPSEEK_API_KEY *=' .env | head -1 | cut -d= -f2- | tr -d "\r\"' " || true)"
fi
existe gc secrets describe "$SECRETO" || gc secrets create "$SECRETO" --replication-policy automatic
if [ -n "$CLAVE" ]; then
  printf '%s' "$CLAVE" | gc secrets versions add "$SECRETO" --data-file=- >/dev/null
  echo "   clave guardada (no se muestra)"
elif ! existe gc secrets versions access latest --secret "$SECRETO"; then
  printf ' ' | gc secrets versions add "$SECRETO" --data-file=- >/dev/null
  echo "   sin clave: secreto en blanco (un espacio), el asistente quedará oculto"
fi
gc secrets add-iam-policy-binding "$SECRETO" --member "serviceAccount:$SA_RUN" \
  --role roles/secretmanager.secretAccessor >/dev/null

echo "== Workload Identity Federation (GitHub → GCP sin claves)"
existe gc iam workload-identity-pools describe "$POOL" --location global ||
  gc iam workload-identity-pools create "$POOL" --location global --display-name "GitHub Actions"
existe gc iam workload-identity-pools providers describe "$PROVEEDOR" --location global --workload-identity-pool "$POOL" ||
  gc iam workload-identity-pools providers create-oidc "$PROVEEDOR" --location global \
    --workload-identity-pool "$POOL" --display-name "GitHub" \
    --issuer-uri "https://token.actions.githubusercontent.com" \
    --attribute-mapping "google.subject=assertion.sub,attribute.repository=assertion.repository,attribute.ref=assertion.ref" \
    --attribute-condition "assertion.repository == '${REPO_GH}' && assertion.ref == 'refs/heads/main'"
PRINCIPAL="principalSet://iam.googleapis.com/projects/${NUM}/locations/global/workloadIdentityPools/${POOL}/attribute.repository/${REPO_GH}"
gc iam service-accounts add-iam-policy-binding "$SA_DEPLOY" --member "$PRINCIPAL" \
  --role roles/iam.workloadIdentityUser >/dev/null

echo "== Variables del repositorio en GitHub (no son secretos)"
gh variable set GCP_PROJECT_ID   --body "$PROYECTO"
gh variable set GCP_REGION       --body "$REGION"
gh variable set CLOUD_RUN_SERVICE --body "$SERVICIO"
gh variable set GCP_DEPLOY_SA    --body "$SA_DEPLOY"
gh variable set GCP_RUNTIME_SA   --body "$SA_RUN"
gh variable set GCP_WIF_PROVIDER --body "projects/${NUM}/locations/global/workloadIdentityPools/${POOL}/providers/${PROVEEDOR}"

echo "== Listo. El próximo push a main con la CI en verde despliega; o a mano: gh workflow run deploy.yml --ref main"
