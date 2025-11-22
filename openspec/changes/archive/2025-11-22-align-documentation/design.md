# Design: Documentation Alignment and Code Consolidation

## Architecture Decisions

### 1. Manual Command Mode vs Automatic Loop

**Decision**: Transition from automatic 5-minute loop to manual command-triggered analysis

**Rationale**:
- **User Control**: Explicit control over when trading analysis runs
- **Cost Efficiency**: No continuous LLM API calls when not needed
- **Debuggability**: Easier to trace single command execution
- **Safety**: Human-in-the-loop for major decisions
- **Development**: Aligns with Claude Code workflow (slash commands)

**Trade-offs**:
- ❌ Not "autonomous" in continuous sense
- ✅ More predictable behavior
- ✅ Lower API costs
- ✅ Better for development and testing

**Implementation**:
```
User types command in Claude Code
    ↓
Slash command invokes Commander system prompt
    ↓
Commander calls workflow_skills.run_full_trading_analysis()
    ↓
Analysis complete, results displayed
```

---

### 2. Unified Data Persistence Layer

**Decision**: Consolidate 3 different `get_db_connection()` implementations into 1

**Current Problem**:
```python
# db_helpers.py - context manager (BEST)
@contextmanager
def get_db_connection():
    # ... auto commit/rollback

# market_data_manager.py - manual close (RISKY)
def get_db_connection():
    return conn  # caller must close

# seed_watchlist.py - inline (INCONSISTENT)
conn = sqlite3.connect(DB_PATH)
```

**Solution**: Single source of truth in `data_lake/db_config.py`

**Benefits**:
- Consistent error handling (auto rollback)
- Consistent performance settings (WAL, NORMAL sync)
- Single point for configuration changes
- Prevents resource leaks (context manager auto-close)

**PRAGMA Settings Chosen**:
```python
PRAGMA journal_mode=WAL    # Write-Ahead Logging for concurrency
PRAGMA synchronous=NORMAL  # Balance safety/performance
```

**Why WAL?**
- Allows concurrent reads during writes
- Better performance for multi-process access
- Standard for modern SQLite applications

**Why NORMAL sync?**
- Trades absolute durability for performance
- Safe for local development
- Acceptable risk for paper trading
- Can upgrade to FULL for live trading

---

### 3. Data Sync Pathway Hierarchy

**Decision**: Establish clear primary vs secondary sync pathways

**Primary Path** (Interactive):
```
User command → Slash command → workflow_skills → Data sync as needed
```

**Secondary Path** (Background):
```
Cron/Daemon → data_sync_daemon.py → Periodic updates
```

**Rationale**:
- Primary path: User-initiated, on-demand
- Secondary path: Maintenance, non-trading hours
- Clear separation of concerns

**Deleted Scripts** (Redundant):
- `sync_with_rest_api.py` - Functionality in skills
- `run_sync_once.py` - Functionality in daemon --once flag

**Kept Scripts**:
- `demo_incremental_sync.py` - Educational example

---

### 4. REST API vs MCP for ThetaData

**Decision**: Use REST API directly, not MCP wrapper

**Comparison**:
| Aspect | MCP Approach | REST API Approach |
|--------|--------------|-------------------|
| Reliability | ❌ Extra layer of failure | ✅ Direct HTTP calls |
| Debugging | ❌ Harder to inspect | ✅ Standard HTTP tools |
| Performance | ❌ JSON-RPC overhead | ✅ Direct requests |
| Dependencies | ❌ Requires MCP server running | ✅ Just httpx library |
| Flexibility | ❌ Limited to MCP schema | ✅ Full API access |

**Implementation**:
- Use `skills/thetadata_client.py` for direct REST calls
- Use `httpx` library for HTTP requests
- Cache responses in `data_lake/market_data_bars` table

**MCP Still Used For**:
- IBKR trading operations (official MCP server exists)
- Complex state management where MCP benefits outweigh costs

---

### 5. Watchdog Consolidation Strategy

**Current State**:
- `watchdog.py`: Heartbeat + account monitoring
- `data_sync_daemon.py`: Background data sync

**Future State** (Proposed):
- **Option A**: Merge into single daemon
  - ✅ Single process to manage
  - ✅ Shared database connection
  - ❌ More complex codebase

- **Option B**: Keep separate, remove heartbeat
  - ✅ Simple, focused daemons
  - ✅ Easier to understand
  - ✅ Can run independently
  - ❓ Two processes instead of one

**Recommendation**: Option B (keep separate, remove heartbeat)

**Rationale**:
- Heartbeat only needed for automatic loop (deprecated)
- Account monitoring and data sync are separate concerns
- Unix philosophy: Do one thing well
- Easier to enable/disable independently

**Updated Responsibilities**:
```python
# watchdog.py (simplified)
- Monitor account drawdown
- Trigger circuit breaker if needed
- NO heartbeat monitoring

# data_sync_daemon.py (unchanged)
- Background data synchronization
- Market hours aware
- Incremental updates
```

---

## Data Flow Diagrams

### Current User Flow (After Changes)

