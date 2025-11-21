# Design: Chinese Localization Architecture

## Overview (概述)

This design outlines the architectural approach for comprehensively localizing the Agentic AlphaHive Runtime system to Chinese while maintaining code quality, debugging capability, and international collaboration standards.

## Translation Strategy (翻译策略)

### Terminology Classification (术语分类)

We categorize all text content into three translation approaches:

| Category | Approach | Examples |
|----------|----------|----------|
| **Domain Terms** | Keep English | PUT_SPREAD, OHLC, MACD, RSI, VIX |
| **System Concepts** | Translate | Commander → 指挥官, Swarm → 蜂群, Signal → 信号 |
| **User Messages** | Full Chinese | Error messages, status updates, prompts |

### Standard Translations (标准译名)

Establish consistent terminology across all components:

```yaml
# Core System Components
Commander: 指挥官
Alpha Swarm: Alpha蜂群 (or 阿尔法蜂群)
Swarm Intelligence: 蜂群智能
Agent: 智能体 (or Agent, context-dependent)
Skill: 技能
MCP Server: MCP服务器

# Trading Concepts
Signal: 信号
Strategy: 策略
Risk: 风险
Portfolio: 投资组合
Position: 持仓
Order: 订单
Trade: 交易

# Workflow States
SENSE: 感知
THINK: 思考
DECIDE: 决策
ACT: 行动

# Data Quality
Fresh Data: 新鲜数据
Stale Data: 过期数据
Snapshot: 快照
Validation: 验证

# Safety & Limits
Safety Layer: 安全层
Circuit Breaker: 熔断机制
Watchdog: 看门狗
Rejection: 拒绝
```

## Implementation Approach (实现方式)

### Phase 1: Prompts & Templates (提示词与模板)

**Files to Modify**:
- `prompts/commander_system.md`
- `swarm_intelligence/templates/*.md` (5 files)

**Approach**:
1. Translate all natural language instructions to Chinese
2. Keep code examples and function signatures in English
3. Preserve Jinja2 template variables unchanged (e.g., `{{ symbol_pool }}`)
4. Add translation notes for ambiguous terms

**Example Transformation**:

```markdown
# Before
You are the **Commander**, the central orchestrator of the trading system.

## Your Role
- **Market Sensing**: Query account state and market conditions

# After
您是**指挥官**（Commander），交易系统的中央协调者。

## 您的职责
- **市场感知**：查询账户状态和市场状况
```

**Testing Strategy**:
- Run Commander workflow with Chinese prompt
- Verify LLM reasoning is coherent and actionable
- Check that code generation (Python snippets) remains valid

### Phase 2: Skills Output (技能输出)

**Files to Modify**:
- `skills/*.py` (14 files)
- Focus: `print()`, `logger.*()`, function docstrings

**Approach**:
1. Replace English print statements with Chinese equivalents
2. Keep variable names, function names, and code structure in English
3. Translate docstring descriptions while keeping parameter names English
4. Add encoding declarations if needed (`# -*- coding: utf-8 -*-`)

**Example Transformation**:

```python
# Before
print(f"✅ {symbol}: Fresh data @ {result['timestamp']}")
logger.error(f"Failed to fetch {symbol}: {e}")

# After
print(f"✅ {symbol}: 新鲜数据 @ {result['timestamp']}")
logger.error(f"获取数据失败 {symbol}: {e}")
```

**Docstring Strategy**:
```python
# Before
def place_order_with_guard(symbol: str, strategy: str) -> OrderResult:
    """
    Place order with safety validation.

    Args:
        symbol: Underlying ticker
        strategy: Strategy name

    Returns:
        OrderResult with status and trade_id
    """

# After
def place_order_with_guard(symbol: str, strategy: str) -> OrderResult:
    """
    通过安全验证层提交订单。

    Args:
        symbol: 标的代码（如 "AAPL"）
        strategy: 策略名称（如 "PUT_SPREAD"）

    Returns:
        OrderResult 包含状态和交易ID
    """
```

