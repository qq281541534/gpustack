<!--
普通文档 / 小型流程修改：只填「修改」「验证」；没有相关 Issue 时删除 Refs 行。
运行时改动（gpustack/、pack/、hack/、依赖、镜像输入、tests/ 等）：保留 Refs 并填写全部章节。
不要使用 Closes / Fixes / Resolves，生产 Issue 在上线验证后由 AI 关闭。
-->
Refs #<issue>

## 修改

<改了什么以及原因。>

## 验证

- `<command>` -> <结果>

## 发布影响

- Scope: <runtime | release-governance | process-only | mixed>
- 构建/部署：<需要新镜像 / 沿用既有镜像 / 不部署>
- 数据迁移、Secrets/Variables：<仅涉及时填写>

## 上游冲突风险

<是否修改 upstream core；后续同步 `gpustack/gpustack` 的潜在冲突点。>

## 回滚

<部署上一版完整 SHA 镜像（rollback=true）；流程改动 revert PR。>
