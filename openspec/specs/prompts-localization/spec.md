# prompts-localization Specification

## Purpose
TBD - created by archiving change localize-to-chinese. Update Purpose after archive.
## Requirements
### Requirement: Commander System Prompt in Chinese

The Commander system prompt MUST be fully translated to Chinese while preserving all technical functionality and code examples.

**Rationale**: The Commander is the central decision-maker. Chinese-language prompts enable Chinese-speaking operators to understand system reasoning and debug behavior more effectively.

#### Scenario: Commander executes trading workflow with Chinese instructions

**Given** the Commander system prompt is localized to Chinese
**When** the Commander executes a full SENSE-THINK-DECIDE-ACT cycle
**Then**:
- The Commander's reasoning output MUST be in Chinese
- All instructions (e.g., "感知市场状态", "调用蜂群智能") MUST be translated
- Python code examples MUST remain syntactically valid
- Function signatures and variable names MUST remain in English
- Technical terms (e.g., "PUT_SPREAD", "OHLC") MUST retain English terminology
- The Commander MUST successfully invoke skills and generate orders

**Example Input** (from `prompts/commander_system.md`):
```markdown
# Before Translation
You are the **Commander**, the central orchestrator of the trading system.