**Testing Strategy**:
- Run each skill function independently
- Verify output messages are readable and properly formatted
- Check no encoding errors in terminal/logs

### Phase 3: Validation & Error Messages (验证与错误消息)

**Files to Modify**:
- `skills/execution_gate.py`
- `mcp-servers/ibkr/safety.py`
- `skills/data_quality.py`

**Approach**:
1. Translate all user-facing error messages
2. Include English error codes for debugging (e.g., `RISK_EXCEEDED`)
3. Keep exception class names in English
4. Translate validation explanations

**Example Transformation**:

```python
# Before
return OrderResult(
    success=False,
    error="Trade risk $600 exceeds max_trade_risk limit of $500"
)

# After
return OrderResult(
    success=False,
    error="交易风险 $600 超过最大交易风险限额 $500 (RISK_EXCEEDED)"
)
```

**Error Code Strategy**:
```python
# Standardized error codes (kept in English for grep-ability)
ERROR_CODES = {
    "RISK_EXCEEDED": "交易风险超限",
    "CAPITAL_EXCEEDED": "资金需求超限",
    "CONCENTRATION_EXCEEDED": "仓位集中度超限",
    "DRAWDOWN_TRIGGERED": "触发回撤熔断",
    "MARKET_CLOSED": "市场已关闭"
}
```

**Testing Strategy**:
- Trigger each validation scenario
- Verify error messages are clear and actionable
- Ensure English error codes are still grep-able in logs

### Phase 4: Documentation (文档)

