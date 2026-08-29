# ACR 镜像自持与节点部署配置（中国网络）

> 2026-08-29 确立。背景：docker hub / quay.io 在生产与客户网络不可达，
> GPUStack 对裸镜像名（`gpustack/runner`、`gpustack/runtime`）的 registry
> 解析会回落到国内地址，但我们的 ACR 账号没有 `gpustack` 命名空间。
> 方案：全部镜像推入自己的 `lmzjai` 命名空间，用官方配置点逐族钉死引用，
> 不依赖外网，不使用逐节点补丁。

## 一、镜像族与官方配置点

| 镜像族 | ACR 仓库 | 配置点 | 生效方式 |
|---|---|---|---|
| GPUStack server/worker | `lmzjai/gpustack-custom:<完整SHA>` | server compose 环境变量 `GPUSTACK_IMAGE_NAME_OVERRIDE`（自动跟随发版 SHA） | 集群「添加节点」命令的镜像行 |
| 推理 runner（vLLM/SGLang 等） | `lmzjai/runner:<tag>` | 推理后端 `version_configs.<版本>.image_name` | 该后端所有模型实例 |
| runtime 辅助（pause/health） | `lmzjai/runtime:pause` `lmzjai/runtime:health` | 添加节点命令 env `GPUSTACK_RUNTIME_DOCKER_PAUSE_IMAGE` / `GPUSTACK_RUNTIME_DOCKER_UNHEALTHY_RESTART_IMAGE` | worker 全部实例容器 |
| 基准测试（用到时再配） | `lmzjai/benchmark-runner:<tag>` | 集群节点配置 `benchmark_image_repo: "lmzjai/benchmark-runner"` | 基准测试任务 |

依据：`system_default_container_registry`/`image_repo`/`image_name_override`/
`benchmark_image_repo` 均为官方 start 命令配置项（docs: cli-reference/start#config-file）；
runner 按版本覆盖镜像为推理后端 `VersionConfig.image_name` 官方字段。

## 二、节点添加命令模板（客户/新 worker 用）

从 UI 集群页生成后，确认包含以下要点再执行。`runner`/`runtime` 仓库已设为公开，
**无需任何镜像凭证**（gpustack-custom 仍为私有：执行前先 `docker login
registry.cn-chengdu.aliyuncs.com`，或将其也设为公开后免去此步）：

```bash
sudo docker run -d --name gpustack-worker \
  -e "GPUSTACK_RUNTIME_DEPLOY_MIRRORED_NAME=gpustack-worker" \
  -e "GPUSTACK_TOKEN=<UI 生成的集群 token>" \
  -e "GPUSTACK_RUNTIME_DOCKER_PAUSE_IMAGE=registry.cn-chengdu.aliyuncs.com/lmzjai/runtime:pause" \
  -e "GPUSTACK_RUNTIME_DOCKER_UNHEALTHY_RESTART_IMAGE=registry.cn-chengdu.aliyuncs.com/lmzjai/runtime:health" \
  --restart=unless-stopped --privileged --network=host \
  --volume /var/run/docker.sock:/var/run/docker.sock \
  --volume gpustack-data:/var/lib/gpustack \
  --volume <模型目录>:<模型目录> \
  --runtime nvidia \
  registry.cn-chengdu.aliyuncs.com/lmzjai/gpustack-custom:<完整40位SHA> \
  --server-url https://llm.lmzjai.com \
  --worker-ip <内网IP> \
  --advertise-address <公网IP>
```

检查点：镜像必须是完整 SHA；模型目录挂载不可漏（LOCAL_PATH 模型必需）；
server→worker 10150 端口必须可达（安全组放行给 server IP）。
注意：若仓库改回私有，gpustack_runtime 的 SDK 拉取不读 docker login 凭证，
必须追加 `GPUSTACK_RUNTIME_DEPLOY_DEFAULT_CONTAINER_REGISTRY(_USERNAME/_PASSWORD)`
env（官方配置项）。

## 三、新推理后端版本入库流程

当模型需要新的 runner 版本（如 vllm 0.12.x）时：

```bash
# 1. 在能访问 quay.io 的机器拉取（当前可用：worker/server 均可达）
docker pull quay.io/gpustack/runner:<tag>
# 2. 打标推送
docker tag quay.io/gpustack/runner:<tag> registry.cn-chengdu.aliyuncs.com/lmzjai/runner:<tag>
docker push registry.cn-chengdu.aliyuncs.com/lmzjai/runner:<tag>
# 3. 在 推理后端 → vLLM → 版本配置 中为该版本增加 image_name 指向 ACR
```

## 四、验证记录（2026-08-29）

- `lmzjai/runtime:pause|health`、`lmzjai/runner:cuda12.8-vllm0.11.2` 已入库（46.8G runner 从 worker 推送）
- vLLM 0.11.2 `version_configs.image_name` 已指向 ACR；集群 `system_default_container_registry = registry.cn-chengdu.aliyuncs.com`
- **端到端验证一**（认证）：凭证 env 下从 ACR 拉取 → vLLM → 推理 200 ✓
- **端到端验证二**（冷启动 + 匿名）：删除本地镜像全部数据 → 重启实例 → 匿名拉取 46.8G（约 4 分钟）→ RUNNING → 推理 200 ✓

## 五、仓库可见性现状

- `lmzjai/runner`、`lmzjai/runtime`：**公开**（匿名拉取已验证）
- `lmzjai/gpustack-custom`：私有（CLI 拉取前需 `docker login`；如需完全免凭证可在控制台改公开）
- 历史遗留：`lmzjai/gpustack-runtime` 为早期命名，已被 `lmzjai/runtime` 取代，可在控制台删除
