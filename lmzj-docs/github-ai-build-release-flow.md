# GPUStack AI Issue-to-Production 发布流程

本文档是 LMZJ 维护 GPUStack 二开 fork 的 AI 交付执行源。GPUStack upstream 原有
`docs/` 目录保持为上游产品文档目录，LMZJ 专属的 CI/CD、release、deployment、
rollback 文档统一放在 `lmzj-docs/`。

## 项目画像

```yaml
project_type: secondary_development
repository_visibility: public
release_source_branch: dev
feature_branch_base: dev
pr_target_branch: dev
image_build_branch: dev
governance_level: L4 platform-enforced
docs_directory: lmzj-docs/
registry: registry.cn-chengdu.aliyuncs.com/lmzjai
image_names:
  - gpustack-custom
production_image_profile: slim-server
production_package_extras: audio
frontend_repository: qq281541534/gpustack-ui
frontend_default_ref: dev
deploy_workflow: .github/workflows/deploy-production.yml
deploy_inputs:
  image_tag: full_commit_sha
verification:
  - GET /healthz
  - GET /readyz
rollback:
  strategy: deploy_previous_full_sha
issue_closure: ai_allowed_after_verified_release
```

## Public Repo L4 平台门禁

本仓库是 public repository，治理级别为 `L4 platform-enforced`。这意味着生产发布
关口必须由 GitHub 平台强制，而不是只靠聊天确认、文档约束或补偿性 CI 检查。

人类负责人需要在 GitHub UI 中完成以下配置：

- 对 release source branch `dev` 配置 branch protection 或 ruleset。
- 启用 Require a pull request before merging。
- 启用 Require status checks to pass / required status checks，至少要求
  `pr-check.yml` 对应检查通过。
- 启用 Require approvals，至少 1 个非作者 human approval。
- 启用 Dismiss stale approvals when new commits are pushed。
- 创建 `production` environment。
- `production` environment 必须存在并保存生产 secrets；多人维护时启用 required
  reviewers 和 prevent self-review。
- 单人维护 bootstrap 阶段可关闭 production required reviewers，避免“对话确认部署”
  和 GitHub UI 审批重复；此时必须保留 `DEPLOY <full-sha>` 输入确认。
- deployment branches 只允许 `dev`。
- Production secrets 放入 `production` environment，不放普通 repository secrets。

## 必须执行的发布链路

1. 创建或复用 GitHub Issue。
2. 从最新 `dev` 创建功能分支或修复分支。
3. 提交 PR 到 `dev`。
4. PR body 使用 `Refs #<issue>`，不得使用 `Closes`、`Fixes`、`Resolves`。
5. PR checks 通过。
6. 人工审核并合并 PR。
7. PR 合并后，执行后续检查的 agent 必须先同步本地 `dev`，并用
   `git status --short --branch`、`git log -1 --oneline` 确认本地 HEAD 已包含 merge
   commit。
8. GitHub Actions 从 `dev` 构建不可变镜像
   `gpustack-custom:<full-40-character-sha>`。
9. 部署前审查 image digest/size、生产目标磁盘余量、dependency profile，以及
   production compose/manifest。
10. 人工明确确认是否将该完整 SHA 镜像部署到生产。
11. 手动触发生产部署 workflow，生产服务器只拉取镜像并执行
   `docker compose up -d --no-build`。
12. 验证 `/healthz`、`/readyz` 和必要业务路径。
13. 记录发布证据和上一版可回滚完整 SHA。
14. 生产验证和回滚准备证据齐全后，AI 可按人类明确指令关闭 Issue。

## Workflow 分工

### `.github/workflows/pr-check.yml`

- 触发：PR to `dev`。
- 校验 PR body 必须包含 `Refs #<issue>`。
- 拒绝 `Closes`、`Fixes`、`Resolves` 自动关闭关键词。
- 要求摘要、验证、部署影响、回滚、上游冲突风险等章节。
- 编译 `scripts/` 下的流程脚本，避免脚本语法错误进入 PR。

### `.github/workflows/build-images.yml`

- 触发：push to `dev` 或手动 `workflow_dispatch`。
- 只接受完整 40 位 commit SHA。
- 校验 SHA 位于 `dev`，并关联到已合并到 `dev` 的 PR。
- 从 `qq281541534/gpustack-ui` 构建二开前端。
- 构建并推送
  `registry.cn-chengdu.aliyuncs.com/lmzjai/gpustack-custom:<full-sha>`。
- 默认传入 `GPUSTACK_PACKAGE_EXTRAS=audio`，构建 slim server 镜像，避免把
  `vllm`、PyTorch/CUDA/xformers 等推理运行栈打进生产 control-plane 镜像。
