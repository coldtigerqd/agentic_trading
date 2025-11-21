# Spec: Documentation Localization (文档本地化)

## ADDED Requirements

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

## 系统概述

Agentic AlphaHive 是一个无头（Headless）、非交互式的量化交易运行时环境...

## 核心特性

- 🧠 **递归智能体架构**: 指挥官(Commander) + Alpha蜂群(Swarm)
- 🛡️ **独立安全层**: 硬编码风险限额，独立于AI决策
- 📊 **实时数据同步**: ThetaData REST API集成

## 快速开始

### 1. 环境准备
```bash
# 克隆仓库
git clone ...
```

---

## English Documentation

System Overview in English...
```

**Validation**:
- Render README.md in GitHub preview
- Verify Chinese sections are clear and complete
- Confirm English sections maintain original clarity
- Check all links work (both Chinese and English anchors)

---

### Requirement: Full Chinese QUICKSTART Guide

The QUICKSTART.md file MUST be fully translated to Chinese with step-by-step instructions.

**Rationale**: Quick start guides are action-oriented. Chinese-speaking users need Chinese instructions to set up the system efficiently.

#### Scenario: New user follows QUICKSTART to set up system

**Given** a Chinese-speaking user with no prior knowledge of the system
**When** they follow the QUICKSTART.md guide
**Then**:
- All section headings MUST be in Chinese
- All step descriptions MUST be in Chinese
- All code examples MUST have Chinese comments
- All troubleshooting tips MUST be in Chinese
- Command outputs MUST have Chinese explanations

**Example Transformation**:
```markdown
# Before
# Quick Start Guide

## Prerequisites
- Python 3.11+
- Interactive Brokers account
- ThetaData subscription

## Setup Steps

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment
Create a `.env` file with your API keys...

# After
# 快速开始指南

## 前置条件
- Python 3.11+
- Interactive Brokers 账户
- ThetaData 订阅

## 设置步骤

### 1. 安装依赖
```bash
# 安装Python依赖包
pip install -r requirements.txt
```

### 2. 配置环境变量
创建 `.env` 文件并添加您的API密钥...
```

**Validation**:
- Have a Chinese-speaking tester follow the guide from scratch
- Verify each step is clear and actionable
- Confirm no English-only blockers exist
- Check all commands execute successfully

---

### Requirement: Preserve CLAUDE.md Bilingual Instructions

The CLAUDE.md file (project instructions for AI assistants) MUST remain bilingual with minimal changes.

**Rationale**: CLAUDE.md already contains bilingual instructions. Maintaining this format ensures compatibility with both Chinese and English AI assistants.

#### Scenario: AI assistant reads project instructions

**Given** Claude Code loads the CLAUDE.md file
**When** the AI processes project instructions
**Then**:
- The OpenSpec instructions MUST remain in English (managed by OpenSpec framework)
- The custom instructions (e.g., prompt references) MUST remain in original language
- Chinese sections MUST be preserved as-is
- No functional changes to AI behavior MUST occur

**Change Scope**:
```markdown
# Minimal changes - only update references if needed
- @prompts/commander_system.md 请开始一轮分析吧
# This line can be updated to reflect Chinese prompt if needed
```

**Validation**:
- Load CLAUDE.md in Claude Code
- Verify AI assistant understands instructions
- Confirm no parsing errors occur
- Test that custom slash commands still work

---

### Requirement: Chinese Inline Code Comments in User-Facing Modules

Critical user-facing modules MUST have Chinese inline comments for complex logic.

**Rationale**: Code comments help developers understand intent. Chinese comments reduce cognitive load for Chinese-speaking contributors.

#### Scenario: Developer reads complex validation logic

**Given** a developer reviews the `place_order_with_guard()` function
**When** they encounter complex validation logic (e.g., concentration limit check)
**Then**:
- High-level logic explanations MUST be in Chinese
- Technical implementation details MAY remain in English
- Algorithm references (e.g., Kelly criterion) MAY remain in English
- Variable names and function names MUST remain in English

**Example Transformation**:
```python
# Before
# Check if adding this position would exceed concentration limit
# Concentration = (existing_position_value + new_position_value) / total_portfolio_value
# Limit: 30% per symbol
if concentration > 0.30:
    return OrderResult(success=False, error="Concentration limit exceeded")

# After
# 检查添加该仓位是否会超过集中度限额
# 集中度 = (现有仓位价值 + 新仓位价值) / 投资组合总价值
# 限额: 每个标的不超过30%
if concentration > 0.30:
    return OrderResult(success=False, error="仓位集中度超限 (CONCENTRATION_EXCEEDED)")
```

**Scope**:
- `skills/execution_gate.py`: Order validation logic
- `skills/data_quality.py`: Data quality checks
- `skills/swarm_core.py`: Swarm orchestration
- `mcp-servers/ibkr/safety.py`: Safety limits enforcement

**Validation**:
- Code review for comment clarity
- Verify comments align with code behavior
- Confirm no misleading translations

---

## MODIFIED Requirements

None. This is a new localization capability with no modifications to existing specs.

---

## REMOVED Requirements

None. No existing functionality is removed, only translated.
