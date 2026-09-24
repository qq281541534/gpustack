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
EXPECTED_DIGEST="${EXPECTED_DIGEST:-}"
MIN_FREE_GB="${MIN_FREE_GB:-10}"

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

image_ref="${IMAGE_REGISTRY}/${IMAGE_NAMESPACE}/${IMAGE_REPOSITORY}"

# Disk preflight: pull and unpack need room before the old container stops.
docker_root="$(docker info --format '{{.DockerRootDir}}')"
free_gb="$(df -Pk "${docker_root}" | awk 'NR==2 {print int($4 / 1024 / 1024)}')"
echo "Free disk under ${docker_root}: ${free_gb} GiB (minimum ${MIN_FREE_GB} GiB)"
if [[ "${free_gb}" -lt "${MIN_FREE_GB}" ]]; then
  echo "ERROR: not enough free disk to pull ${image_ref}:${IMAGE_TAG}." >&2
  exit 1
fi

echo "Deploying ${image_ref}:${IMAGE_TAG}"
docker compose "${compose_args[@]}" pull gpustack-server

if [[ -n "${EXPECTED_DIGEST}" ]]; then
  repo_digests="$(docker image inspect "${image_ref}:${IMAGE_TAG}" --format '{{join .RepoDigests " "}}')"
  if [[ " ${repo_digests} " != *"@${EXPECTED_DIGEST} "* ]]; then
    echo "ERROR: pulled image digest (${repo_digests}) does not match ${EXPECTED_DIGEST}." >&2
    exit 1
  fi
fi

docker compose "${compose_args[@]}" up -d --no-build gpustack-server

running_image="$(docker inspect --format '{{.Config.Image}}' "$(docker compose "${compose_args[@]}" ps -q gpustack-server)")"
if [[ "${running_image}" != "${image_ref}:${IMAGE_TAG}" ]]; then
  echo "ERROR: gpustack-server runs ${running_image}, expected ${image_ref}:${IMAGE_TAG}." >&2
  exit 1
fi

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

echo "Deployment verified: ${running_image}${EXPECTED_DIGEST:+@${EXPECTED_DIGEST}}"
if [[ -n "${previous_tag}" ]]; then
  echo "Rollback-ready previous tag: ${previous_tag}"
else
  echo "Rollback-ready previous tag: unknown; check registry or prior release evidence."
fi

# Remove older images of this repository, keeping the current and the
# previous tag locally for a fast rollback.
docker images --format '{{.Repository}}:{{.Tag}} {{.ID}}' \
  | awk -v repo="${image_ref}" -v current="${IMAGE_TAG}" -v previous="${previous_tag}" \
    '$1 ~ "^" repo ":" && $1 != repo ":" current && $1 != repo ":" previous {print $2}' \
  | sort -u \
  | xargs -r docker image rm >/dev/null || true