- 如确需 full runtime 镜像，手动触发时可设置 `package_extras=all`，但该镜像不得
  替代默认生产 server 镜像，部署前必须单独评估磁盘容量和回滚空间。
- `AGENTS.md`、`CLAUDE.md`、`.claude/**`、`.trae/**`、`.cursor/**`、`README*`、`docs/**`、`lmzj-docs/**`、
  `skills/**`、`.github/workflows/**`、Issue template、PR template、deploy script、production
  compose/manifest 和纯 process/lint 脚本变更属于 non-runtime，不得触发或执行生产镜像
  build/push。

### `.github/workflows/deploy-production.yml`

- 只允许手动触发。
- 绑定 `environment: production`，使用 production environment secrets。
- 部署前把仓库中的 `docker-compose/<compose_file>` 同步到生产服务器
  `PROD_DEPLOY_PATH`，避免服务器残留旧 compose 文件。
- `image_tag` 必须是完整 40 位 SHA。
- `confirm_production_deploy` 必须精确输入 `DEPLOY <image_tag>`。
- 通过 SSH 在生产服务器执行 `scripts/deploy-images.sh`。
- 部署脚本必须拒绝 `latest`、`dev`、版本别名和短 SHA。

## Post-Merge Local Sync

PR 合并后继续 image build、deploy inspection 或 production verification 前，不得假设本地
worktree 自动跟随远程 `dev`。执行后续检查的 agent 必须先运行：

```bash
git fetch origin dev
git switch dev
git pull --ff-only origin dev
git status --short --branch
git log -1 --oneline
```

如果当前是 Codex worktree、detached HEAD 或需要保留当前分支，至少要 fetch 后明确检查
`origin/dev` 的最新 merge commit。未确认本地 HEAD 包含 merge commit 前，不继续构建或部署判断。

## Pre-Deploy Review

`image_built` 只表示镜像已构建和推送，不表示可部署。请求生产部署确认前必须完成：

- Image tag 是完整 40 位 SHA，记录 digest 和 size。
- 目标生产机器磁盘余量足够 pull、解压、启动新容器，并保留必要回滚空间。
- dependency profile 已确认；生产 server 默认使用 `audio`，不得误用 `all`/full runtime
  作为默认生产 control-plane 镜像。
- production compose/manifest 已审查，确认使用不可变镜像、无 `build:`、无 `latest`/短 SHA，
  secrets、volumes、ports、health checks、restart policy 和部署路径适合生产。

审查失败或仍有 unknown/unresolved 项时，不得请求生产部署确认。

## Workflow Resume

长耗时 workflow 中断、会话恢复或上下文丢失后，先重新查询 run 状态，而不是沿用上一轮口头结论：

```bash
gh run list --workflow "<workflow>" --branch dev
gh run view <run-id> --json status,conclusion,jobs,url
```

恢复时必须报告 final conclusion、job log 摘要和 health check 证据。没有 final conclusion 或
health check 证据时，状态只能是 `workflow_in_progress`、`verification missing` 或
`unresolved`，不得写成“部署成功”。

## GitHub 配置

Production environment secrets:

- `ALIYUN_ACR_USERNAME`
- `ALIYUN_ACR_PASSWORD`
- `PROD_SSH_HOST`
- `PROD_SSH_PORT`
- `PROD_SSH_USER`
- `PROD_SSH_KEY`
- `PROD_DEPLOY_PATH`

Repository variables:

- `ACR_REGISTRY`
- `ACR_NAMESPACE`
- `ACR_REPOSITORY`
- `FRONTEND_REPOSITORY`

建议变量:

- `PROD_COMPOSE_FILES`
- `PROD_HEALTHCHECK_BASE_URL`

## 发布证据模板

```markdown
## Release Evidence

- Issue:
- PR:
- Merge commit:
- Build workflow:
- Deploy workflow:
- Pre-deploy review: passed/failed/unresolved

## Images

- GPUStack: registry.cn-chengdu.aliyuncs.com/lmzjai/gpustack-custom:<full-sha>
- Digest:
- Image size:
- Dependency profile:

## Validation

- PR checks:
- Build:
- /healthz:
- /readyz:
- Public URL:

## Deployment Decision

- Production deployed: yes/no
- Human approver:
- Deployment time:

## Rollback

- Previous tag:
- Rollback input: deploy previous full SHA with deploy-production workflow
```

## 旧流程兼容说明

现有 `.github/workflows/build-custom-image.yml` 是历史手动构建入口，可作为迁移期
legacy workflow 保留，但它不得用于 `dev`、`latest`、版本别名或短 SHA 镜像；只能接受位于
`dev` 且关联到已合并 PR 的完整 40 位 SHA。生产发布优先使用 `build-images.yml` 产出的完整
SHA 镜像。
