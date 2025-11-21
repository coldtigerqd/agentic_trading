---
name: OpenSpec: 应用
description: 实施已批准的OpenSpec变更并保持任务同步。
category: OpenSpec
tags: [openspec, apply]
---
<!-- OPENSPEC:START -->
**防护原则**
- 优先采用直接、最小化的实现，仅在请求或明确需要时增加复杂性。
- 保持变更范围与请求结果紧密匹配。
- 如需额外的OpenSpec约定或澄清，请参考 `openspec/AGENTS.md`（位于 `openspec/` 目录内——如果看不到，运行 `ls openspec` 或 `openspec update`）。

**步骤**
将这些步骤作为TODO并逐一完成。
1. 阅读 `changes/<id>/proposal.md`、`design.md`（如果存在）和 `tasks.md` 以确认范围和验收标准。
2. 顺序处理任务，保持编辑最小化并专注于请求的变更。
3. 在更新状态前确认完成——确保 `tasks.md` 中的每个项目都已完成。
4. 在所有工作完成后更新检查清单，使每个任务标记为 `- [x]` 并反映实际情况。
5. 需要额外上下文时，参考 `openspec list` 或 `openspec show <item>`。

**参考**
- 如果在实施过程中需要提案的额外上下文，使用 `openspec show <id> --json --deltas-only`。
<!-- OPENSPEC:END -->
