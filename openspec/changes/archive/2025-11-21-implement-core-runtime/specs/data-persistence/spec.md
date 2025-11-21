# Capability: Data Persistence

**Version:** 1.0.0
**Status:** Proposed
**Owner:** Core Runtime Team

## Overview

Data Persistence provides SQLite database for trade records, decision snapshot storage, and safety event logging.

## ADDED Requirements

### Requirement: Trade Records Database
**Priority:** MUST
**Category:** Data Storage

The system MUST persist all trade orders (submitted, filled, rejected) to a SQLite database.

#### Scenario: Log submitted order

**Given** Order submitted through execution_gate
**When** Order accepted by IBKR
**Then** system writes record to `data_lake/trades.db`:
```sql
INSERT INTO trades (timestamp, symbol, strategy, legs, max_risk, capital_required, confidence, reasoning, order_id, status)
VALUES (...)
```

**Verification:**
- Database file at `data_lake/trades.db`
- Schema includes all order parameters
- Atomic transactions (no partial writes)
- WAL mode for concurrent reads

### Requirement: Decision Snapshot Storage
**Priority:** MUST
**Category:** Auditability

The system MUST save complete input context for every swarm instance execution.

#### Scenario: Save swarm input snapshot

**Given** Swarm instance about to invoke LLM API
**When** Instance ID is "tech_aggressive", timestamp is "2025-11-20T09:30:45"
**Then** system saves `data_lake/snapshots/20251120T093045_tech_aggressive.json` containing:
- Complete rendered prompt
- All market data inputs
- Timestamp
- Instance configuration

**Verification:**
- Snapshots saved BEFORE LLM call
- Filename format: `{timestamp}_{instance_id}.json`
- Complete reproducibility (can replay exact inputs)

### Requirement: Safety Event Logging
**Priority:** MUST
**Category:** Safety

The system MUST log all safety violations and circuit breaker events.

#### Scenario: Log rejected order

**Given** Order rejected by safety validator
**When** Rejection occurs
**Then** system writes to safety_events table:
```sql
INSERT INTO safety_events (timestamp, event_type, details, action_taken)
VALUES ('2025-11-20T10:15:30', 'ORDER_REJECTED', '{"reason": "max_risk_exceeded", ...}', 'order_blocked')
```

**Verification:**
- All rejections logged
- Circuit breaker triggers logged
- Watchdog emergency actions logged
- Separate table from trades

## Cross-Capability Dependencies

- **Used by**: `skills-library` for trade/snapshot logging
- **Used by**: `runtime-lifecycle` for safety event logging
