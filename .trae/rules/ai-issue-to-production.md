---
alwaysApply: true
---

# Trae AI Issue-to-Production Rules

Trae 在本仓库中是 AI agent 入口之一。所有 issue、branch、PR、CI/CD、release、
deployment、rollback 工作必须读取并遵守：

- `AGENTS.md`
- 公司级 skill 源仓库 `company-ai-skills/skills/ai-issue-to-production/SKILL.md`
- `company-ai-skills/skills/ai-issue-to-production/references/` 下的相关文件

本项目是 `secondary_development`：从 `dev` 创建分支，PR target 是 `dev`，生产镜像来源是
`dev`。PR 使用 `Refs #<issue>`，不得使用 auto-close keywords。没有人类明确确认，不触发
生产部署。
