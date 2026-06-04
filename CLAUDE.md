# GPUStack Claude Agent Loader

## AI Issue to Production

所有 issue、branch、PR、CI/CD、release、image build、production deploy、rollback 工作都使用
`ai-issue-to-production`。生产相关工作开始前读取：

- `AGENTS.md`
- 公司级 skill 源仓库 `company-ai-skills/skills/ai-issue-to-production/SKILL.md`
- `company-ai-skills/skills/ai-issue-to-production/references/` 下的相关文件

本项目是 `secondary_development`：从 `dev` 创建分支，PR target 是 `dev`，生产镜像来源是
`dev`。PR 使用 `Refs #<issue>`，不得使用 `Closes`、`Fixes`、`Resolves` 自动关闭 Issue。
没有人类明确确认，不触发生产部署；生产部署、验证和回滚准备证据齐全后，AI 可按人类明确指令关闭 Issue。
