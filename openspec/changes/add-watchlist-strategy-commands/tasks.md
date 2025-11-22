# Tasks: Add Watchlist and Strategy Management Slash Commands

## Task Breakdown

### Phase 1: Watchlist Management Commands (Parallel)

#### Task 1.1: Implement `/trade:watchlist` command
- **Description**: Display current watchlist with symbols, priorities, and data freshness
- **Files**: `.claude/commands/trade/watchlist.md`
- **Acceptance**:
  - Shows all active watchlist symbols
  - Displays priority levels and notes
  - Shows data freshness (bars cached, latest timestamp)
  - Clear formatting for easy scanning
- **Dependencies**: None
- **Estimate**: 30 min

#### Task 1.2: Implement `/trade:watchlist-add` command
- **Description**: Add one or more symbols to watchlist
- **Files**: `.claude/commands/trade/watchlist-add.md`
- **Acceptance**:
  - Accepts symbol(s), priority (default 5), and optional notes
  - Validates symbol format (uppercase, valid ticker)
  - Provides feedback on success/failure
  - Suggests next step (trigger backfill if needed)
- **Dependencies**: None
- **Estimate**: 30 min

#### Task 1.3: Implement `/trade:watchlist-remove` command
- **Description**: Remove one or more symbols from watchlist
- **Files**: `.claude/commands/trade/watchlist-remove.md`
- **Acceptance**:
  - Accepts symbol(s) to remove
  - Confirms removal (soft delete, preserves cached data)
  - Warns if symbol has active positions
  - Provides clear success/error messages
- **Dependencies**: None
- **Estimate**: 30 min

---

### Phase 2: Strategy Management Commands (Parallel)

#### Task 2.1: Implement `/trade:strategies` command
- **Description**: List all active swarm strategy instances
- **Files**: `.claude/commands/trade/strategies.md`
- **Acceptance**:
  - Lists all instance IDs from `swarm_intelligence/active_instances/`
  - Shows template name, sector, enabled status
  - Displays key parameters (symbol_pool, thresholds)
  - Clear table format
- **Dependencies**: None
- **Estimate**: 45 min
- **Note**: Requires new helper function to scan active_instances/

#### Task 2.2: Implement `/trade:strategy-enable` command
- **Description**: Enable a disabled strategy instance
- **Files**: `.claude/commands/trade/strategy-enable.md`
- **Acceptance**:
  - Accepts instance ID
  - Sets `"enabled": true` in JSON config
  - Validates instance exists before modification
  - Uses atomic file write (temp file + rename)
- **Dependencies**: None
- **Estimate**: 45 min
- **Note**: Requires new helper function to modify instance config

#### Task 2.3: Implement `/trade:strategy-disable` command
- **Description**: Disable an active strategy instance
- **Files**: `.claude/commands/trade/strategy-disable.md`
- **Acceptance**:
  - Accepts instance ID
  - Sets `"enabled": false` in JSON config
  - Preserves all other configuration
  - Confirms action with user
- **Dependencies**: Task 2.2 (shares helper function)
- **Estimate**: 30 min

---

### Phase 3: Symbol-Strategy Analysis Command

#### Task 3.1: Implement `/trade:analyze-symbol` command
- **Description**: Run specific strategy against specific symbol
- **Files**: `.claude/commands/trade/analyze-symbol.md`
- **Acceptance**:
  - Accepts symbol and strategy instance ID
  - Runs single-instance swarm analysis (not full consult_swarm)
  - Returns signal with confidence score
  - Shows reasoning from strategy
  - Useful for testing strategies before enabling
- **Dependencies**: None
- **Estimate**: 60 min
- **Note**: May require new skill function for single-strategy analysis

---

### Phase 4: Helper Functions & Integration

#### Task 4.1: Create strategy management skill functions
- **Description**: Add helper functions for strategy instance management
- **Files**: `skills/strategy_manager.py` (new)
- **Functions**:
  - `list_active_strategies()` - Scan and parse active_instances/
  - `enable_strategy(instance_id)` - Set enabled flag
  - `disable_strategy(instance_id)` - Clear enabled flag
  - `get_strategy_config(instance_id)` - Read instance JSON
  - `analyze_with_strategy(symbol, instance_id, market_data)` - Single-strategy analysis
- **Acceptance**:
  - All functions have proper error handling
  - JSON operations are atomic (no corruption)
  - Functions are exported in `skills/__init__.py`
- **Dependencies**: None (can be done in parallel with commands)
- **Estimate**: 90 min

#### Task 4.2: Update skills exports
- **Description**: Ensure all watchlist/strategy functions are exported
- **Files**: `skills/__init__.py`
- **Acceptance**:
  - All watchlist functions accessible
  - All strategy management functions accessible
  - Proper __all__ list
- **Dependencies**: Task 4.1
- **Estimate**: 15 min

---

### Phase 5: Documentation & Testing

#### Task 5.1: Update README.md
- **Description**: Add new slash commands to documentation
- **Files**: `README.md`
- **Acceptance**:
  - New commands listed in Scripts Reference section
  - Usage examples for each command
  - Clear descriptions of parameters
- **Dependencies**: All command tasks complete
- **Estimate**: 30 min

#### Task 5.2: Manual testing
- **Description**: Test all commands end-to-end
- **Test Cases**:
  - Add/remove symbols from watchlist
  - View watchlist with data status
  - List strategies and view details
  - Enable/disable strategies
  - Run analysis on specific symbol with specific strategy
  - Error handling (invalid symbols, non-existent instances, etc.)
- **Dependencies**: All implementation complete
- **Estimate**: 45 min

#### Task 5.3: Validate OpenSpec compliance
- **Description**: Run `openspec validate` and resolve issues
- **Files**: All spec files
- **Acceptance**: `openspec validate add-watchlist-strategy-commands --strict` passes
- **Dependencies**: All specs written
- **Estimate**: 15 min

---

## Task Ordering & Parallelization

### Parallel Tracks
- **Track A**: Watchlist commands (Tasks 1.1-1.3) - Can run in parallel
- **Track B**: Strategy commands (Tasks 2.1-2.3) - Can run in parallel
- **Track C**: Helper functions (Task 4.1) - Can start immediately

### Sequential Dependencies
1. Task 4.1 → Task 4.2 (exports depend on functions)
2. All implementation → Task 5.1 (documentation)
3. All implementation → Task 5.2 (testing)
4. All specs → Task 5.3 (validation)

### Optimal Execution Order
1. **Start simultaneously**: Tasks 1.1, 1.2, 1.3, 2.1, 4.1
2. **Then**: Tasks 2.2, 2.3, 3.1 (after 4.1 provides helpers)
3. **Then**: Task 4.2
4. **Finally**: Tasks 5.1, 5.2, 5.3

## Total Estimates
- **Implementation**: ~5.5 hours
- **Documentation & Testing**: ~1.5 hours
- **Total**: ~7 hours (can be reduced to ~4 hours with parallelization)
