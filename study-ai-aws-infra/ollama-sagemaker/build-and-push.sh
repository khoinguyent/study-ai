#!/usr/bin/env bash
set -euo pipefail

AWS_REGION="${AWS_REGION:-ap-southeast-1}"
AWS_ACCOUNT_ID="${AWS_ACCOUNT_ID:-}"
ECR_REPOSITORY_NAME="${ECR_REPOSITORY_NAME:-ollama-inference}"
IMAGE_TAG="${IMAGE_TAG:-sm-compat-v2}"  # use a distinct tag for SageMaker

log() { echo -e "\033[32m[INFO]\033[0m $*"; }
err() { echo -e "\033[31m[ERR]\033[0m  $*" >&2; }

# 1) Prereqs
command -v aws >/dev/null || { err "aws CLI missing"; exit 1; }
command -v docker >/dev/null || { err "docker missing"; exit 1; }
docker info >/dev/null || { err "docker daemon not running"; exit 1; }
aws sts get-caller-identity >/dev/null || { err "aws credentials not configured"; exit 1; }

# 2) Account id
if [[ -z "${AWS_ACCOUNT_ID}" ]]; then
  AWS_ACCOUNT_ID="$(aws sts get-caller-identity --query Account --output text)"
fi
ECR_URI="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPOSITORY_NAME}:${IMAGE_TAG}"

# 3) Ensure repo
aws ecr describe-repositories --repository-names "${ECR_REPOSITORY_NAME}" --region "${AWS_REGION}" >/dev/null 2>&1 \
  || aws ecr create-repository --repository-name "${ECR_REPOSITORY_NAME}" --region "${AWS_REGION}" \
       --image-scanning-configuration scanOnPush=true --encryption-configuration encryptionType=AES256 >/dev/null

# 4) Login
aws ecr get-login-password --region "${AWS_REGION}" \
| docker login --username AWS --password-stdin "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"

# 5) Build single-arch (amd64) and load to local Docker daemon
# IMPORTANT: Avoid buildx --push (defaults to OCI). Use --load + docker push to force Docker v2 schema 2.
log "Building linux/amd64 image (Docker v2 Schema 2) ..."
docker buildx create --use --name sm-builder >/dev/null 2>&1 || true
docker buildx build --platform linux/amd64 -t "${ECR_URI}" --load .

# 6) Check if skopeo is available for schema conversion
if command -v skopeo >/dev/null; then
  log "Using skopeo to ensure Docker v2 schema2..."
  PASS=$(aws ecr get-login-password --region "${AWS_REGION}")
  skopeo copy --format v2s2 \
    docker-daemon:"${ECR_URI}" \
    docker://"${ECR_URI}" \
    --dest-creds AWS:"${PASS}"
else
  log "Skopeo not available, pushing with classic docker..."
  docker push "${ECR_URI}"
fi

# 7) Verify media type is Docker v2 schema2 (NOT OCI index)
log "Verifying image manifest type..."
MEDIATYPE="$(aws ecr batch-get-image \
  --region "${AWS_REGION}" \
  --repository-name "${ECR_REPOSITORY_NAME}" \
  --image-ids imageTag="${IMAGE_TAG}" \
  --query 'images[0].imageManifestMediaType' --output text || true)"

if [[ "${MEDIATYPE}" != "application/vnd.docker.distribution.manifest.v2+json" ]]; then
  err "ECR tag is not Docker v2 schema2. Got: '${MEDIATYPE:-<none>}'"
  err "SageMaker rejects OCI manifest lists. This usually happens when using buildx --push."
  err "Fix by ensuring you use --load + docker push (not buildx --push)."
  err "For guaranteed v2 schema2, install skopeo and use this script."
  exit 2
fi

log "Success. Image is SageMaker-compatible: ${ECR_URI}"
log "Manifest type: ${MEDIATYPE}"
