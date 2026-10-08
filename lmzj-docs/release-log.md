# LMZJ GPUStack 发布日志

记录每次生产镜像发布对应的源码基线。镜像 tag = 后端 dev 完整 SHA；前端产物在构建时从
`qq281541534/gpustack-ui` dev 分支打包进镜像（机制见 `hack/install.sh` 本地 UI 优先补丁）。

## 1.2.0 — 2026-10-09（fce055ee，已部署）

- 后端：依赖钉版 + uv.lock 重生成（PR #44/#45，Issue #41）——`sqlalchemy<2.1`、
  `pydantic<2.14`、`alembic<1.20`、`uvicorn<0.53`。根因：换 logo 镜像 `06112376`
  首次部署即崩（healthz 300s 不恢复），本地容器复现实锤为 10 月冷构建依赖漂移——
  SQLAlchemy 2.1 对默认 `postgresql://` 不再回落 psycopg2（镜像内仅 psycopg2-binary），
  alembic 同步迁移引擎抛 `No module named 'psycopg'`。钉版取 8 月生产验证过的 minor。
  镜像 `uv pip install` 安装 wheel 时不消费 uv.lock，锁文件仅保证 `uv lock --locked`
  通过；彻底修复（安装走锁）另行治理。
- 前端：gpustack-ui dev `466c63a9`（PR #4，Issue #41）——公司新 logo「流动内核」全面
  切换：favicon 换真 ICO（新文件名 `favicon-lmzj.ico` 防浏览器缓存）；登录页/侧边栏
  展开态/版本弹窗用 lockup 横版（浅色 primary、深色 reverse 按主题）；折叠态与
  16x16 路由图标用透明底 symbol；删除无引用死资产；摩尔线程厂商 logo 不动。
- 流程：`deploy-images.sh` 新增低磁盘「删除优先」回退（PR #43，负责人授权
  「先删镜像容器再拉取」）：磁盘 <10 GiB 时先停容器、删本仓库本地镜像再拉取，
  数据卷永不触碰；代价是停机拉取（本次实测约 10 分钟）且回滚需重新拉取。
- 构建：`06112376`（run 37794127022；首跑 37765294792 在 Docker 步骤停滞
  232 分钟、ACR 无产物，取消重派）、`297f5fe0`（uv.lock 未同步快速失败）、
  `fce055ee`（run 37809992455，5 分钟热缓存成功）。
- 部署：`fce055ee`（run 37811046849）成功。期间 `06112376` 部署失败
  （run 37801813969）→ 回滚 `498ab3bf`（run 37806126277）恢复 → 修复版上线。
- 验证：部署前本地容器预检（healthz/readyz 200、依赖组合 2.0.54/2.13.5/
  1.19.2/0.52.4、新 UI favicon 引用）；上线后 healthz/readyz 200，公网登录页
  深浅双主题截图验收（reverse/primary 均清晰居中无变形）。
- 回滚：registry 保留上一版 `498ab3bf`（本地副本已随删除优先清理，回滚
  = rollback=true 重新拉取，约 10 分钟）。

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
