# Capability: Runtime Lifecycle

**Version:** 1.0.0
**Status:** Proposed
**Owner:** Core Runtime Team

## Overview

Runtime Lifecycle manages the main trading loop and independent watchdog process that monitors AI health and enforces safety circuit breakers.

## ADDED Requirements

### Requirement: Main Trading Loop
**Priority:** MUST
**Category:** Core Infrastructure

The system MUST provide a main loop that schedules trading cycles and invokes Commander agent.

#### Scenario: Execute scheduled trading cycle

**Given** Main loop is running
**When** Cycle interval elapses
**Then** main loop:
- Sends heartbeat to watchdog
- Checks circuit breaker status
- Invokes Commander agent
- Waits for cycle completion
- Repeats

**Verification:**
- Implemented in `runtime/main_loop.py`
- Configurable cycle interval (default: 5 minutes)
- Graceful shutdown on SIGTERM
- Logs all cycle events

### Requirement: Independent Watchdog Process
**Priority:** MUST (Safety-Critical)
**Category:** Safety

The system MUST run an independent watchdog process that monitors AI health and can force-kill frozen processes.

#### Scenario: Detect frozen AI process

**Given** Watchdog monitors AI heartbeat with 60-second timeout
**When** AI process stops sending heartbeat for 60 seconds
**Then** watchdog:
- Logs CRITICAL alert
- Force-kills AI process (SIGKILL)
- Panic-closes all IBKR positions at market
- Sends alert to human operator

**Verification:**
- Separate Python process (multiprocessing)
- Independent IBKR connection (client_id=999)
- Can kill AI process without AI cooperation
- All emergency actions logged

#### Scenario: Trigger circuit breaker on drawdown

**Given** Initial account value is $10,000
**When** Account value drops to $8,900 (11% drawdown)
**Then** watchdog:
- Triggers circuit breaker (limit is 10%)
- Closes all positions
- Sets circuit_breaker_triggered flag
- Prevents new trading cycles

**Verification:**
- Drawdown calculated from session start value
- Circuit breaker persisted to disk
- Manual reset required (human approval)

## Cross-Capability Dependencies

- **Orchestrates**: `commander-orchestration`
- **Monitors**: All trading operations
- **Uses**: IBKR MCP for emergency position closing
