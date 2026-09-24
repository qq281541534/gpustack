# GPUStack Agent 规则

## 项目画像

```yaml
project_type: secondary_development
repository_visibility: public
governance_level: platform_checks
upstream_repository: https://github.com/gpustack/gpustack
fork_repository: https://github.com/qq281541534/gpustack
release_source_branch: dev
pr_target_branch: dev
image_build_branch: dev
deployment_owner: qq281541534/gpustack
docs_directory: lmzj-docs/
registry: registry.cn-chengdu.aliyuncs.com/lmzjai
image_names: [gpustack-custom]
frontend_repository: qq281541534/gpustack-ui
frontend_pin: pack/frontend-ref
build_workflow: .github/workflows/build-images.yml
deploy_workflow: .github/workflows/deploy-production.yml
verification: [GET /healthz, GET /readyz, 公网 UI]
rollback: 以 rollback=true 部署上一版完整 SHA 镜像；含数据库迁移时先评估兼容性
delivery_mode: autonomous
authorization_scope:
  source: 负责人 2026-09-25 会话授权（方案 1A）
  repositories: [qq281541534/gpustack]
  environments: [production]
  actions: 推送工作分支、开 PR 并在必需检查通过后合并到 dev、触发镜像构建、部署生产、线上验证、常规回滚到上一版镜像、关闭 Issue、清理 AI 自建的已合并短期分支
  exclusions: 上游 gpustack 版本同步合并、删数据或不可逆的数据库迁移、secrets/权限/GitHub 设置修改、删除服务器 volume 或数据
docs_issue_required: false
issue_required_for: runtime_or_tracked_work
issue_closure: ai_after_verified_delivery
```

- 生产 server 镜像默认 `GPUSTACK_PACKAGE_EXTRAS=audio`（slim）。不要默认安装 `all`：
  它会引入 `vllm`、PyTorch/CUDA/xformers 等推理运行栈，显著放大镜像。
- LMZJ 专属流程文档放 `lmzj-docs/`；upstream 原有 `docs/` 不放 LMZJ 的交付、CI/CD、
  发布、部署、回滚文档。

## AI Issue to Production

交付、PR、CI/CD、发布和回滚使用 `ai-issue-to-production`。不能自动加载时读取公司级源仓库
`company-ai-skills/skills/ai-issue-to-production/SKILL.md`，只按当前任务需要读取 references。
本文件只记录 GPUStack 项目事实、持续授权和本地规则，不复制通用流程。

- 授权范围内 AI 连续完成合并、构建、部署、验证、回滚和 Issue 收尾，不逐 PR、逐 SHA
  或逐次关闭再向人类确认；`exclusions` 内的动作先提出具体决定。
- 改动范围以 `scripts/classify_change_scope.py` 为唯一口径，PR 检查和合并后构建共用：
  普通文档免 Issue、不构建；流程/发布治理只验证受影响规则、workflow 和脚本；runtime
  和无法识别的路径需要 Issue、应用检查，镜像输入变化时构建新镜像。
- 发布细节、GitHub 配置与恢复命令见 `lmzj-docs/github-ai-build-release-flow.md`，
  发布证据记入 `lmzj-docs/release-log.md`。

## GitHub 平台门禁

以下为实际生效配置，改动属于 `exclusions`：

- `dev` 由 ruleset `protect-dev` 保护：必须通过 PR、必需检查（required status checks）`PR check passed` 通过且
  分支与 `dev` 同步，禁止删除和强推；不要求人工 approval，不设管理员 bypass。
- 不用管理员 bypass 合并；检查失败就修复后以新 head 重跑。
- `production` environment 只允许 `dev` 部署，保存生产 secrets，不设 required reviewers。
- 仓库开启合并后自动删除 head 分支。

## 分支规则

- 不直接提交到 `dev` 或 `main`。
- `main` 尽量保持为 upstream/stable baseline。
- 公司集成和生产发布源是 `dev`。
- 功能分支、修复分支从最新 `dev` 创建，命名沿用 `<type>/<slug>`，如 `fix/*`、`docs/*`、
  `chore/*`。
