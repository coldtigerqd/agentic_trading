# Design: Watchlist and Strategy Management Slash Commands

## Architecture Overview

This change introduces a **command layer** on top of existing watchlist and swarm intelligence capabilities, following the established `/trade:*` command pattern.

```
┌─────────────────────────────────────────────────────────────┐
│                   Slash Command Layer                        │
│  (.claude/commands/trade/*.md)                              │
│                                                              │
│  /trade:watchlist    /trade:strategies    /trade:analyze-symbol │
│  /trade:watchlist-add   /trade:strategy-enable              │
│  /trade:watchlist-remove  /trade:strategy-disable           │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                   Skills Layer (Python)                      │
│  skills/watchlist_manager.py   skills/strategy_manager.py   │
│                                                              │
│  - get_watchlist()              - list_active_strategies()  │
│  - add_to_watchlist()           - enable_strategy()         │
│  - remove_from_watchlist()      - disable_strategy()        │
│  - get_watchlist_status()       - analyze_with_strategy()   │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                   Data Layer                                 │
│                                                              │
│  SQLite DB                       JSON Files                 │
│  data_lake/trades.db             swarm_intelligence/        │
│  - watchlist table               active_instances/*.json    │
│  - market_data_bars              - template_name            │
│                                  - enabled                   │
│                                  - parameters                │
└─────────────────────────────────────────────────────────────┘
```

## Key Design Decisions

### 1. Slash Commands vs. Direct Skills

**Decision**: Implement as slash commands (`.claude/commands/trade/*.md`) that invoke Python skills

**Rationale**:
- Consistency with existing `/trade:analyze`, `/trade:health` pattern
- User-friendly interface (no need to remember Python function signatures)
- Easy to discover via tab completion and `/help`
- Separation of concerns: commands handle I/O, skills handle logic

**Alternative Considered**: Expose Python skills directly
- Rejected: Less discoverable, inconsistent UX, more friction

### 2. Soft Delete vs. Hard Delete for Watchlist Removal

**Decision**: Soft delete (set `is_active=false`, preserve data)

**Rationale**:
- Preserves historical data for potential re-addition
- Prevents accidental data loss
- Allows "undo" by re-adding symbol
- Database queries simply filter `WHERE is_active=true`

**Trade-offs**:
- Database grows slightly larger (negligible for realistic watchlist sizes)
- Need to handle "re-add" scenario (update existing row vs. insert new)

### 3. Atomic File Operations for Strategy Enable/Disable

**Decision**: Use write-to-temp-then-rename pattern for JSON updates

**Rationale**:
- POSIX guarantees atomicity of `rename()` system call
- Prevents file corruption if process killed mid-write
- Simple to implement, no external dependencies (no file locks needed)

**Implementation**:
```python
# Write to temp file
with open(f"{instance_id}.json.tmp", 'w') as f:
    json.dump(config, f, indent=2)

# Atomic rename
os.rename(f"{instance_id}.json.tmp", f"{instance_id}.json")
```

**Alternative Considered**: File locking
- Rejected: More complex, platform-dependent, can deadlock

### 4. Single-Strategy Analysis vs. Full Swarm Consult

**Decision**: Create new `analyze_with_strategy()` function separate from `consult_swarm()`

**Rationale**:
- Different use cases: testing/learning vs. production trading
- Simpler implementation (no aggregation logic needed)
- Faster execution (only one strategy, one symbol)
- Clearer educational output (show strategy reasoning in detail)

**Integration Point**: Both functions can share underlying strategy template code

### 5. Data Fetching for analyze_with_strategy()

**Decision**: Check cache first, fetch from ThetaData on-demand if missing

**Rationale**:
- Flexibility: analyze any symbol, not just watchlist
- Performance: use cache when available
- User experience: automatic data fetch prevents "no data" errors

**Trade-off**: Initial analysis may be slow (15 seconds) if fetching 3 years of data
- Mitigation: Show progress indicator, suggest adding to watchlist for caching

## Data Flow Diagrams

### Watchlist Add Flow

