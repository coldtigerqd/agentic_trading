# Spec Delta: Runtime Mode

## MODIFIED Requirements

### Requirement: Manual Command-Triggered Execution

The system SHALL operate in manual command mode where trading analysis MUST be triggered explicitly by user commands in Claude Code. The system MUST NOT run automatic time-based trading loops.

**Rationale**: Manual mode provides better user control, lower costs, and clearer execution tracing compared to automatic loops. Aligns with Claude Code's interactive workflow model.

#### Scenario: User triggers trading analysis

**Given** the user is in Claude Code with the project loaded
**When** they type a command like "请开始一次交易分析"
**Then** the Commander system prompt should be activated
**And** workflow skills should execute trading analysis
**And** results should be returned to the user
**And** NO automatic loop should continue after completion

#### Scenario: System idle state

**Given** the system has completed a trading analysis
**When** no user command is received
**Then** the system should remain idle
**And** NO automatic trading cycles should execute
**And** NO heartbeat monitoring is required

---

### Requirement: Background Daemon Operations (Optional)

Background daemons MAY run independently for maintenance tasks (data sync, account monitoring) but SHALL be supplementary to manual command mode. Daemons MUST NOT trigger trading decisions autonomously.

**Rationale**: Data sync and account monitoring can run in background without requiring manual intervention, but should not drive trading decisions.

#### Scenario: Data sync daemon running in background

**Given** data_sync_daemon.py is running
**When** market is open
**Then** daemon should sync watchlist data periodically
**And** daemon should NOT trigger trading analysis
**And** daemon should be independent of user commands

#### Scenario: Watchdog monitoring account

**Given** watchdog.py is running
**When** account drawdown exceeds threshold
**Then** watchdog should trigger circuit breaker
**And** watchdog should update agent memory
**And** watchdog should NOT require main loop to be running

---

## REMOVED Requirements

### ~~Requirement: Automatic Trading Loop~~

~~The system runs continuous trading loops at fixed intervals (e.g., every 5 minutes) managed by main_loop.py.~~

**Reason for Removal**: System architecture shifted to manual command mode. Automatic loop mode is deprecated and moved to legacy.

---

### ~~Requirement: Heartbeat Monitoring~~

~~The AI process writes periodic heartbeat timestamps that watchdog monitors to detect frozen processes.~~

**Reason for Removal**: Heartbeat only necessary for automatic loop detection. In manual mode, process state is managed by Claude Code runtime.

---

## ADDED Requirements

### Requirement: Slash Command Integration

The system SHALL support slash command invocation as the primary user interface for triggering trading operations. Commands MUST map to workflow skills in `skills/workflow_skills.py`.

**Rationale**: Slash commands provide a clean, documented interface within Claude Code for common operations.

#### Scenario: User invokes trading analysis via slash command

**Given** the project has defined slash commands
**When** user types a slash command (e.g., `/trade-analyze`)
**Then** the command should trigger the appropriate workflow skill
**And** the command should pass any parameters to the skill
**And** results should be formatted and displayed to user

#### Scenario: User discovers available commands

**Given** a new user exploring the system
**When** they view slash command documentation
**Then** they should see commands for: trading analysis, market health check, data sync
**And** each command should have clear description and usage examples
**And** commands should map to workflow skills in `skills/workflow_skills.py`
