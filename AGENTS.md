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
- Production image: `gpustack-custom`，默认使用 slim server 构建。
- Production package extras: `audio`。不要在生产 server 镜像默认安装 `all`，
  因为 `all` 会引入 `vllm`、PyTorch/CUDA/xformers 等推理运行栈，显著放大镜像。
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
- `production` environment 必须存在并保存生产 secrets；多人维护时启用 required
  reviewers 和 prevent self-review。
- 单人维护 bootstrap 阶段可关闭 production required reviewers，避免“对话确认部署”
  和 GitHub UI 审批重复；此时必须保留 `DEPLOY <full-sha>` 输入确认。
- deployment branches 只允许 `dev`。
- 生产相关 secrets 优先放入 `production` environment，不放普通 repository secrets。

## AI Issue to Production

所有 issue、PR、CI/CD、release、deployment、verification、rollback 工作都必须遵循
`ai-issue-to-production`。该 skill 的公司级源仓库是
`company-ai-skills/skills/ai-issue-to-production/`；Codex 全局安装路径通常是
`/Volumes/data/Users/lcx/.codex/skills/ai-issue-to-production/`。本文件只记录 GPUStack
项目特定事实和本地规则，不维护 repo-local skill 副本。

必须执行的交付链路：

```text
Issue
  -> branch from dev
  -> PR to dev
  -> PR checks
  -> human review and merge
  -> post-merge local sync to dev
  -> immutable image build from dev
  -> pre-deploy artifact review
  -> production manifest review
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
- PR 合并后继续检查构建或部署前，先同步本地 `dev`，并用
  `git status --short --branch`、`git log -1 --oneline` 确认本地 HEAD 已包含 merge
  commit。

## Issue 和 PR 规则

- 生产相关工作必须先有 GitHub Issue。
- PR 默认 target 为 `dev`，除非人类负责人明确记录其他 target。
- PR body 必须使用 `Refs #<issue>`。
- PR body 不得使用 `Closes`、`Fixes`、`Resolves`。
- PR body 必须包含摘要、验证、部署影响、回滚方案和上游冲突风险。
- Issue 在生产部署、验证和回滚准备完成前保持 open；证据齐全后 AI 可按人类明确指令关闭 Issue。

## 上游同步减功能红线

减功能或商业化的合并属于最重要的红线，必须在上游同步评估阶段发现，
不得拖到生产验收阶段。本规则来自 v2.2.3 同步教训（Issue #22）。

- 任何上游同步评估必须包含"减功能/商业化 diff"：枚举被删除或收缩的
  后端路由、数据库表、schema 字段、UI 页面、菜单和功能入口。
- 每个被移除的能力必须逐项标注我们是否在用；证据以生产库实际数据
  （行数、内容）和当前部署前端代码引用为准，不得凭印象判断。
- UI 入口从"可用"变为"禁用/企业版提示/升级推销"同样视为减功能。
- 任何在用功能被移除即一票否决：升级前必须先在 fork 中恢复该功能，
  或放弃本次同步。
- 同步评估报告必须单独列出减功能清单并给出定性结论；缺少该检查的
  评估视为不完整，不得进入合并关口。

## AI 短期分支清理

- PR 合并、release source 同步、证据记录完成后，AI 必须清理自己创建的已合并本地工作分支。
- 远端 PR 分支默认删除；如果 GitHub 已自动删除，记录 already gone。
- 不得删除 `main`、`dev`、`release/*`、`hotfix/*`、`upstream/*`、未合并分支、仍有关联
  open PR 的分支、归属不清分支或人类明确要求保留的分支。

## 构建和部署规则

- 生产镜像必须由 GitHub Actions 构建，不在生产服务器构建。
- 生产 server 镜像默认构建参数为 `GPUSTACK_PACKAGE_EXTRAS=audio`。
- 只有明确需要 all-in-one/full runtime 镜像时，才允许把
  `GPUSTACK_PACKAGE_EXTRAS` 改为 `all`；full 镜像不得替代默认生产 server 镜像。
- 生产镜像 tag 必须是完整 40 位 commit SHA。
- 不部署 `latest`、`dev`、版本别名或短 SHA 到生产。
- 生产部署必须使用手动 deploy workflow，并指定完整 SHA tag。
- `deploy-production.yml` 必须绑定 `environment: production`，使用 production secrets。
  单人维护 bootstrap 阶段可不启用 required reviewers，但必须保留完整 SHA 和
  `DEPLOY <full-sha>` 强确认。
- 生产服务器只拉取镜像并执行 `docker compose up -d --no-build`。
- 回滚使用 registry 中上一版不可变完整 SHA 镜像。
- `image_built` 不等于可部署。部署前必须审查 image digest/size、目标磁盘余量、
  dependency profile，以及 production compose/manifest 是否使用不可变镜像、正确
  secrets、volumes、ports、health checks 和生产路径。
- 长耗时 workflow 中断、会话恢复或上下文丢失后，必须重新查询 run final conclusion、
  job logs 和 health check 证据；缺少证据时只能标记为 `unresolved`。
- `AGENTS.md`、`CLAUDE.md`、`.claude/**`、`.trae/**`、`.cursor/**`、`README*`、`docs/**`、`lmzj-docs/**`、
  `skills/**`、`.github/workflows/**`、Issue template、PR template、deploy script、production
  compose/manifest 和纯 process/lint 脚本变更属于 non-runtime，不得构建或 push 生产镜像。

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
