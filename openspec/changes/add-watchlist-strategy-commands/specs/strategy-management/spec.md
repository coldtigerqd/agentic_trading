# strategy-management Specification Deltas

## ADDED Requirements

### Requirement: List All Strategy Instances

The system SHALL provide a `/trade:strategies` slash command that lists all swarm intelligence strategy instances from `swarm_intelligence/active_instances/` with their configuration details.

**Priority:** MUST
**Impact:** Core UX for strategy visibility and management

#### Scenario: View all strategy instances with mixed enabled status

**Given** directory `swarm_intelligence/active_instances/` contains 4 JSON files:
- `momentum_tech_short.json` (template=momentum_hunter, sector=tech, enabled=true, 15 symbols)
- `mean_reversion_energy.json` (template=mean_reversion, sector=energy, enabled=true, 8 symbols)
- `volatility_breakout_all.json` (template=vol_breakout, sector=all, enabled=false, 30 symbols)
- `iron_condor_tech.json` (template=iron_condor, sector=tech, enabled=true, 10 symbols)

**When** user executes `/trade:strategies`

**Then** the system SHALL display:
- Table with columns: ID, Template, Sector, Status, Symbols, Key Parameters
- Enabled strategies marked with ✓, disabled with ○
- Sorted by status (enabled first), then by instance ID
- Summary line: "Total: 4 instances | Enabled: 3 | Disabled: 1"
- Clear formatting showing key parameters for each strategy

#### Scenario: Empty active_instances directory

**Given** directory `swarm_intelligence/active_instances/` is empty

**When** user executes `/trade:strategies`

**Then** the system SHALL display:
- "No strategy instances found in swarm_intelligence/active_instances/"
- Helpful suggestion: "Create strategy instances by copying from templates/"

#### Scenario: Gracefully handle malformed JSON

**Given** `active_instances/` contains:
- `valid_strategy.json` (well-formed, enabled=true)
- `broken_strategy.json` (invalid JSON syntax)
- `incomplete.json` (valid JSON but missing 'template_name' field)

**When** user executes `/trade:strategies`

**Then** the system SHALL:
- Display `valid_strategy` successfully
- Show warning: "Warning: Skipped 'broken_strategy.json' (invalid JSON format)"
- Show warning: "Warning: 'incomplete.json' missing 'template_name' field"
- Include both warnings below the table

---

### Requirement: Enable Strategy Instance

The system SHALL provide a `/trade:strategy-enable` slash command to activate a disabled strategy instance using atomic file operations to prevent corruption.

**Priority:** MUST
**Impact:** Core UX for strategy activation with safety guarantees

#### Scenario: Enable a disabled strategy

**Given** strategy instance `volatility_breakout_all.json` exists with `enabled: false`
**And** JSON file is valid and well-formed

**When** user executes `/trade:strategy-enable volatility_breakout_all`

**Then** the system SHALL:
- Read current JSON configuration
- Set `"enabled": true` in configuration
- Write atomically using temp file + rename pattern:
  1. Write to `volatility_breakout_all.json.tmp`
  2. Validate JSON is well-formed
  3. Rename temp file to `volatility_breakout_all.json` (atomic operation)
- Display:
  ```
  ✓ Enabled strategy instance: volatility_breakout_all
    Template: vol_breakout
    Sector: all
    Symbol pool: 30 symbols

  This strategy will be active in the next swarm consultation.
  Run /trade:analyze to trigger analysis immediately.
  ```

#### Scenario: Enable already-enabled strategy (idempotent)

**Given** strategy instance `momentum_tech_short.json` exists with `enabled: true`

**When** user executes `/trade:strategy-enable momentum_tech_short`

**Then** the system SHALL:
- Detect strategy is already enabled
- Display: "ℹ Strategy 'momentum_tech_short' is already enabled (no changes made)"
- Not modify file

#### Scenario: Reject non-existent strategy instance

**Given** strategy instance `nonexistent_strategy.json` does not exist in `active_instances/`

**When** user executes `/trade:strategy-enable nonexistent_strategy`

**Then** the system SHALL:
- Display error: "Error: Strategy instance 'nonexistent_strategy' not found. Use /trade:strategies to list available instances."
- Not create new files

---

### Requirement: Disable Strategy Instance

The system SHALL provide a `/trade:strategy-disable` slash command to deactivate an enabled strategy instance while preserving all configuration.

**Priority:** MUST
**Impact:** Core UX for strategy deactivation

#### Scenario: Disable an enabled strategy

**Given** strategy instance `iron_condor_tech.json` exists with `enabled: true`

**When** user executes `/trade:strategy-disable iron_condor_tech`

**Then** the system SHALL:
- Read current JSON configuration
- Set `"enabled": false` in configuration
- Preserve all other fields (parameters, symbol_pool, sector, etc.)
- Write atomically using temp file + rename
- Display:
  ```
  ✓ Disabled strategy instance: iron_condor_tech
    Template: iron_condor
    Sector: tech
    Symbol pool: 10 symbols

  This strategy will NOT participate in future swarm consultations.
  All configuration preserved. Re-enable anytime with:
    /trade:strategy-enable iron_condor_tech
  ```

#### Scenario: Disable already-disabled strategy (idempotent)

**Given** strategy instance `volatility_breakout_all.json` exists with `enabled: false`

**When** user executes `/trade:strategy-disable volatility_breakout_all`

**Then** the system SHALL:
- Detect strategy is already disabled
- Display: "ℹ Strategy 'volatility_breakout_all' is already disabled (no changes made)"
- Not modify file

#### Scenario: Atomic write prevents file corruption

**Given** strategy instance `momentum_tech_short.json` exists with `enabled: true`
**And** process is killed mid-write (simulated by removing write permissions during test)

**When** user executes `/trade:strategy-disable momentum_tech_short`
**And** atomic rename fails due to permission error

**Then** the system SHALL:
- Detect write failure
- Leave original file unchanged (atomic rename guarantee)
- Display error: "Error: Failed to update configuration (file may be locked). Retry in a moment."
- Temp file (`momentum_tech_short.json.tmp`) may remain but original is intact