- 上游同步和功能开发保持独立的 PR 与验证证据；构建、部署作为独立阶段自动接续。
- 合并后需要本地继续操作时，从 merge SHA 或已包含它的 `origin/dev` 读取，不假设本地
  worktree 已跟随远端。

## Issue 和 PR 规则

- PR target 为 `dev`。
- runtime/unknown 改动和系统性流程改造使用 Issue，PR body 写 `Refs #<issue>`，并包含
  修改、验证、发布影响、上游冲突风险、回滚。
- 普通文档和简单流程修改不要求 Issue，PR body 只需修改、验证。
- PR body 不得使用 `Closes`、`Fixes`、`Resolves`。
- Issue 在上线验证和回滚准备完成后由 AI 记录证据并关闭；仍含未交付目标时保持 open。

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

- PR 合并、证据记录完成后，AI 用 `git branch -d` 安全删除自己创建的已合并本地分支。
- 远端 PR 分支由 GitHub 自动删除；已不存在时记录 already gone。
- 不得删除 `main`、`dev`、`release/*`、`hotfix/*`、`upstream/*`、未合并分支、仍有关联
  open PR 的分支、归属不清分支或人类明确要求保留的分支。

## 构建和部署规则

- 生产镜像由 `build-images.yml` 在 GitHub Actions 构建，不在生产服务器构建。
- 生产镜像 tag 是完整 40 位 commit SHA；前端版本固定在 `pack/frontend-ref`，更新前端
  需提 PR 修改该文件。tag 已存在时复用，不覆盖。
- 非 `audio` extras 镜像的 tag 为 `<sha>-<extras>`，不得替代默认生产 server 镜像。
- 不部署 `latest`、`dev`、版本别名或短 SHA 到生产；生产部署使用 `deploy-production.yml`，
  服务器只拉取镜像并执行 `docker compose up -d --no-build`。
- 部署前核对镜像 digest、目标磁盘（`deploy-images.sh` 预检）和上一版回滚 tag；
  dependency profile 与 compose 未变化时复用已有审查结论，变化时审查不可变镜像、secrets、
  volumes、ports、health checks 和生产路径。
- 回滚以 `rollback=true` 部署上一版完整 SHA 镜像；含数据库迁移时先确认兼容性。
- workflow 中断或会话恢复后，只查询未决 run 的 final conclusion 和健康证据；缺少证据时
  标记为 `unresolved`，不重复 dispatch 状态不明的部署。
- 镜像引用自持体系（compose 的 `GPUSTACK_IMAGE_NAME_OVERRIDE`、推理后端
  `version_configs.image_name`、worker 的 runtime pause/health env）指向 `lmzjai` ACR，
  **不得移除或改回 quay.io/docker.io**——中国网络下外网源不可达，且版本号含 `+` 后
  添加节点命令必须依赖 override。详见 `lmzj-docs/acr-image-mirror.md`。

## Secret 规则

- 不提交 `.env`、`.env.ssl`、token、password、private key 或真实 SSO client secret。
- 文档只写 GitHub Secrets 和 Variables 名称，不写真实值。
- 如果 secret 已经出现在 git history 或文档中，先要求人类负责人轮换，再继续使用。

## 本地验证

流程脚本或 workflow 变更后运行：

```bash
python -m unittest discover -s scripts/tests
python -m compileall -q scripts
bash -n scripts/deploy-images.sh
```

流程接入核对（只读，WARN 是待核对迹象）：

```bash
python /path/to/company-ai-skills/skills/ai-issue-to-production/scripts/audit_ai_issue_to_production.py \
  --repo . --project-type secondary_development --release-source dev --pr-target dev --focus delivery
```

应用代码变更先跑最小相关检查；风险较高时再扩大到 `make lint`、`make test` 或 `make ci`。
