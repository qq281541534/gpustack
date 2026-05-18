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
issue_closure: human_after_verified_release
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
7. GitHub Actions 从 `dev` 构建不可变镜像
   `gpustack-custom:<full-40-character-sha>`。
8. 人工明确确认是否将该完整 SHA 镜像部署到生产。
9. 手动触发生产部署 workflow，生产服务器只拉取镜像并执行
   `docker compose up -d --no-build`。
10. 验证 `/healthz`、`/readyz` 和必要业务路径。
11. 记录发布证据和上一版可回滚完整 SHA。
12. 人工在生产验证和回滚准备完成后关闭 Issue。

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

### `.github/workflows/deploy-production.yml`

- 只允许手动触发。
- 绑定 `environment: production`，使用 production environment secrets。
- 部署前把仓库中的 `docker-compose/<compose_file>` 同步到生产服务器
  `PROD_DEPLOY_PATH`，避免服务器残留旧 compose 文件。
- `image_tag` 必须是完整 40 位 SHA。
- `confirm_production_deploy` 必须精确输入 `DEPLOY <image_tag>`。
- 通过 SSH 在生产服务器执行 `scripts/deploy-images.sh`。
- 部署脚本必须拒绝 `latest`、`dev`、版本别名和短 SHA。

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

## Images

- GPUStack: registry.cn-chengdu.aliyuncs.com/lmzjai/gpustack-custom:<full-sha>
- Digest:

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
legacy workflow 保留；生产发布应优先使用 `build-images.yml` 产出的完整 SHA 镜像。
