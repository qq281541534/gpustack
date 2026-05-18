Refs #<issue>

## 摘要

- 

## 变更范围

- 

## 验证

- `<command>` -> 

## 部署影响

- 是否需要重建镜像: yes/no
- 是否新增 GitHub Secrets 或 Variables: yes/no
- 是否需要调整 GitHub L4 门禁或 production environment: yes/no
- 是否需要数据库迁移: yes/no
- 是否需要生产部署: yes/no

## 上游冲突风险

- 本次是否修改 upstream core 文件: yes/no
- 后续同步 `gpustack/gpustack` 的潜在冲突点: 

## 回滚

- 部署上一版完整 40 位 SHA 镜像。

## 发布证据

- Repository visibility: `public`
- Governance level: `L4 platform-enforced`
- Issue:
- PR:
- Merge commit:
- Image tag: `registry.cn-chengdu.aliyuncs.com/lmzjai/gpustack-custom:<full-sha>`
- Deploy workflow:
- Verification:
- LMZJ release docs: `lmzj-docs/github-ai-build-release-flow.md`