```
User: /trade:watchlist-add AAPL --priority 1 --notes "Core holding"
  │
  ▼
Command: .claude/commands/trade/watchlist-add.md
  │ Parse arguments (symbol, priority, notes)
  │ Validate inputs
  ▼
Skill: skills/watchlist_manager.add_to_watchlist(symbol, priority, notes)
  │ Check if symbol exists (UPDATE vs INSERT)
  │ Validate ticker format
  ├─ If exists: UPDATE priority, notes WHERE symbol=AAPL
  └─ If new: INSERT INTO watchlist (symbol, priority, notes, is_active, added_at)
  │
  ▼
Database: data_lake/trades.db
  │ Transaction committed
  ▼
Response: "✓ Added AAPL to watchlist (priority=1)"
          "Next steps: Run backfill or wait for daily sync"
```

### Strategy Enable Flow

```
User: /trade:strategy-enable momentum_tech_short
  │
  ▼
Command: .claude/commands/trade/strategy-enable.md
  │ Parse argument (instance_id)
  ▼
Skill: skills/strategy_manager.enable_strategy(instance_id)
  │ Verify instance exists
  │ Read JSON config
  │ Set enabled=true
  │ Write atomically (temp file + rename)
  │
  ▼
File System: swarm_intelligence/active_instances/momentum_tech_short.json
  │ File updated atomically
  ▼
Response: "✓ Enabled strategy instance: momentum_tech_short"
          "Active in next swarm consultation"
```

### Symbol-Strategy Analysis Flow

```
User: /trade:analyze-symbol AAPL momentum_tech_short
  │
  ▼
Command: .claude/commands/trade/analyze-symbol.md
  │ Parse arguments (symbol, instance_id)
  ▼
Skill: skills/strategy_manager.analyze_with_strategy(symbol, instance_id)
  │
  ├─ Load strategy config from JSON
  │  └─ Get template_name, parameters, symbol_pool
  │
  ├─ Fetch market data
  │  ├─ Check cache: SELECT * FROM market_data_bars WHERE symbol=AAPL
  │  ├─ If missing/stale: Fetch from ThetaData (on-demand)
  │  └─ Check data quality (freshness)
  │
  ├─ Import strategy template module
  │  └─ from swarm_intelligence.templates.{template_name} import analyze
  │
  ├─ Execute strategy logic
  │  └─ signal, confidence, reasoning = template.analyze(symbol, data, params)
  │
  └─ Format output (signal, confidence, reasoning, metrics, suggested_trade)
  │
  ▼
Response: Detailed analysis with reasoning and next steps
```

## Module Organization

### New Files

```
skills/
  strategy_manager.py        # NEW: Strategy instance management
    - list_active_strategies() → List[StrategyInstance]
    - enable_strategy(instance_id: str) → bool
    - disable_strategy(instance_id: str) → bool
    - get_strategy_config(instance_id: str) → dict
    - analyze_with_strategy(symbol: str, instance_id: str) → AnalysisResult

.claude/commands/trade/
  watchlist.md              # NEW: /trade:watchlist
  watchlist-add.md          # NEW: /trade:watchlist-add
  watchlist-remove.md       # NEW: /trade:watchlist-remove
  strategies.md             # NEW: /trade:strategies
  strategy-enable.md        # NEW: /trade:strategy-enable
  strategy-disable.md       # NEW: /trade:strategy-disable
  analyze-symbol.md         # NEW: /trade:analyze-symbol
```

### Modified Files

```
skills/__init__.py
  # Add exports for strategy_manager
  from .strategy_manager import (
      list_active_strategies,
      enable_strategy,
      disable_strategy,
      analyze_with_strategy
  )

README.md
  # Update Scripts Reference section
  # Add documentation for all 7 new slash commands
```

## Error Handling Strategy

### Principle: Fail Fast with Clear Messages

**Database Errors**:
- SQLite locked → Retry with exponential backoff (3 attempts)
- Table doesn't exist → Clear error: "Database not initialized. Run setup first."

**File System Errors**:
- JSON not found → "Error: Strategy instance 'xyz' not found. Use /trade:strategies to list."
- JSON malformed → "Warning: Skipped 'xyz.json' (invalid JSON). Check file syntax."
- Write failure → "Error: Failed to update config. File may be locked. Retry."

**Data Errors**:
- No market data → "Error: No data for AAPL. Run backfill or wait for sync."
- Stale data → "⚠ Warning: Data is 5 days old. Results may be inaccurate."
- ThetaData fetch failure → "Error: ThetaData fetch failed (timeout). Try again or check connection."

