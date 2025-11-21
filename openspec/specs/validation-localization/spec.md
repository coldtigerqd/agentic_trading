# validation-localization Specification

## Purpose
TBD - created by archiving change localize-to-chinese. Update Purpose after archive.
## Requirements
### Requirement: Safety Validator Rejection Messages in Chinese

All safety validator rejection messages MUST be translated to Chinese with English error codes preserved for audit trail.

**Rationale**: Safety rejections are critical operator feedback. Chinese messages enable faster comprehension and response to rejected orders.

#### Scenario: Order rejected for exceeding risk limit

**Given** the `place_order_with_guard()` function receives an order
**When** the safety validator rejects the order because trade risk exceeds max_trade_risk limit
**Then**:
- The `OrderResult.error` field MUST contain a Chinese error message
- The error message MUST include an English error code (e.g., "RISK_EXCEEDED")
- The actual risk value and limit MUST be displayed
- The error MUST be logged for audit trail

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

**Validation**:
- Submit order with risk > $500
- Verify Chinese error message displays
- Confirm error code "RISK_EXCEEDED" is present for grep
- Check `trades.db` logs contain rejection reason

---

### Requirement: Data Quality Validation Messages in Chinese

All data quality validation messages MUST be translated to Chinese with structured validation reports.

**Rationale**: Data quality checks gate swarm consultation. Chinese messages help operators quickly identify and resolve data issues.

#### Scenario: Data quality pre-flight check fails

**Given** the `consult_swarm()` function performs data quality validation
**When** validation detects stale data or missing bars
**Then**:
- The validation summary MUST be in Chinese
- Issue descriptions MUST be in Chinese with symbol names preserved
- Severity levels (CRITICAL, HIGH) MUST be translated
- Recommendations MUST be in Chinese

**Example Transformation**:
```python
# Before
print(f"⚠️  DATA QUALITY VALIDATION FAILED")
print(f"Summary: {validation['summary']}")
print(f"  CRITICAL ({len(critical_issues)}):")
print(f"    - {issue['symbol']}: {issue['issue']} ({issue['detail']})")
print(f"Recommendations:")
print(f"  → {rec}")

# After
print(f"⚠️  数据质量验证失败")
print(f"概要: {validation['summary']}")
print(f"  严重 ({len(critical_issues)}):")
print(f"    - {issue['symbol']}: {issue['issue']} ({issue['detail']})")
print(f"建议:")
print(f"  → {rec}")
```

**Validation**:
- Trigger data quality failure (e.g., disconnect ThetaData)
- Verify Chinese validation report displays
- Confirm recommendations are actionable
- Check swarm aborts with NO_TRADE signals

---

### Requirement: Order Validation Error Messages in Chinese

All order validation errors (invalid strikes, missing parameters, malformed legs) MUST be translated to Chinese.

**Rationale**: Order validation errors indicate configuration issues. Chinese messages help operators debug strategy parameters faster.

#### Scenario: Order validation fails for missing contract type

**Given** an order leg is missing the `contract_type` field
**When** the `place_order_with_guard()` function validates the order
**Then**:
- The validation error MUST be in Chinese
- The missing field name MUST be highlighted
- The leg index MUST be specified
- The error MUST suggest corrective action

**Example Transformation**:
```python
# Before
raise ValueError(f"Leg {i}: Missing required field 'contract_type'")

# After
raise ValueError(f"订单腿 {i}: 缺少必需字段 'contract_type' (请指定 'PUT' 或 'CALL')")
```

**Validation**:
- Submit order with missing `contract_type`
- Verify Chinese error message with corrective hint
- Confirm exception traceback is readable
- Check error log contains full details

---

### Requirement: Standardized Error Codes for Grep-ability

All error messages MUST include English error codes in parentheses to enable log searching.

**Rationale**: Operators need to quickly find related errors in logs using `grep`. English error codes provide consistent search terms.

#### Scenario: Search logs for specific error type

**Given** the system has logged multiple errors in Chinese
**When** an operator searches logs using `grep "CAPITAL_EXCEEDED"`
**Then**:
- All capital-exceeded errors MUST be found
- The search MUST work regardless of Chinese text variations
- The error code MUST be at the end of the message in parentheses

**Error Code Registry**:
```python
ERROR_CODES = {
    "RISK_EXCEEDED": "交易风险超限",
    "CAPITAL_EXCEEDED": "资金需求超限",
    "CONCENTRATION_EXCEEDED": "仓位集中度超限",
    "DRAWDOWN_TRIGGERED": "触发回撤熔断",
    "DAILY_LOSS_LIMIT": "触发每日亏损限额",
    "MARKET_CLOSED": "市场已关闭",
    "STALE_DATA": "数据过期",
    "INVALID_STRIKE": "无效行权价",
    "INVALID_EXPIRY": "无效到期日",
    "MISSING_FIELD": "缺少字段"
}
```

**Message Format**:
```python
f"{chinese_message} ({ERROR_CODE})"
# Example: "交易风险 $600 超过限额 $500 (RISK_EXCEEDED)"
```

**Validation**:
- Trigger each error scenario
- Run `grep "RISK_EXCEEDED" logs/*.log`
- Verify all occurrences are found
- Confirm error codes are consistent

---

