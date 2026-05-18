# GPUStack Fork 维护方案

> 本文档记录 GPUStack 项目的 Fork 维护策略，确保团队能够长期同步官方更新并进行二次开发。
>
> **Fork 仓库**: https://github.com/qq281541534/gpustack.git  
> **上游仓库**: https://github.com/gpustack/gpustack.git  
> **维护方式**: 手动 Sync Fork（方式一）

---

## 一、Fork 背景

### 1.1 为什么要 Fork？

| 需求 | 说明 |
|------|------|
| **持续合并官方更新** | 官方 `gpustack/gpustack` 持续迭代，我们需要定期合并官方修复和新功能 |
| **二次开发** | 在官方代码基础上进行自定义修改（二开），满足内部业务需求 |
| **版本控制** | 通过 Fork 保持独立的版本管理，避免直接修改官方仓库 |

### 1.2 仓库关系

```
┌─────────────────────────┐         ┌─────────────────────────┐
│   gpustack/gpustack     │         │  qq281541534/gpustack   │
│     (上游官方仓库)        │ ──────► │      (我们的 Fork)       │
│                         │  Sync   │                         │
└─────────────────────────┘         └─────────────────────────┘
                                              │
                                              ▼
                                    ┌─────────────────────────┐
                                    │   lmzj-docs/ (本文档)    │
                                    │   自定义二开代码...        │
                                    └─────────────────────────┘
```

---

## 二、本地开发环境配置

### 2.1 首次克隆

```bash
# 从我们的 Fork 克隆（注意：不是官方仓库）
git clone https://github.com/qq281541534/gpustack.git
cd gpustack
```

### 2.2 配置上游（Upstream）

Fork 后必须手动添加 upstream 远程地址，才能拉取官方更新：

```bash
# 查看当前远程仓库
git remote -v
# origin    https://github.com/qq281541534/gpustack.git (fetch)
# origin    https://github.com/qq281541534/gpustack.git (push)

# 添加上游官方仓库
git remote add upstream https://github.com/gpustack/gpustack.git

# 验证
git remote -v
# origin    https://github.com/qq281541534/gpustack.git (fetch)
# origin    https://github.com/qq281541534/gpustack.git (push)
# upstream  https://github.com/gpustack/gpustack.git (fetch)
# upstream  https://github.com/gpustack/gpustack.git (push)
```

> **⚠️ 重要**: 每次新克隆或新成员加入时，都需要执行 `git remote add upstream`。

---

## 三、手动同步上游更新（方式一）

### 3.1 什么时候需要同步？

| 场景 | 建议操作 |
|------|----------|
| 官方发布了新版本（Release） | 建议立即同步 |
| 官方修复了关键 Bug | 建议尽快同步 |
| 日常维护 | 建议每周检查一次 |
| 开始新的二开功能前 | **必须同步**，避免后续大量冲突 |

### 3.2 同步步骤（GitHub Web 界面）

**步骤 1**: 打开你的 Fork 仓库页面  
`https://github.com/qq281541534/gpustack`

**步骤 2**: 如果上游有更新，页面会显示提示：
```
This branch is N commits behind gpustack:main.
[Sync fork]
```

**步骤 3**: 点击 **"Sync fork"** → **"Update branch"**

**步骤 4**: 等待同步完成，页面会显示：
```
This branch is up to date with gpustack:main.
```

**步骤 5**: 本地拉取更新
```bash
git pull origin main
```

### 3.3 同步步骤（命令行方式）

如果习惯用命令行，也可以不通过 Web 界面：

```bash
# 1. 切换到 main 分支
git checkout main

# 2. 拉取上游更新
git fetch upstream

# 3. 合并上游 main 分支到本地 main
git merge upstream/main

# 4. 推送到自己的 Fork
git push origin main
```

---

## 四、二开分支管理策略

### 4.1 分支规范

为了避免同步时产生大量冲突，建议采用以下分支策略：

```
main (与官方同步，尽量不直接修改)
  │
  ├── dev (内部开发主干，基于 main)
  │     │
  │     ├── feature/xxx (具体功能分支)
  │     ├── feature/yyy
  │     └── hotfix/zzz
  │
  └── lmzj-docs (文档维护分支，可选)
```

### 4.2 推荐工作流程