**Files to Modify**:
- `README.md` (bilingual, Chinese-primary)
- `QUICKSTART.md` (full Chinese)
- `CLAUDE.md` (keep as-is, it's already bilingual)

**Approach**:
1. **README.md**: Translate high-level overview and feature descriptions to Chinese, keep setup commands in English with Chinese annotations
2. **QUICKSTART.md**: Full Chinese walkthrough with code examples
3. Add English sections for technical troubleshooting (e.g., "Common Setup Issues")

**Structure for Bilingual Docs**:
```markdown
# Agentic AlphaHive Runtime | 智能交易运行时

[中文说明在后 | English follows]

## English Section
[Original English content...]

---

## 中文说明

系统概述...
```

**Testing Strategy**:
- Verify markdown rendering in GitHub
- Test code snippets from documentation
- Ensure no broken links

## File Organization (文件组织)

No new files or directories needed. All changes are in-place translations.

### Modified Files Summary

```
prompts/
  commander_system.md         [TRANSLATE: Full Chinese]

swarm_intelligence/templates/
  trend_scout.md              [TRANSLATE: Full Chinese]
  vol_sniper.md               [TRANSLATE: Full Chinese]
  mean_reversion.md           [TRANSLATE: Full Chinese]
  breakout_scout.md           [TRANSLATE: Full Chinese]
  correlation_arbitrage.md    [TRANSLATE: Full Chinese]

skills/
  swarm_core.py               [TRANSLATE: Logs & docstrings]
  execution_gate.py           [TRANSLATE: Error messages & docstrings]
  data_quality.py             [TRANSLATE: Validation messages]
  market_data.py              [TRANSLATE: Logs & docstrings]
  data_sync.py                [TRANSLATE: Logs]
  technical_indicators.py     [TRANSLATE: Docstrings]
  market_calendar.py          [TRANSLATE: Status messages]
  watchlist_manager.py        [TRANSLATE: Logs]
  math_core.py                [TRANSLATE: Docstrings]
  mcp_bridge.py               [TRANSLATE: Error messages]
  commander_workflow.py       [TRANSLATE: Logs]
  signal_enrichment.py        [TRANSLATE: Validation messages]
  thetadata_client.py         [TRANSLATE: Error logs]

mcp-servers/ibkr/
  safety.py                   [TRANSLATE: Rejection messages]

docs/
  README.md                   [TRANSLATE: Bilingual]
  QUICKSTART.md               [TRANSLATE: Full Chinese]
```

## Technical Considerations (技术考虑)

### Character Encoding

Ensure UTF-8 encoding throughout:
```python
# Add to top of Python files if needed
# -*- coding: utf-8 -*-
```

Verify `.gitattributes` specifies UTF-8:
```
*.py text eol=lf encoding=utf-8
*.md text eol=lf encoding=utf-8
```

### Terminal Output Testing

Test on common terminals:
- macOS Terminal.app
- iTerm2
- Windows Terminal (if applicable)
- Linux xterm/konsole

Verify:
- ✅ Chinese characters render correctly
- ✅ Emojis (✅, ❌, ⚠️) work
- ✅ Box-drawing characters align properly

### Logging Considerations

Ensure log parsers handle Chinese:
```python
# Good: Structured logging with English keys
logger.info("data_sync_complete", symbol=symbol, bars_added=count,
            message="数据同步完成")

# Avoid: Pure Chinese log keys (harder to grep)
logger.info({"符号": symbol, "新增数据条数": count})  # Not recommended
```

### Git Diff Readability

Chinese characters may affect `git diff` display:
- Use `git diff --word-diff=color` for better Chinese diff viewing
- Consider adding `.gitattributes` rules for better diffing

## Validation Plan (验证计划)

### Automated Tests

No new tests needed, but verify existing tests pass:
```bash
# Run existing test suite
pytest skills/tests/
pytest mcp-servers/ibkr/tests/

# Verify no encoding errors
python3 -c "import skills; print('UTF-8 OK')"
```

### Manual Validation Checklist

1. **Commander Workflow**:
   - [ ] Run Commander cycle with Chinese prompt
   - [ ] Verify reasoning output is coherent
   - [ ] Check code generation remains valid

2. **Swarm Execution**:
   - [ ] Consult swarm with Chinese templates
   - [ ] Verify signal generation with Chinese explanations
   - [ ] Check JSON output structure unchanged

3. **Skills Output**:
   - [ ] Trigger each skill function
   - [ ] Verify Chinese messages display correctly
   - [ ] Check no encoding errors in logs

4. **Error Handling**:
   - [ ] Trigger safety validator rejections
   - [ ] Verify error messages are clear
   - [ ] Check English error codes present

5. **Documentation**:
   - [ ] Render README.md in browser
   - [ ] Test QUICKSTART.md walkthrough
   - [ ] Verify code examples work

## Rollback Strategy (回滚策略)

If issues arise, rollback is straightforward:
1. Revert branch: `git checkout main`
2. No schema changes means no data migration needed
3. No API changes means no client compatibility issues

## Future Enhancements (未来改进)

This design supports future i18n work:
1. **Configuration-based language selection**:
   ```python
   # config.yaml
   language: zh-CN  # or en-US
   ```

2. **Separate translation files**:
   ```
   locales/
     zh-CN.json  # Chinese translations
     en-US.json  # English (default)
   ```

3. **Runtime language switching**:
   ```python
   from skills.i18n import _
   print(_("order_rejected", risk=600, limit=500))
   ```

However, these are out of scope for this change. Current approach is **hard-coded Chinese** for simplicity and immediate value.

## Performance Impact (性能影响)

**Expected**: Negligible
- String translations do not affect algorithmic complexity
- No additional runtime dependencies
- No changes to data structures or API calls

**Monitoring**: Track Commander cycle latency before/after to confirm no regression.

## Security & Safety (安全性)

**No security impact**:
- Translation does not affect validation logic
- Safety limits remain hard-coded in `safety.py`
- Order validation unchanged (only error messages translated)

**Safety validation**:
- All rejection scenarios tested with Chinese messages
- English error codes preserved for audit trail grep-ability
