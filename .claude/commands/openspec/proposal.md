---
name: OpenSpec: 提案
description: 创建新的OpenSpec变更并进行严格验证。
category: OpenSpec
tags: [openspec, change]
---
<!-- OPENSPEC:START -->
**防护原则**
- 优先采用直接、最小化的实现，仅在请求或明确需要时增加复杂性。
- 保持变更范围与请求结果紧密匹配。
- 如需额外的OpenSpec约定或澄清，请参考 `openspec/AGENTS.md`（位于 `openspec/` 目录内——如果看不到，运行 `ls openspec` 或 `openspec update`）。
- 识别任何模糊或含糊的细节，在编辑文件前提出必要的后续问题。

**步骤**
1. 审查 `openspec/project.md`，运行 `openspec list` 和 `openspec list --specs`，并检查相关代码或文档（例如通过 `rg`/`ls`），将提案基于当前行为；记录需要澄清的任何空白。
2. 选择唯一的动词开头的 `change-id`，并在 `openspec/changes/<id>/` 下搭建 `proposal.md`、`tasks.md` 和 `design.md`（需要时）。
3. 将变更映射到具体功能或需求，将多范围工作分解为具有清晰关系和排序的不同规范增量。
4. 当解决方案跨越多个系统、引入新模式或在提交规范前需要权衡讨论时，在 `design.md` 中记录架构推理。
5. 在 `changes/<id>/specs/<capability>/spec.md`（每个功能一个文件夹）中起草规范增量，使用 `## ADDED|MODIFIED|REMOVED Requirements`，每个需求至少包含一个 `#### Scenario:`，并在相关时交叉引用相关功能。
6. 将 `tasks.md` 起草为提供用户可见进展的小型、可验证工作项的有序列表，包括验证（测试、工具），并突出依赖项或可并行的工作。
7. 使用 `openspec validate <id> --strict` 验证并在分享提案前解决每个问题。

**参考**
- 当验证失败时，使用 `openspec show <id> --json --deltas-only` 或 `openspec show <spec> --type spec` 检查详情。
- 在编写新需求前，使用 `rg -n "Requirement:|Scenario:" openspec/specs` 搜索现有需求。
- 使用 `rg <keyword>`、`ls` 或直接文件读取探索代码库，使提案与当前实现现实保持一致。
<!-- OPENSPEC:END -->