```
┌─────────────────────────────────────────────────────┐
│ User types command in Claude Code                   │
│ Example: "请开始一次交易分析"                         │
└────────────────────┬────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────────┐
│ Commander System Prompt Activated                   │
│ (prompts/commander_system.md)                       │
└────────────────────┬────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────────┐
│ Workflow Skill: run_full_trading_analysis()         │
│ - Check market status                               │
│ - Sync data if needed                               │
│ - Consult swarm                                     │
│ - Evaluate signals                                  │
└────────────────────┬────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────────┐
│ Return results to user                              │
│ - Signals found                                     │
│ - Orders placed/rejected                            │
│ - Reasoning                                         │
└─────────────────────────────────────────────────────┘
```

### Data Persistence Architecture (After Consolidation)

```
┌──────────────────────────────────────────────────────┐
│                  Application Layer                   │
│  (skills, runtime, scripts)                          │
└────────────────┬─────────────────────────────────────┘
                 ↓
┌──────────────────────────────────────────────────────┐
│             data_lake/ Public API                    │
│  log_trade(), insert_bars(), save_snapshot()         │
└────────────────┬─────────────────────────────────────┘
                 ↓
         ┌───────┴────────┐
         ↓                ↓
┌─────────────────┐  ┌──────────────────┐
│  db_helpers.py  │  │ market_data_     │
│  (trades)       │  │ manager.py       │
└────────┬────────┘  └────────┬─────────┘
         ↓                    ↓
         └──────────┬─────────┘
                    ↓
         ┌──────────────────────┐
         │  db_config.py        │
         │  - DB_PATH           │
         │  - get_db_connection │
         └──────────┬───────────┘
                    ↓
         ┌──────────────────────┐
         │  trades.db (SQLite)  │
         │  - trades            │
         │  - safety_events     │
         │  - market_data_bars  │
         │  - watchlist         │
         └──────────────────────┘
```

---

## Migration Path

### For Existing Users (if any)

**If using main_loop.py**:
1. Stop the main loop process
2. Switch to manual command mode
3. Use slash commands to trigger analysis
4. Optionally: Run data_sync_daemon for background updates

**If using MCP ThetaData**:
1. No action needed - REST API is transparent
2. Ensure `THETADATA_API_KEY` in `.env`
3. Skills library handles API calls

**For Developers**:
1. Import from `data_lake` module instead of individual files
2. All `get_db_connection()` calls now use context manager
3. Manual `conn.close()` calls can be removed

---

## Testing Strategy

### Code Consolidation Testing
```bash
# Test unified DB connection
python -c "from data_lake import log_trade, insert_bars"

# Test context manager works
python -c "from data_lake.db_config import get_db_connection; \
with get_db_connection() as conn: print('OK')"

# Ensure no duplicates
grep -r "^DB_PATH = " data_lake/  # Should show only db_config.py
```

### Documentation Accuracy Testing
```bash
# Check all referenced files exist
grep -oP '`[^`]+\.py`' README.md | sort -u | while read f; do
  f=$(echo $f | tr -d '`')
  [ -f "$f" ] || echo "MISSING: $f"
done

# Check no mentions of unimplemented features
grep -i "dream.lab\|dream_lab" README.md  # Should only be in Roadmap section
```

### Integration Testing
```bash
# Run existing test suite
pytest tests/ -v

# Run seed script with new config
python data_lake/seed_watchlist.py

# Test workflow skills
python -c "from skills import run_market_health_check; \
result = run_market_health_check(); print(result)"
```

---

## Risks and Mitigations

### Risk 1: Breaking Imports
**Risk**: Refactoring `data_lake/` breaks existing imports
**Mitigation**:
- Keep public API stable
- Use `__init__.py` for backwards compatibility
- Test all import patterns

### Risk 2: Database Connection Issues
**Risk**: Context manager changes break existing code
**Mitigation**:
- Grep for all `get_db_connection` usages
- Verify all use `with` statement
- Test with actual database operations

### Risk 3: Documentation Drift
**Risk**: Documentation becomes stale again
**Mitigation**:
- Add CI check: grep for "dream_lab" outside Roadmap
- Code review process includes doc updates
- Keep README close to code (mention file names)

### Risk 4: User Confusion During Transition
**Risk**: Users don't know about manual mode
**Mitigation**:
- Create MIGRATION.md with clear examples
- Add deprecation warnings in legacy files
- Update CLAUDE.md with new workflow

---

## Future Considerations

### When to Implement Dream Lab
If/when Dream Lab is implemented:
1. Create actual `dream_lab/` directory
2. Move from Roadmap to Implemented section
3. Update architecture diagram
4. Add testing section for genetic algorithms

### When to Add News Sentiment
When MCP server is complete:
1. Update tech stack in project.md
2. Document integration in README
3. Add to workflow_skills integration points

### Scalability
Current design scales to:
- ✅ Manual command: 10-100 analyses per day
- ✅ Data storage: 50 symbols × 3 years ≈ 500MB
- ✅ Concurrent access: SQLite WAL mode handles 5-10 processes
- ❌ High-frequency trading: Not designed for this

---

## Conclusion

This design establishes:
1. **Clear running mode**: Manual commands, not automatic loop
2. **Unified codebase**: Single DB connection pattern
3. **Clean pathways**: Primary (interactive) vs Secondary (background) data sync
4. **Accurate documentation**: README matches reality
5. **Migration path**: Clear guidance for any legacy users

The changes are **low-risk** (mostly documentation + consolidation) with **high value** (clarity, maintainability).
