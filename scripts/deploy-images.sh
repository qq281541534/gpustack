#!/usr/bin/env bash
#
# Pull-only production deploy for GPUStack.

set -euo pipefail

IMAGE_TAG="${1:-${GPUSTACK_TAG:-}}"
IMAGE_REGISTRY="${IMAGE_REGISTRY:-registry.cn-chengdu.aliyuncs.com}"
IMAGE_NAMESPACE="${IMAGE_NAMESPACE:-lmzjai}"
IMAGE_REPOSITORY="${IMAGE_REPOSITORY:-${ACR_REPOSITORY:-gpustack-custom}}"
PROD_DEPLOY_PATH="${PROD_DEPLOY_PATH:-/opt/gpustack/docker-compose}"
COMPOSE_FILES="${COMPOSE_FILES:-docker-compose.server.yaml}"
HEALTHCHECK_BASE_URL="${HEALTHCHECK_BASE_URL:-http://127.0.0.1:8080}"
CURRENT_TAG_FILE="${CURRENT_TAG_FILE:-.lmzj-current-image-tag}"

if [[ ! "${IMAGE_TAG}" =~ ^[0-9a-f]{40}$ ]]; then
  echo "ERROR: image tag must be a full 40-character lowercase git SHA." >&2
  exit 1
fi

case "${IMAGE_TAG}" in
  latest|dev|main|v*)
    echo "ERROR: floating or version alias tags are not allowed for production deploy." >&2
    exit 1
    ;;
esac

cd "${PROD_DEPLOY_PATH}"

compose_args=()
for compose_file in ${COMPOSE_FILES}; do
  compose_args+=("-f" "${compose_file}")
done

export IMAGE_REGISTRY
export IMAGE_NAMESPACE
export GPUSTACK_IMAGE_NAMESPACE="${GPUSTACK_IMAGE_NAMESPACE:-${IMAGE_NAMESPACE}}"
export IMAGE_REPOSITORY
export GPUSTACK_TAG="${IMAGE_TAG}"

previous_tag=""
if [[ -f "${CURRENT_TAG_FILE}" ]]; then
  previous_tag="$(cat "${CURRENT_TAG_FILE}")"
fi

echo "Deploying ${IMAGE_REGISTRY}/${IMAGE_NAMESPACE}/${IMAGE_REPOSITORY}:${IMAGE_TAG}"
docker compose "${compose_args[@]}" pull gpustack-server
docker compose "${compose_args[@]}" up -d --no-build gpustack-server

# The server takes ~60-90s to boot (embedded postgres + migrations + uvicorn);
# poll until healthy instead of failing on the first refused connection.
health_wait() {
  local endpoint="$1" waited=0
  while [ "${waited}" -lt 300 ]; do
    if curl --fail --silent --max-time 5 "${HEALTHCHECK_BASE_URL%/}${endpoint}" >/dev/null 2>&1; then
      return 0
    fi
    sleep 10
    waited=$((waited + 10))
  done
  echo "ERROR: ${endpoint} did not become healthy within 300s." >&2
  return 1
}
health_wait "/healthz"
health_wait "/readyz"

printf '%s\n' "${IMAGE_TAG}" > "${CURRENT_TAG_FILE}"

echo "Deployment verified."
if [[ -n "${previous_tag}" ]]; then
  echo "Rollback-ready previous tag: ${previous_tag}"
else
  echo "Rollback-ready previous tag: unknown; check registry or prior release evidence."
fi

image_ref="${IMAGE_REGISTRY}/${IMAGE_NAMESPACE}/${IMAGE_REPOSITORY}"
docker images --format '{{.Repository}}:{{.Tag}} {{.ID}}' \
  | awk -v repo="${image_ref}" -v current="${IMAGE_TAG}" '$1 ~ "^" repo ":" && $1 != repo ":" current {print $2}' \
  | sort -u \
  | xargs -r docker image rm >/dev/null