**Validation Errors**:
- Invalid ticker → "Error: 'abc' is not valid (must be 2-5 uppercase letters)"
- Invalid priority → "Error: Priority must be 1-10 (got 15)"
- Symbol has positions → "Error: AAPL has active positions. Use --force to override."

### Recovery Mechanisms

1. **Database**: Retry on lock, rollback on error
2. **File System**: Backup before modify, restore on corruption
3. **Network**: Retry with exponential backoff (ThetaData fetches)
4. **Strategy Execution**: Catch exceptions, log details, continue (don't crash entire analysis)

## Performance Considerations

### Expected Latencies

| Operation | Target | Notes |
|-----------|--------|-------|
| `/trade:watchlist` | <2s | Query DB, format table |
| `/trade:watchlist-add` | <1s | Single INSERT/UPDATE |
| `/trade:watchlist-remove` | <1s | Single UPDATE (soft delete) |
| `/trade:strategies` | <1s | Scan directory, parse JSON |
| `/trade:strategy-enable` | <500ms | Atomic file write |
| `/trade:strategy-disable` | <500ms | Atomic file write |
| `/trade:analyze-symbol` (cached) | <5s | Load data, run strategy |
| `/trade:analyze-symbol` (fetch) | <15s | Fetch 3 years from ThetaData |

### Optimization Opportunities

1. **Watchlist Status**: Cache market_data_bars aggregations (per-symbol latest timestamp)
2. **Strategy List**: Cache directory scan results (invalidate on file change)
3. **Analyze Symbol**: Pre-fetch options chain if strategy requires it (async)

### Scalability

- **Watchlist Size**: Tested up to 50 symbols (typical: 10-20)
- **Strategy Instances**: Tested up to 20 instances (typical: 5-10)
- **Market Data**: 3 years × 10 symbols × 78 bars/day = ~590k rows (manageable for SQLite)

## Security Considerations

### Input Validation

- **Symbol**: Must match `^[A-Z]{2,5}$` (uppercase, 2-5 letters)
- **Priority**: Must be integer 1-10
- **Instance ID**: Must match `^[a-z0-9_]+$` (alphanumeric + underscore, no path traversal)

### File System Safety

- **No Path Traversal**: Validate instance_id doesn't contain `..` or `/`
- **Restricted Directory**: Only read/write in `swarm_intelligence/active_instances/`
- **Atomic Writes**: Use temp file + rename to prevent corruption

### Database Safety

- **Parameterized Queries**: Always use `?` placeholders (no SQL injection)
- **Transactions**: Wrap multi-step operations in transactions
- **Soft Deletes**: Never hard delete (can't recover from accidental deletion)

## Testing Strategy

### Unit Tests

- `test_watchlist_manager.py`:
  - Add symbol (new and duplicate)
  - Remove symbol (with/without positions)
  - Get watchlist status (various data freshness)

- `test_strategy_manager.py`:
  - List strategies (empty, partial, all)
  - Enable/disable (idempotency, error cases)
  - Analyze with strategy (various signal types)

### Integration Tests

- End-to-end command flow (user input → database/file change → output)
- Concurrent operations (multiple add/remove in parallel)
- Data quality scenarios (GOOD/STALE/CRITICAL)

### Manual Testing

See `tasks.md` Phase 5 for comprehensive manual test scenarios

## Migration Plan

**No migration needed** - This is additive functionality only:
- No existing table schema changes
- No existing file format changes
- No breaking changes to existing commands or skills

**Rollout Steps**:
1. Implement and test all slash commands
2. Update documentation (README.md)
3. Deploy to production (no downtime required)
4. Monitor logs for any errors in first 24 hours

## Future Improvements

1. **Bulk Operations**: Add/remove multiple symbols, enable/disable by sector
2. **Analytics**: Track strategy performance over time (win rate, avg P&L)
3. **Notifications**: Alert when strategy is enabled/disabled
4. **Web UI**: Visual dashboard for watchlist and strategy management (low priority)
5. **Backtesting**: Historical performance of strategy against symbol

## Open Questions

- Should `/trade:analyze-symbol` cache results? (Probably not - analysis is cheap)
- Should we limit watchlist size? (Current: no limit, realistic max ~50)
- Should we require confirmation for strategy disable? (Optional safety feature)

---

**Version**: 1.0
**Date**: 2025-11-22
**Status**: Proposed
