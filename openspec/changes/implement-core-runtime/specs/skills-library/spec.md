# Capability: Skills Library

**Version:** 1.0.0
**Status:** Proposed
**Owner:** Core Runtime Team

## Overview

The Skills Library provides computational primitives that Claude Code (Commander agent) can invoke to perform deterministic operations. Skills are Python functions that handle swarm orchestration, mathematical calculations, and validated order execution.

## ADDED Requirements

### Requirement: Swarm Intelligence Skill
**Priority:** MUST
**Category:** Core Functionality

The system MUST provide a `consult_swarm()` skill that executes concurrent sub-agent analysis across all active swarm instances.

#### Scenario: Commander requests swarm analysis for all sectors

**Given** Commander agent needs trading signals
**When** Commander invokes `skill.consult_swarm(sector="ALL")`
**Then** the skill:
- Loads all JSON configurations from `swarm_intelligence/active_instances/`
- Renders each template with instance parameters
- Saves complete input snapshot to `data_lake/snapshots/`
- Executes LLM API calls concurrently using asyncio
- Returns aggregated signal list with structure:
  ```json
  [{
    "instance_id": "tech_aggressive",
    "template_used": "vol_sniper",
    "target": "NVDA",
    "signal": "SHORT_PUT_SPREAD",
    "params": {"strike_short": 120, "strike_long": 115},
    "confidence": 0.88,
    "reasoning": "..."
  }]
  ```

**Verification:**
- Function signature: `consult_swarm(sector: str, market_data: Optional[Dict], max_concurrent: int) -> List[Signal]`
- All input snapshots saved before LLM execution
- Concurrent execution completes within 30 seconds for 10 instances
- Returns valid signal list or empty list (never fails silently)

#### Scenario: Swarm handles partial failures gracefully

**Given** 10 swarm instances are configured
**When** 3 LLM API calls fail due to timeout
**Then** the skill:
- Returns signals from 7 successful instances
- Logs all 3 failures with instance_id and error details
- Does NOT raise exception to Commander
- Includes warning in logs if >50% instances fail

**Verification:**
- Partial results returned successfully
- All failures logged to system logs
- Commander receives degraded but usable results

### Requirement: Mathematical Calculation Skill
**Priority:** MUST
**Category:** Core Functionality

The system MUST provide a `math_core` skill module containing deterministic financial calculations.

#### Scenario: Calculate position size using Kelly Criterion

**Given** Commander has winning probability, expected returns, and bankroll
**When** Commander invokes `skill.kelly_criterion(win_prob=0.6, win_amount=500, loss_amount=200, bankroll=10000, fraction=0.25)`
**Then** the skill returns fractional Kelly position size ($)

**Verification:**
- Function is pure (no side effects)
- Same inputs always produce same output
- Returns non-negative position size
- Default fraction is 0.25 for safety

#### Scenario: Calculate implied volatility from option price

**Given** Commander has option price and underlying parameters
**When** Commander invokes `skill.black_scholes_iv(option_price=5.50, spot=100, strike=105, time_to_expiry=0.25, rate=0.05, is_call=True)`
**Then** the skill returns implied volatility as decimal (e.g., 0.35 for 35%)

**Verification:**
- Uses Newton-Raphson method for IV calculation
- Converges within 20 iterations or returns None
- Handles edge cases (deep ITM/OTM)

### Requirement: Validated Order Execution Skill
**Priority:** MUST
**Category:** Safety-Critical

The system MUST provide an `execution_gate()` skill that validates and submits orders through the safety layer.

#### Scenario: Submit order passing all safety checks

**Given** Commander decides to place a put spread trade
**When** Commander invokes:
```python
skill.place_order_with_guard(
    symbol="AAPL",
    strategy="PUT_SPREAD",
    legs=[
        {"action": "SELL", "strike": 180, "expiry": "20251128", "quantity": 1, "price": 2.50},
        {"action": "BUY", "strike": 175, "expiry": "20251128", "quantity": 1, "price": 1.50}
    ],
    max_risk=100,
    capital_required=500,
    metadata={"confidence": 0.85, "reasoning": "High IV, neutral sentiment"}
)
```
**Then** the skill:
- Validates order against all safety limits in `safety.py`
- Constructs IBKR-compatible order format
- Submits to IBKR MCP server
- Logs order to `data_lake/trades.db`
- Returns OrderResult with status and order_id

**Verification:**
- All orders pass through SafetyValidator first
- No code path bypasses safety validation
- Both approved and rejected orders logged
- Function signature enforces required parameters

#### Scenario: Reject order exceeding risk limits

**Given** Commander attempts order with $600 max risk
**When** Commander invokes `skill.place_order_with_guard()` with `max_risk=600`
**Then** the skill:
- Safety validator rejects (limit is $500)
- Returns `OrderResult(success=False, error="Max risk ($600) exceeds limit ($500)")`
- Logs rejection to safety_events table
- Does NOT submit to IBKR

**Verification:**
- No IBKR API call made for rejected orders
- Rejection logged with full context
- Error message clearly states violation

### Requirement: Skills Module Structure
**Priority:** MUST
**Category:** Architecture

Skills MUST be organized as a Python package with clear module separation.

#### Scenario: Import skills in Commander runtime

**Given** Commander agent is starting up
**When** Runtime imports skills: `from skills import swarm_core, math_core, execution_gate`
**Then** all skill modules load successfully without errors

**Verification:**
- Directory structure:
  ```
  skills/
    __init__.py
    swarm_core.py
    math_core.py
    execution_gate.py
  ```
- Each module has type hints for all public functions
- Each function has docstring with Args/Returns
- Async functions properly marked with `async def`

### Requirement: Skills Error Handling
**Priority:** MUST
**Category:** Reliability

Skills MUST handle errors gracefully and provide actionable error messages to Commander.

#### Scenario: Handle missing template file

**Given** Swarm instance references non-existent template
**When** `consult_swarm()` attempts to load template
**Then** the skill:
- Skips that instance
- Logs warning: "Template 'vol_sniper.md' not found for instance 'tech_aggressive'"
- Continues processing other instances
- Returns signals from successful instances

**Verification:**
- System does not crash
- Error clearly identifies which instance and template
- Other instances process successfully

#### Scenario: Handle IBKR connection failure

**Given** IBKR Gateway is not running
**When** `place_order_with_guard()` attempts to submit order
**Then** the skill:
- Catches connection error
- Returns `OrderResult(success=False, error="IBKR connection failed: connection refused")`
- Does NOT retry automatically (Commander decides retry logic)

**Verification:**
- Connection errors caught and wrapped
- Error message helps diagnose issue
- No infinite retry loops

## Cross-Capability Dependencies

- **Requires**: `data-persistence` for snapshot and trade logging
- **Requires**: `swarm-intelligence` for template/instance loading
- **Uses**: IBKR MCP server for order submission
- **Uses**: Safety layer (mcp-servers/ibkr/safety.py) for validation
