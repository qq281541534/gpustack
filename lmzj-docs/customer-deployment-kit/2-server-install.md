# 2. Server 安装（管理端）

## 2.1 准备文件

在 server 主机创建部署目录并放入两个文件（均来自本仓库，随交付 SHA 固化）：

```bash
mkdir -p /opt/gpustack && cd /opt/gpustack
# 放入 docker-compose/docker-compose.server.yaml 与 scripts/deploy-images.sh
```

创建 `.env`（与 compose 同目录，按客户信息填写）：

```bash
# .env —— server 容器业务环境变量（按需增删）
GPUSTACK_HOST_PORT=8080
```

## 2.2 部署

镜像 tag = 后端仓库 dev 分支的完整 40 位 commit SHA（交付 Issue 中记录的 SHA）。

```bash
cd /opt/gpustack
PROD_DEPLOY_PATH=/opt/gpustack \
GPUSTACK_TAG=<完整40位SHA> \
bash deploy-images.sh <完整40位SHA>
```

脚本行为：校验 SHA → 拉取镜像（源：`registry.cn-chengdu.aliyuncs.com/lmzjai/gpustack-custom`，公开仓库）→ `up -d --no-build` → 轮询 healthz/readyz（最长 300s）→ 记录当前 tag。

> 首次启动含数据库初始化，约 60–90 秒就绪属正常。

## 2.3 管理员初始化

```bash
docker exec gpustack-server cat /var/lib/gpustack/initial_admin_password
```

浏览器访问 `http://<server>:8080`，用户名 `admin` + 初始密码登录，**立即改密**。

## 2.4 镜像版本自检

```bash
docker exec gpustack-server gpustack version
# 期望：version 与 git_commit 均为交付 SHA（v0.0.0 为异常，见 lmzj-docs 记录）
```

## 2.5 重要机制说明（交付人必读）

- compose 中 `GPUSTACK_IMAGE_NAME_OVERRIDE` 已指向 `${GPUSTACK_TAG}`：UI「集群→添加节点」命令自动携带与本 server 一致的镜像，**禁止改回官方 quay 镜像**；
- 推理 runner 镜像由「推理后端 version_configs」钉在 ACR（见 `../acr-image-mirror.md` §3）；
- 日常升级 = 用新 SHA 重跑 2.2 的命令（数据卷持久，配置不丢）；回滚 = 重跑上一交付 Issue 中记录的 SHA。