```bash
# 1. 确保 main 是最新的（已同步上游）
git checkout main
git pull origin main

# 2. 从 main 创建功能分支
git checkout -b feature/my-custom-feature

# 3. 进行二开代码修改...
# ... coding ...

# 4. 提交到功能分支
git add .
git commit -m "feat: 自定义功能描述"

# 5. 合并到 dev（或 main，视团队策略而定）
git checkout dev
git merge feature/my-custom-feature

# 6. 推送
git push origin dev
```

### 4.3 同步时的冲突处理

如果官方更新和你的二开代码有冲突：

```bash
# 1. 同步上游
git fetch upstream
git merge upstream/main

# 2. 如果出现冲突，会提示类似：
# Auto-merging gpustack/config/config.py
# CONFLICT (content): Merge conflict in gpustack/config/config.py

# 3. 手动编辑冲突文件，解决后标记为已解决
git add gpustack/config/config.py

# 4. 完成合并
git commit -m "merge: sync upstream and resolve conflicts"

# 5. 推送
git push origin main
```

---

## 五、注意事项

### 5.1 不要直接修改 main 分支

`main` 分支建议保持与官方同步，这样每次 sync 最简单。所有二开代码应该在 `dev` 或 `feature/*` 分支上进行。

### 5.2 关注 Release 标签

官方发版时通常会打 `vX.Y.Z` 标签。建议关注 Release 页面：  
https://github.com/gpustack/gpustack/releases

### 5.3 重大版本升级

如果官方发布了 **Breaking Change**（破坏性变更），同步前务必：
1. 在本地测试环境先合并验证
2. 检查官方 Release Notes
3. 确保二开代码兼容后再推送到生产分支

### 5.4 文档维护

本文档位于 `lmzj-docs/` 目录下，二开相关的技术文档、部署手册、内部规范都可以放在这里。这些文件不会影响与官方仓库的同步（官方没有此目录）。

---

## 六、镜像构建与部署

### 6.1 GitHub Actions 自动构建（推荐）

本项目已配置 GitHub Actions，支持在 GitHub 云端自动构建 Docker 镜像并推送到阿里云 ACR。

**前置条件**：
1. 在 GitHub 仓库 `Settings → Secrets and variables → Actions` 中配置以下 Secrets：
   - `ALIYUN_ACR_USERNAME`
   - `ALIYUN_ACR_PASSWORD`
2. 阿里云 ACR 命名空间 `lmzjai` 和镜像仓库 `gpustack-custom` 已创建
3. 生产发布必须使用完整 40 位 commit SHA 作为镜像标签，不使用 `latest`、`dev` 或短 SHA。

**触发构建**：
1. 打开 GitHub 仓库 → **Actions** 标签
2. 选择 **Build Custom GPUStack Image**
3. 点击右侧 **Run workflow**
4. 参数说明：
   - `tag`: 镜像标签。生产发布必须使用完整 40 位 commit SHA
   - `frontend_ref`: 前端仓库分支，默认 `dev`
   - `push_image`: 勾选则推送到阿里云 ACR

**构建流程**：
```
拉取后端代码(dev) → 拉取前端代码(gpustack-ui/dev) → 编译前端 → 复制到 gpustack/ui/
→ 构建 linux/amd64 Docker 镜像 → 推送到 registry.cn-chengdu.aliyuncs.com/lmzjai/gpustack-custom:<full-sha>
```

构建预计 **15~30 分钟**。

### 6.2 本地构建脚本（可选）

如需在本地构建镜像（需 Docker 环境能访问 Docker Hub）：

```bash
# 赋予执行权限
chmod +x hack/build-image.sh

# 默认构建（linux/amd64，使用国内镜像源）
./hack/build-image.sh

# 指定标签和平台
./hack/build-image.sh --tag v1.0.0 --platform linux/amd64

# 查看帮助
./hack/build-image.sh --help
```

> ⚠️ **注意**：本地构建需要能正常访问 Docker Hub 拉取基础镜像。当前本地环境因网络限制无法完成构建，建议使用 GitHub Actions。

### 6.3 Docker Compose 部署

项目已修改 `docker-compose/` 下的配置文件，默认使用阿里云 ACR 自定义镜像。

**镜像地址**：
```
registry.cn-chengdu.aliyuncs.com/lmzjai/gpustack-custom:<full-40-character-sha>
```

**部署步骤**：

