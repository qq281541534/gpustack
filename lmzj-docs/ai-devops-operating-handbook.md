# GPUStack AI DevOps 操作手册

## 范围

本文档只覆盖 LMZJ GPUStack fork 的 AI 交付、CI/CD、发布、部署和回滚流程。
GPUStack upstream `docs/` 目录继续作为上游产品文档目录维护，不放入 LMZJ 专属流程。

## 项目画像

- Project type: `secondary_development`
- Repository visibility: `public`
- Release source branch: `dev`
- PR target branch: `dev`
- Governance level: `L4 platform-enforced`
- Docs directory: `lmzj-docs/`

## Public Repo L4 门禁

本仓库按 public repository 的 L4 平台强制模型治理。人类负责人必须在 GitHub UI 中
配置以下门禁：

- 对 `dev` 配置 branch protection 或 ruleset。
- 启用 Require a pull request before merging。
- 启用 Require status checks to pass / required status checks，至少要求 PR
  process lint 和轻量验证通过。
- 启用 Require approvals。
- 启用 Dismiss stale approvals when new commits are pushed。
- 创建 `production` environment。
- `production` environment 必须存在并保存生产 secrets；多人维护时启用 required
  reviewers 和 prevent self-review。
- 单人维护 bootstrap 阶段可关闭 production required reviewers，避免“对话确认部署”
  和 GitHub UI 审批重复；此时必须保留 `DEPLOY <full-sha>` 输入确认。
- deployment branches 只允许 `dev`。
- Production secrets 只放在 `production` environment。

## 开发关口

- 从最新 `dev` 创建分支。
- 使用 `feature/*`、`fix/*` 或 `docs/*` 分支。
- 上游同步、功能开发、镜像构建、生产部署必须拆开。
- 优先使用 extension、adapter、plugin、独立服务或 proxy 层，谨慎修改 upstream core。
- 所有生产相关 PR 都必须说明后续同步 `gpustack/gpustack` 的潜在冲突风险。
- PR 合并后继续构建、部署审查或生产验证前，先同步本地 `dev`，并用
  `git status --short --branch`、`git log -1 --oneline` 确认本地 HEAD 已包含 merge
  commit。

## PR 关口

PR 必须包含：

- `Refs #<issue>`
- 摘要
- 变更范围
- 验证命令和结果
- 部署影响
- 上游冲突风险
- 回滚方案

PR 不得包含：

- `Closes #...`
- `Fixes #...`
- `Resolves #...`
- 真实 secret、token、password、private key

## 镜像构建关口

生产镜像只有满足以下条件才可接受：

- 源 SHA 位于 `dev`。
- 源 SHA 关联到已合并进 `dev` 的 PR。
- 镜像 tag 是完整 40 位 commit SHA。
- 镜像推送到配置的 ACR 仓库。
- 生产 server 镜像使用 `GPUSTACK_PACKAGE_EXTRAS=audio` 的 slim profile，不默认安装
  `all` extras。`all` 会引入 `vllm`、PyTorch/CUDA/xformers 等推理运行栈，只能作为
  明确评估过磁盘容量的 full runtime 镜像使用。
- `AGENTS.md`、`CLAUDE.md`、`.trae/**`、`README*`、`docs/**`、`lmzj-docs/**`、
  `skills/**`、`.github/workflows/**`、PR template、deploy script、production
  compose/manifest 和纯 process/lint 脚本变更属于 non-runtime，不得构建或 push 生产镜像。

`PR merged` 只表示代码被接受，不表示已经部署生产。镜像构建只表示代码被打包。

## 部署前审查关口

`image_built` 不等于可部署。请求生产部署确认前必须审查：

- Image tag、digest、size。
- 生产目标机器磁盘余量，必须足够 pull、解压、启动新容器，并保留必要回滚空间。
- dependency profile，生产 server 默认 `audio`，不得把 `all`/full runtime 当默认生产镜像。
- production compose/manifest，确认使用不可变完整 SHA 镜像，无 `build:`、无 `latest`/短
  SHA，secrets、volumes、ports、health checks、restart policy 和生产部署路径已审查。

审查失败或 unresolved 时，不得请求生产部署确认。

## 生产部署关口

生产部署必须由人类针对一个精确镜像 tag 明确确认。使用
`.github/workflows/deploy-production.yml`，输入：

- `image_tag`: 完整 40 位 SHA。
- `confirm_production_deploy`: `DEPLOY <image_tag>`。
- `compose_files`: 生产服务器上的 compose 文件列表。
- `healthcheck_base_url`: 生产服务器可访问的基础 URL。

`deploy-production.yml` 必须绑定 `environment: production`，并使用 production
environment secrets。单人维护 bootstrap 阶段可不启用 required reviewers，但必须保留
完整 SHA 和 `DEPLOY <full-sha>` 强确认。

生产服务器必须：

- 使用 workflow 同步到 `PROD_DEPLOY_PATH` 的生产 compose 文件。
- 拉取指定镜像。
- 执行 `docker compose up -d --no-build`。
- 验证 `/healthz` 和 `/readyz`。
- 记录当前部署 tag。

生产服务器不得：

- 构建生产镜像。
- 部署 `latest`、`dev`、版本别名或短 SHA。
- 执行 `docker system prune -a --volumes` 等跨项目清理。

## Workflow 恢复

长耗时 workflow 中断、会话恢复或上下文丢失后，必须重新查询：

```bash
gh run list --workflow "<workflow>" --branch dev
gh run view <run-id> --json status,conclusion,jobs,url
```

恢复报告必须包含 final conclusion、job log 摘要和 health check 证据。没有 final
conclusion 或 health check 证据时，只能标记为 `workflow_in_progress`、`verification
missing` 或 `unresolved`，不得报告“部署成功”。

## 回滚

回滚使用同一个生产部署 workflow，输入上一版已知可用完整 SHA。

回滚步骤：

1. 从发布证据中找到上一版完整 SHA。
2. 确认该镜像仍在 ACR 中。
3. 手动触发 `deploy-production.yml`，输入上一版完整 SHA。
4. 验证 `/healthz`、`/readyz` 和公网 UI。
5. 在 Issue 或发布记录中记录回滚证据。

## Secret 管理

- Registry 凭据放 GitHub Secrets。
- 生产 SSH 凭据放 GitHub Secrets。
- Registry host、namespace、repository、frontend repository 放 GitHub Variables。
- `.env` 和 `.env.ssl` 不进 git。
- 如果凭据已经出现在文档或 git history 中，先由人类轮换，再使用新 workflow。

## 验证

流程变更后运行：

```bash
python /Volumes/data/Users/lcx/.codex/skills/ai-issue-to-production/scripts/audit_ai_issue_to_production.py \
  --repo . \
  --project-type secondary_development \
  --release-source dev \
  --pr-target dev

python -m compileall scripts
bash -n scripts/deploy-images.sh
```
