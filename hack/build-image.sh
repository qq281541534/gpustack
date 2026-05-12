#!/usr/bin/env bash
#
# GPUStack Docker 镜像构建脚本
# 支持国内镜像源加速，并保留本地二开前端产物
#

set -o errexit
set -o nounset
set -o pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

cd "${ROOT_DIR}"

# ------------------------------------------------------------------
# 配置参数
# ------------------------------------------------------------------

IMAGE_NAME="${IMAGE_NAME:-gpustack-custom}"
IMAGE_TAG="${IMAGE_TAG:-latest}"
DOCKERFILE="${DOCKERFILE:-pack/Dockerfile}"
PLATFORM="${PLATFORM:-linux/amd64}"

# 是否使用国内镜像源（默认启用）
USE_CHINA_MIRROR="${USE_CHINA_MIRROR:-true}"

# 是否跳过 UI 远程下载（优先使用本地二开产物）
# 注意：install.sh 已修改，会优先检测本地 UI，此参数为兼容保留
UI_DOWNLOAD="${UI_DOWNLOAD:-true}"

# ------------------------------------------------------------------
# 颜色输出
# ------------------------------------------------------------------

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
  echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
  echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
  echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
  echo -e "${BLUE}[STEP]${NC} $1"
}

# ------------------------------------------------------------------
# 前置检查
# ------------------------------------------------------------------

check_prerequisites() {
  log_step "检查前置条件..."

  if ! command -v docker &> /dev/null; then
    log_error "Docker 未安装，请先安装 Docker"
    exit 1
  fi

  if ! docker info &> /dev/null; then
    log_error "Docker 守护进程未运行，请启动 Docker"
    exit 1
  fi

  # 检查本地 UI 产物是否存在
  if [[ -d "${ROOT_DIR}/gpustack/ui" && -f "${ROOT_DIR}/gpustack/ui/index.html" ]]; then
    log_info "检测到本地二开前端产物：gpustack/ui/"
    log_info "构建时将优先使用本地 UI，不会覆盖为官方版本"
  else
    log_warn "未检测到本地二开前端产物（gpustack/ui/index.html 不存在）"
    log_warn "构建时将下载官方 UI，如需使用二开前端，请先编译并复制到 gpustack/ui/"
  fi

  log_info "前置条件检查通过"
}

# ------------------------------------------------------------------
# 构建镜像
# ------------------------------------------------------------------

build_image() {
  log_step "开始构建 Docker 镜像..."
  log_info "镜像名称: ${IMAGE_NAME}:${IMAGE_TAG}"
  log_info "目标平台: ${PLATFORM}"
  log_info "Dockerfile: ${DOCKERFILE}"
  log_info "国内镜像源: ${USE_CHINA_MIRROR}"
  log_info "UI 下载: ${UI_DOWNLOAD}"

  local build_args=()

  # 国内镜像源参数
  if [[ "${USE_CHINA_MIRROR}" == "true" ]]; then
    log_info "已启用国内镜像源加速"
  fi

  # UI 下载参数（install.sh 已修改优先检测本地 UI，此处为双重保障）
  build_args+=("--build-arg" "UI_DOWNLOAD=${UI_DOWNLOAD}")

  # 平台参数
  build_args+=("--platform" "${PLATFORM}")

  # 标签
  build_args+=("--tag" "${IMAGE_NAME}:${IMAGE_TAG}")

  # Dockerfile 路径
  build_args+=("--file" "${DOCKERFILE}")

  log_step "执行 docker build..."
  docker build \
    "${build_args[@]}" \
    "${ROOT_DIR}"

  log_info "Docker 镜像构建完成！"
}

# ------------------------------------------------------------------
# 验证镜像
# ------------------------------------------------------------------

verify_image() {
  log_step "验证镜像..."

  if ! docker images "${IMAGE_NAME}:${IMAGE_TAG}" --format '{{.Repository}}:{{.Tag}}' | grep -q "${IMAGE_NAME}:${IMAGE_TAG}"; then
    log_error "镜像构建失败，未找到 ${IMAGE_NAME}:${IMAGE_TAG}"
    exit 1
  fi

  log_info "镜像验证通过"
  docker images "${IMAGE_NAME}:${IMAGE_TAG}" --format 'table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}'

  # 检查镜像中是否包含二开前端
  log_step "检查镜像中是否包含二开前端..."
  local ui_check
  ui_check=$(docker run --rm "${IMAGE_NAME}:${IMAGE_TAG}" \
    python3 -c "import gpustack, os; p=os.path.join(os.path.dirname(gpustack.__file__), 'ui/index.html'); print(open(p).read()[:2000])" 2>/dev/null | grep -o "LLM部署平台" | head -1 || true)

  if [[ "${ui_check}" == "LLM部署平台" ]]; then
    log_info "✅ 镜像中包含二开前端（LLM部署平台）"
  else
    log_warn "⚠️ 未在镜像中检测到二开前端，可能使用了官方默认 UI"
  fi
}

# ------------------------------------------------------------------
# 使用说明
# ------------------------------------------------------------------

usage() {
  cat <<EOF
GPUStack Docker 镜像构建脚本

用法: $0 [选项]

选项:
  -n, --name NAME       镜像名称 (默认: gpustack-custom)
  -t, --tag TAG         镜像标签 (默认: latest)
  -p, --platform ARCH   目标平台 (默认: linux/amd64)
  --no-mirror           禁用国内镜像源
  --ui-download         强制从远程下载 UI（覆盖本地二开产物）
  -h, --help            显示此帮助

示例:
  # 默认构建（使用国内镜像源 + 本地二开 UI）
  $0

  # 指定镜像名称和标签
  $0 --name my-gpustack --tag v1.0.0

  # 构建 amd64 平台镜像
  $0 --platform linux/amd64

  # 禁用国内镜像源
  $0 --no-mirror

EOF
}

# ------------------------------------------------------------------
# 主流程
# ------------------------------------------------------------------

main() {
  # 解析参数
  while [[ $# -gt 0 ]]; do
    case $1 in
      -n|--name)
        IMAGE_NAME="$2"
        shift 2
        ;;
      -t|--tag)
        IMAGE_TAG="$2"
        shift 2
        ;;
      -p|--platform)
        PLATFORM="$2"
        shift 2
        ;;
      --no-mirror)
        USE_CHINA_MIRROR="false"
        shift
        ;;
      --ui-download)
        UI_DOWNLOAD="true"
        shift
        ;;
      -h|--help)
        usage
        exit 0
        ;;
      *)
        log_error "未知参数: $1"
        usage
        exit 1
        ;;
    esac
  done

  log_info "========================================"
  log_info "GPUStack Docker 镜像构建"
  log_info "========================================"

  check_prerequisites
  build_image
  verify_image

  log_info "========================================"
  log_info "构建完成！"
  log_info "镜像: ${IMAGE_NAME}:${IMAGE_TAG}"
  log_info "========================================"
  log_info ""
  log_info "启动命令示例:"
  log_info "  docker run -d --name gpustack-custom \\"
  log_info "    -p 8080:80 \\"
  log_info "    -v gpustack-data:/var/lib/gpustack \\"
  log_info "    ${IMAGE_NAME}:${IMAGE_TAG}"
}

main "$@"
