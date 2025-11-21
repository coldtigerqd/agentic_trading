---
name: OpenSpec: 归档
description: 归档已部署的OpenSpec变更并更新规范。
category: OpenSpec
tags: [openspec, archive]
---
<!-- OPENSPEC:START -->
**防护原则**
- 优先采用直接、最小化的实现，仅在请求或明确需要时增加复杂性。
- 保持变更范围与请求结果紧密匹配。
- 如需额外的OpenSpec约定或澄清，请参考 `openspec/AGENTS.md`（位于 `openspec/` 目录内——如果看不到，运行 `ls openspec` 或 `openspec update`）。

**步骤**
1. 确定要归档的变更ID：
   - 如果此提示已包含特定的变更ID（例如在由斜杠命令参数填充的 `<ChangeId>` 块内），请在修剪空白字符后使用该值。
   - 如果对话松散地引用了变更（例如通过标题或摘要），运行 `openspec list` 显示可能的ID，分享相关候选项，并确认用户意图选择哪一个。
   - 否则，审查对话，运行 `openspec list`，并询问用户要归档哪个变更；在继续之前等待确认的变更ID。
   - 如果您仍然无法识别单个变更ID，请停止并告诉用户您还不能归档任何内容。
2. 通过运行 `openspec list`（或 `openspec show <id>`）验证变更ID，如果变更丢失、已归档或以其他方式未准备好归档，则停止。
3. 运行 `openspec archive <id> --yes`，使CLI移动变更并应用规范更新而无需提示（仅对工具专用工作使用 `--skip-specs`）。
4. 审查命令输出以确认目标规范已更新且变更已移至 `changes/archive/`。
5. 使用 `openspec validate --strict` 验证，如果看起来有异常，使用 `openspec show <id>` 检查。

**参考**
- 在归档前使用 `openspec list` 确认变更ID。
- 使用 `openspec list --specs` 检查刷新的规范，并在移交前解决任何验证问题。
<!-- OPENSPEC:END -->
