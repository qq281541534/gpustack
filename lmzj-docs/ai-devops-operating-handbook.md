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

`PR merged` 只表示代码被接受，不表示已经部署生产。镜像构建只表示代码被打包。

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
