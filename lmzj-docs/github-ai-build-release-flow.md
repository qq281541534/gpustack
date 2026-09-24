# GPUStack 构建与发布流程

LMZJ 维护的 GPUStack 二开 fork 的构建、发布、部署和回滚入口。项目画像、持续授权范围和
平台门禁见根目录 `AGENTS.md`；通用交付流程见公司级 skill `ai-issue-to-production`。
GPUStack upstream 原有 `docs/` 保持为上游产品文档目录，LMZJ 专属流程文档放在
`lmzj-docs/`。

## 发布链路

```text
普通文档 / 流程修改：PR → PR check passed → 合并 → 完成（不构建、不部署）

runtime 改动：Issue → 分支 → PR（Refs #issue）→ PR check passed → 合并
  → build-images.yml（push 自动触发）→ deploy-production.yml
  → /healthz、/readyz、公网 UI 验证 → release-log.md 记录 → 关闭 Issue
```

改动范围由 `scripts/classify_change_scope.py` 判定，PR 检查和合并后构建使用同一份规则：

| Scope | 典型路径 | Issue | 构建 |
|---|---|---|---|
| `docs-only` | `README*`、`docs/**`、`lmzj-docs/**`、其他普通 Markdown/图片 | 不需要 | 否 |
| `process-only` | `AGENTS.md`、`CLAUDE.md`、`.trae/**`、PR/Issue 模板、process lint 及其测试 | 系统性改造才需要 | 否 |
| `release-governance` | `.github/workflows/**`、`scripts/deploy-images.sh`、`docker-compose/*.yaml`、`charts/**` | 系统性改造才需要 | 否 |
| `runtime` | `gpustack/**`、`pack/**`、`hack/**`、`static/**`、`docker-compose/grafana/**`、依赖文件、`tests/**` | 需要 | 镜像输入才构建（`tests/**` 不构建） |
| `unknown` | 未映射路径 | 需要 | 是 |

`docker-compose/grafana/**` 会被 `pack/Dockerfile` 复制进镜像，所以按 runtime 构建；其余
compose 文件只影响部署配置，改动后复用既有镜像重新部署即可。

## Workflow 分工

### `.github/workflows/pr-check.yml`

- 触发：PR to `dev`（含编辑 PR 描述后重跑）。
- `Detect change scope`：读取 PR 实际改动文件（含重命名前路径）并分类。
- `PR process lint`：读取实时 PR 描述；禁止 `Closes`/`Fixes`/`Resolves`；runtime/unknown
  要求 `Refs #<issue>` 和完整章节，普通文档与流程改动只要求「修改」「验证」。
- `Repository checks`（非 docs-only）：process 脚本单测、`deploy-images.sh` 语法检查、
  对改动文件运行 pre-commit（flake8、black、shellcheck、check-yaml）。
- `PR check passed`：ruleset 绑定的必需检查。应运行的 job 失败、取消或被意外跳过都会失败；
  docs-only 跳过 `Repository checks` 属于合法跳过。

### `.github/workflows/build-images.yml`

- 触发：push to `dev` 自动触发；也可 `workflow_dispatch` 指定 `backend_sha`。
- push 时先用分类器判断本次合并是否包含镜像输入，没有则不构建。
- 只接受位于 `dev`、关联已合并 PR 的完整 40 位 SHA。
- 前端版本固定在 `pack/frontend-ref`（`qq281541534/gpustack-ui` 完整 SHA），镜像内容由后端
  SHA 唯一确定。更新前端 = 提 PR 修改该文件，合并后产生新的后端 SHA 和新镜像。
- 生产镜像：`registry.cn-chengdu.aliyuncs.com/lmzjai/gpustack-custom:<full-sha>`，
  `GPUSTACK_PACKAGE_EXTRAS=audio`。其他 extras（如 `all`）只能手动触发，tag 为
  `<full-sha>-<extras>`，不可被生产部署 workflow 接受。
- tag 不可变：registry 已存在同名 tag 时复用，不覆盖。Job summary 记录镜像、digest、
  前端 SHA 和是否复用。

### `.github/workflows/deploy-production.yml`

- `workflow_dispatch` 触发，输入完整 SHA `image_tag`；绑定 `environment: production`。
- 部署前校验：SHA 位于 `dev`；registry 中存在该 tag 并解析 digest；读取服务器
  `.lmzj-current-image-tag`，目标版本不比线上新时拒绝，回滚需显式 `rollback=true`。
- `concurrency: deploy-production`：同一时间只有一个生产部署，不取消进行中的部署。
- 同步 `docker-compose/<compose_file>` 到 `PROD_DEPLOY_PATH`，通过 SSH 执行
  `scripts/deploy-images.sh`。
- `deploy-images.sh`：检查 Docker 数据盘剩余空间（默认至少 10 GiB，`MIN_FREE_GB` 可调）→
  pull → 核对 digest → `docker compose up -d --no-build` → 核对运行容器镜像 → 等待
  `/healthz`、`/readyz` → 写入当前 tag → 清理本仓库旧镜像（保留当前和上一版）。
- 拒绝 `latest`、`dev`、版本别名和短 SHA；服务器不构建镜像。

## 部署前检查

每次部署核对当前目标的实时状态；依赖 profile 和 compose 未变化时复用上次审查结论。

- 镜像身份：完整 SHA tag、digest、前端 SHA（build job summary）。
- 目标磁盘：由 `deploy-images.sh` 预检。
- dependency profile：生产 server 为 `audio`。
- compose 有变化时审查：不可变镜像、无 `build:`、secrets、volumes、ports、health checks、
  restart policy 和部署路径。
- 回滚版本：部署前服务器记录的上一版 tag（deploy job summary 输出）。
- 含数据库迁移时：确认上一版镜像能否在新 schema 上运行；不能时按迁移的恢复方案处理。

## 回滚

1. 从 deploy job summary 或 `release-log.md` 找到上一版完整 SHA。
2. 以该 SHA 和 `rollback=true` 触发 `deploy-production.yml`（服务器本地保留上一版镜像，
   通常无需重新下载）。
3. 验证 `/healthz`、`/readyz` 和公网 UI，并在 Issue 和 `release-log.md` 记录。

## 中断恢复

先读 PR、run 和 `release-log.md` 已有记录，只查询未决阶段：

```bash
gh pr view <pr> --json state,headRefOid,baseRefName,mergeCommit,statusCheckRollup
gh run view <run-id> --json status,conclusion,jobs,url,headSha
```

没有 final conclusion 或健康检查证据时记为 `unresolved`，不要重复 dispatch 状态不明的部署。

## GitHub 配置

Production environment secrets：`ALIYUN_ACR_USERNAME`、`ALIYUN_ACR_PASSWORD`、
`PROD_SSH_HOST`、`PROD_SSH_PORT`、`PROD_SSH_USER`、`PROD_SSH_KEY`、`PROD_DEPLOY_PATH`。

Repository variables：`ACR_REGISTRY`、`ACR_NAMESPACE`、`ACR_REPOSITORY`、`FRONTEND_REPOSITORY`。

## 发布记录

每次生产发布在 `release-log.md` 追加一段，引用已有 run，不另建证据文档：

```markdown
## <版本> — <日期>（<short-sha>，已部署）

- 后端 / 前端：<PR、Issue、前端 SHA>
- 构建：<build run>，digest `<sha256:…>`
- 部署：<deploy run>
- 验证：<healthz/readyz、公网 UI>
- 回滚：<上一版完整 SHA>
```
