# Spec: Prompts & Templates Localization (提示词与模板本地化)

## ADDED Requirements

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

## Your Role
- **Market Sensing**: Query account state and market conditions
- **Swarm Orchestration**: Invoke concurrent sub-agents for analysis

## Trading Workflow
Execute this cycle on every invocation:

### 1. SENSE: Market & Account State
```python
from skills import sync_watchlist_incremental
sync_info = sync_watchlist_incremental()
```

# After Translation
您是**指挥官**（Commander），交易系统的中央协调者。

## 您的职责
- **市场感知**：查询账户状态和市场状况
- **蜂群协调**：调用并发子智能体进行分析

## 交易工作流
每次调用时执行此循环:

### 1. 感知: 市场与账户状态
```python
from skills import sync_watchlist_incremental
sync_info = sync_watchlist_incremental()
```
```

**Validation**:
- Run Commander with Chinese prompt via Claude Code
- Verify LLM generates coherent Chinese reasoning
- Confirm all code snippets execute without errors

---

### Requirement: Swarm Strategy Templates in Chinese

All 5 swarm strategy templates MUST be fully translated to Chinese, including strategy descriptions, analysis frameworks, and decision criteria.

**Rationale**: Swarm templates define trading logic. Chinese-language templates make strategies more accessible to Chinese analysts and enable faster iteration.

#### Scenario: Swarm agent generates signal with Chinese explanation

**Given** a swarm strategy template (e.g., `trend_scout.md`) is localized to Chinese
**When** the `consult_swarm()` function invokes the strategy
**Then**:
- The rendered prompt MUST be in Chinese
- Jinja2 template variables (e.g., `{{ symbol_pool }}`) MUST remain unchanged
- The LLM response MUST include Chinese reasoning in the `reasoning` field
- The JSON signal structure MUST remain unchanged
- Technical indicators (e.g., "MACD", "RSI") MUST retain English abbreviations

**Example Input** (from `swarm_intelligence/templates/trend_scout.md`):
```markdown
# Before Translation
# Trend Scout Strategy

You are a specialized options trading analyst focused on trend-following.

## Your Role
Analyze multi-timeframe data to identify strong trends.

## Analysis Framework
### 1. Multi-Timeframe Trend Confirmation
Use the following indicators:
- **20-day SMA**: {{ sma_period }} period
- **RSI**: Look for {{ rsi_low }}-{{ rsi_high }} pullbacks

# After Translation
# 趋势侦察策略

您是一位专注于趋势跟踪的期权交易分析师。

## 您的职责
分析多时间周期数据以识别强劲趋势。

## 分析框架
### 1. 多时间周期趋势确认
使用以下指标:
- **20日简单移动平均线（SMA）**: {{ sma_period }} 周期
- **相对强弱指数（RSI）**: 寻找 {{ rsi_low }}-{{ rsi_high }} 回调
```

**Validation**:
- Execute `consult_swarm(sector="TECH")` with Chinese template
- Verify swarm generates signals with Chinese `reasoning` field
- Confirm JSON output structure matches schema

---

### Requirement: Preserve Jinja2 Template Syntax

All Jinja2 template variables and control structures MUST remain syntactically valid after translation.

**Rationale**: Template rendering depends on exact variable names. Changing `{{ symbol_pool }}` to `{{ 符号池 }}` would break template rendering.

#### Scenario: Template rendering succeeds with translated content

**Given** a swarm template with Jinja2 variables (e.g., `{{ trend_strength_threshold }}`)
**When** the template is translated to Chinese
**And** the template is rendered with parameter values
**Then**:
- All `{{ variable }}` syntax MUST remain unchanged
- All `{% if %}` and `{% for %}` control structures MUST remain unchanged
- Surrounding Chinese text MUST render correctly
- No template syntax errors MUST occur

**Example**:
```jinja2
# Correct
您的趋势强度阈值设定为: {{ trend_strength_threshold }}

# Incorrect (DO NOT translate variable names)
您的趋势强度阈值设定为: {{ 趋势强度阈值 }}  ❌
```

**Validation**:
- Run `jinja2.Template(content).render(params)` for each translated template
- Verify no `TemplateError` exceptions occur
- Confirm rendered output contains correct parameter values

---

## MODIFIED Requirements

None. This is a new localization capability with no modifications to existing specs.

---

## REMOVED Requirements

None. No existing functionality is removed, only translated.
