# documentation-localization Specification

## Purpose
TBD - created by archiving change localize-to-chinese. Update Purpose after archive.
## Requirements
### Requirement: Bilingual README with Chinese Primary

The README.md file MUST provide a comprehensive bilingual experience with Chinese as the primary language for high-level content.

**Rationale**: README is the first touchpoint for users. Bilingual format accommodates both Chinese and English speakers while prioritizing Chinese users.

#### Scenario: Chinese user reads system overview

**Given** a Chinese-speaking user opens the README.md file
**When** they read the introduction and feature list
**Then**:
- The main heading MUST be bilingual (e.g., "Agentic AlphaHive Runtime | 智能交易运行时")
- The system overview MUST be in Chinese
- Core features MUST be described in Chinese
- Technical setup commands MUST be in English with Chinese annotations
- Architecture diagrams MUST have Chinese labels

**Example Structure**:
```markdown
# Agentic AlphaHive Runtime | 智能交易运行时

**基于 Claude Code 的递归式自治交易系统**

[English documentation follows below | 英文文档在下方]

