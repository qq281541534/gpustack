# LMZJ GPUStack 发布日志

记录每次生产镜像发布对应的源码基线。镜像 tag = 后端 dev 完整 SHA；前端产物在构建时从
`qq281541534/gpustack-ui` dev 分支打包进镜像（机制见 `hack/install.sh` 本地 UI 优先补丁）。

## 1.1.2 — 2026-08-19（498ab3bf，已部署）

- 后端：无运行时变更（#23 减功能红线规则为文档）。
- 前端：gpustack-ui dev `2358257453f6`（PR #2，Issue #24）——隐藏企业版 teaser：
  计费/组织菜单、API Keys 企业版占位符；分组标签「用量与计费」→「用量」。
- 构建：workflow_dispatch run `32245774248`，`backend_sha=498ab3bf`、
  `frontend_ref=2358257453f6`，digest `sha256:e2ba6f9f66c6…`，audio slim。
- 验证：`127.0.0.1:8080` healthz/readyz 均 200；公网 `/usage/billing` 404；
  UI 指纹 `1787137504579`。deploy 脚本 health_wait 因默认端口指向 nginx（80）
  误报一次，实际部署成功，脚本默认值修复见 Issue #25。
- 回滚：registry 保留上一版 `09bab1fc58fcf…`。

## 1.1.1 — 2026-08-19（09bab1fc，已部署）

- 后端：v2.2.3 同步完成后的 release-log 提交（PR #20），无运行时变更。
- 前端：gpustack-ui dev `5e4c0703`（上游 v2.2.3 前端合并，PR #1），v2.2.0 重设计
  dashboard、GPU 实例管理等新页面随本版上线。
- 验证：healthz/readyz 200，公网 UI 指纹 `1787109827157`。

## 1.1.0 — 2026-08-19（f977d830）

- 后端：合并上游 gpustack v2.2.3（PR #16/#18），生产部署并完成数据移植
  （users→principals 身份整合等，详见后端仓库 Issue #15）。
- 前端：仍为 1.0.0 旧版产物。

## 1.0.0 — 2026-08-18（5fc61020）

- 升级前基线：上游基点 `49f56dab`（2026-05-12 快照），OIDC SSO 定制，
  slim 镜像（audio），生产镜像 `3909c338`。
