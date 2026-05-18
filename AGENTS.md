# GPUStack Agent 规则

## 项目画像

- Project type: `secondary_development`.
- Repository visibility: `public`.
- Governance level: `L4 platform-enforced`.
- Upstream repository: `https://github.com/gpustack/gpustack`.
- Fork repository: `https://github.com/qq281541534/gpustack`.
- Release source branch: `dev`.
- Feature branch base: `dev`.
- Production PR target: `dev`.
- Production image source branch: `dev`.
- Registry: `registry.cn-chengdu.aliyuncs.com/lmzjai`.
- Production image: `gpustack-custom`.
- Frontend customization source: `qq281541534/gpustack-ui`，默认分支 `dev`。
- LMZJ 专属流程文档目录：`lmzj-docs/`。
- GPUStack upstream 原有产品文档目录：`docs/`，不要放入 LMZJ 专属 AI 交付、
  CI/CD、release、deployment、rollback 文档。

## Public Repo L4 门禁

本仓库是 public repository，治理级别为 `L4 platform-enforced`。人类负责人必须在
GitHub UI 中配置以下平台门禁：

- 对 `dev` 配置 branch protection 或 ruleset。
- 启用 Require a pull request before merging。
- 启用 Require status checks to pass / required status checks，至少要求
  `pr-check.yml` 的检查通过。
- 启用 Require approvals。
- 启用 Dismiss stale approvals when new commits are pushed。
- 创建 `production` environment。
- 在 `production` environment 中启用 required reviewers。
- 启用 prevent self-review。
- deployment branches 只允许 `dev`。
- 生产相关 secrets 优先放入 `production` environment，不放普通 repository secrets。

## AI Issue to Production

所有 issue、PR、CI/CD、release、deployment、verification、rollback 工作都必须遵循
`skills/ai-issue-to-production/SKILL.md`。本文件只记录 GPUStack 项目特定事实和本地规则。

必须执行的交付链路：

```text
Issue
  -> branch from dev
  -> PR to dev
  -> PR checks
  -> human review and merge
  -> immutable image build from dev
  -> explicit human production deployment approval
  -> pull-only production deployment
  -> health verification
  -> rollback readiness
  -> human closes Issue
```

## 分支规则

- 不直接提交到 `dev` 或 `main`。
- `main` 尽量保持为 upstream/stable baseline。
- 公司集成和生产发布源是 `dev`。
- 功能分支、修复分支从最新 `dev` 创建。
- 上游同步、功能开发、镜像构建、生产部署必须拆成独立关口。

## Issue 和 PR 规则

- 生产相关工作必须先有 GitHub Issue。
- PR 默认 target 为 `dev`，除非人类负责人明确记录其他 target。
- PR body 必须使用 `Refs #<issue>`。
- PR body 不得使用 `Closes`、`Fixes`、`Resolves`。
- PR body 必须包含摘要、验证、部署影响、回滚方案和上游冲突风险。
- Issue 在生产部署、验证和回滚准备完成前保持 open。

## 构建和部署规则

- 生产镜像必须由 GitHub Actions 构建，不在生产服务器构建。
- 生产镜像 tag 必须是完整 40 位 commit SHA。
- 不部署 `latest`、`dev`、版本别名或短 SHA 到生产。
- 生产部署必须使用手动 deploy workflow，并指定完整 SHA tag。
- `deploy-production.yml` 必须绑定 `environment: production`，让 GitHub 在读取
  production secrets 前强制等待 required reviewers 批准。
- 生产服务器只拉取镜像并执行 `docker compose up -d --no-build`。
- 回滚使用 registry 中上一版不可变完整 SHA 镜像。

## Secret 规则

- 不提交 `.env`、`.env.ssl`、token、password、private key 或真实 SSO client secret。
- 文档只写 GitHub Secrets 和 Variables 名称，不写真实值。
- 如果 secret 已经出现在 git history 或文档中，先要求人类负责人轮换，再继续使用。

## 本地验证

AI Issue-to-Production 流程变更后运行：

```bash
python /Volumes/data/Users/lcx/.codex/skills/ai-issue-to-production/scripts/audit_ai_issue_to_production.py \
  --repo . \
  --project-type secondary_development \
  --release-source dev \
  --pr-target dev

python -m compileall scripts
```

应用代码变更先跑最小相关检查；风险较高时再扩大到 `make lint`、`make test` 或 `make ci`。