```bash
# 1. 登录阿里云 ACR（服务器上只需执行一次）
docker login --username=<ALIYUN_ACR_USERNAME> registry.cn-chengdu.aliyuncs.com
# 输入 GitHub Secret ALIYUN_ACR_PASSWORD 对应的 ACR 密码

# 2. 进入 docker-compose 目录
cd docker-compose

# 3. 启动服务（生产必须只拉取镜像，不在服务器构建）
GPUSTACK_TAG=<full-40-character-sha> docker compose -f docker-compose.server.yaml up -d --no-build

# 4. 查看日志
docker logs -f gpustack-server

# 5. 访问
http://<服务器IP>/
```

**如需使用外部监控（Prometheus + Grafana）**：

```bash
docker compose -f docker-compose.external-observability.yaml up -d
```

**GPU 支持（可选）**：

编辑 `docker-compose.server.yaml`，取消 `deploy.resources.reservations.devices` 段的注释即可启用 NVIDIA GPU 支持。

**环境变量覆盖**：

如需临时切换回官方镜像或其他镜像，可通过环境变量覆盖：

```bash
IMAGE_REGISTRY=docker.io IMAGE_NAMESPACE=gpustack GPUSTACK_TAG=<full-40-character-sha> \
docker compose -f docker-compose.server.yaml up -d --no-build
```

**SSO 配置（OIDC / SAML）**：

Docker Compose 部署已支持通过 `.env` 文件配置 SSO，参数留空即禁用 SSO（只显示本地登录）。

```bash
# 1. 复制模板
cd docker-compose
cp .env.example .env

# 2. 编辑 .env，填写 SSO 参数（以 OIDC 为例）
# GPUSTACK_OIDC_ISSUER=https://keycloak.example.com/realms/master
# GPUSTACK_OIDC_CLIENT_ID=gpustack
# GPUSTACK_OIDC_CLIENT_SECRET=<your-secret>
# GPUSTACK_OIDC_REDIRECT_URI=https://gpustack.example.com/auth/oidc/callback
# GPUSTACK_EXTERNAL_AUTH_NAME=preferred_username
# GPUSTACK_EXTERNAL_AUTH_FULL_NAME=name

# 3. 启动服务
 docker compose -f docker-compose.server.yaml up -d
```

> 详细参数说明请参考 `SSO-INTEGRATION.md`。`.env` 文件已加入 `.gitignore`，不会被提交到仓库。

### 6.4 二开前端产物同步

前端二开代码在 `gpustack-ui` 仓库中修改。如需更新后端中的前端产物：

```bash
# 1. 编译前端
cd ~/thirdComponent/AI/gpustack-ui
pnpm build

# 2. 复制到后端
rm -rf ~/thirdComponent/AI/gpustack/gpustack/ui/*
cp -r ~/thirdComponent/AI/gpustack-ui/dist/* ~/thirdComponent/AI/gpustack/gpustack/ui/

# 3. 提交（如需要）
cd ~/thirdComponent/AI/gpustack
git add gpustack/ui/
git commit -m "chore: sync frontend build"
```

> 注：GitHub Actions 构建时已自动执行上述步骤，从 `gpustack-ui/dev` 分支拉取并编译前端，无需手动同步。

---

## 七、快速参考

| 操作 | 命令 |
|------|------|
| 克隆 Fork | `git clone https://github.com/qq281541534/gpustack.git` |
| 添加 upstream | `git remote add upstream https://github.com/gpustack/gpustack.git` |
| 查看远程 | `git remote -v` |
| 拉取上游 | `git fetch upstream` |
| 合并上游 | `git merge upstream/main` |
| 创建功能分支 | `git checkout -b feature/xxx` |
| 推送分支 | `git push origin feature/xxx` |
| 本地构建镜像 | `./hack/build-image.sh --tag v1.0.0` |
| Docker Compose 部署 | `GPUSTACK_TAG=<full-sha> docker compose -f docker-compose.server.yaml up -d --no-build` |
| Docker Compose + SSO | `cp docker-compose/.env.example docker-compose/.env` → 编辑 → `docker compose -f docker-compose.server.yaml up -d` |
| 登录阿里云 ACR | `docker login --username=<ALIYUN_ACR_USERNAME> registry.cn-chengdu.aliyuncs.com` |
| 前端产物同步 | `cp -r gpustack-ui/dist/* gpustack/ui/` |

---

*本文档由团队维护，如有疑问请在此目录下补充说明。*
