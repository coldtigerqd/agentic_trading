# Migration Guide: Agentic AlphaHive Architecture Evolution

This document explains major architectural changes and provides migration guidance for users and developers.

---

## 🔄 Major Architectural Shifts

### 1. Running Mode: Automatic Loop → Manual Command Triggered

**What Changed**:
- **Before**: System ran continuous 5-minute loops via `main_loop.py`
- **After**: Trading analysis triggered manually via commands in Claude Code

**Why the Change**:
- ✅ Better user control over when analysis runs
- ✅ Lower API costs (no continuous LLM calls)
- ✅ Easier debugging and tracing
- ✅ Human-in-the-loop safety
- ✅ Aligns with Claude Code interactive workflow

**How to Migrate**:

```python
# ❌ Old way (automatic loop)
# Start main_loop.py and it runs every 5 minutes
python runtime/main_loop.py

# ✅ New way (manual command)
# In Claude Code, type:
"请开始一次交易分析"

# Or use slash commands (when implemented):
/trade-analyze
```

**For Developers**:
- `main_loop.py` has been moved to `runtime/legacy/`
- Use `skills/workflow_skills.py` → `run_full_trading_analysis()` instead
- Watchdog no longer monitors heartbeats (not needed for manual mode)

---

### 2. Data Access: MCP ThetaData → REST API

**What Changed**:
- **Before**: Used MCP server wrapper for ThetaData API
- **After**: Direct REST API calls via `skills/thetadata_client.py`

**Why the Change**:

| Aspect | MCP Approach | REST API Approach |
|--------|--------------|-------------------|
| Reliability | ❌ Extra layer of failure | ✅ Direct HTTP calls |
| Debugging | ❌ Harder to inspect | ✅ Standard HTTP tools |
| Performance | ❌ JSON-RPC overhead | ✅ Direct requests |
| Dependencies | ❌ Requires MCP server | ✅ Just httpx library |

**How to Migrate**:

```python
# ❌ Old way (MCP tool)
# Commander called: mcp__ThetaData__stock_snapshot_ohlc(symbol=[...])

# ✅ New way (REST API via skills)
from skills.thetadata_client import fetch_snapshot_with_rest
result = fetch_snapshot_with_rest(symbol="AAPL")
```

**No Action Required**:
- The change is transparent to end users
- Skills library handles all API calls
- Just ensure `THETADATA_API_KEY` is in `.env`

**MCP Still Used For**:
- IBKR trading operations (`mcp-servers/ibkr/`)
- Complex state management where MCP benefits outweigh costs

---

### 3. Data Persistence: Multiple Implementations → Unified Config

**What Changed**:
- **Before**: 3 different `get_db_connection()` implementations
- **After**: Single implementation in `data_lake/db_config.py`

**Why the Change**:
- ✅ Eliminates code duplication
- ✅ Consistent error handling (auto-rollback)
- ✅ Consistent performance settings (WAL, NORMAL sync)
- ✅ Single point for configuration changes

**How to Migrate**:

```python
# ❌ Old way (direct sqlite3)
import sqlite3
from pathlib import Path
DB_PATH = Path(__file__).parent / "trades.db"
conn = sqlite3.connect(DB_PATH)
try:
    # ... operations
    conn.commit()
finally:
    conn.close()

# ✅ New way (unified config)
from data_lake import get_db_connection
with get_db_connection() as conn:
    # ... operations
    # Auto-commits on exit, auto-rollbacks on error
```

**Benefits**:
- No more manual `conn.close()` calls
- Automatic transaction management
- Consistent PRAGMA settings across all operations

---

### 4. Watchdog Simplification: Heartbeat + Account Monitoring → Account Monitoring Only

**What Changed**:
- **Before**: Watchdog monitored heartbeats AND account drawdown
- **After**: Watchdog only monitors account drawdown

**Why the Change**:
- Heartbeat monitoring only necessary for automatic loop detection
- In manual command mode, process state managed by Claude Code
- Simpler, more focused watchdog process

**How to Migrate**:

```python
# ✅ New watchdog behavior (simplified)
# Just run it - no heartbeat monitoring code needed
python runtime/watchdog.py

# It now only:
# - Monitors account drawdown (10% circuit breaker)
# - Triggers panic close if needed
# - NO heartbeat file checking
```

---

## 📋 Deprecated Components

### `runtime/main_loop.py` → `runtime/legacy/main_loop.py`

**Status**: Deprecated, moved to legacy

**What it did**: Automatic 5-minute trading loop

**Replacement**: Manual command mode + optional background daemons

**If you were using it**:
1. Stop the main_loop process
2. Switch to manual command triggering
3. Optionally run `data_sync_daemon.py` for background updates

---

### Redundant Data Sync Scripts

**Deleted**:
- `scripts/sync_with_rest_api.py`
- `scripts/run_sync_once.py`

**Reason**: Functionality consolidated into:
- Primary: Slash commands → `skills/workflow_skills.py`
- Secondary: `runtime/data_sync_daemon.py`

**Kept** (as example):
- `scripts/demo_incremental_sync.py` - Educational reference

---

## 🎯 Quick Migration Checklist

### For End Users

- [ ] Stop any running `main_loop.py` processes
- [ ] Learn new command-based workflow (see README.md)
- [ ] Verify `THETADATA_API_KEY` in `.env` (for REST API)
- [ ] Optionally: Set up `data_sync_daemon.py` for background updates

### For Developers

- [ ] Import from `data_lake` module (not individual files)
- [ ] Use `with get_db_connection()` context manager
- [ ] Remove manual `conn.close()` calls
- [ ] Update references to deleted sync scripts
- [ ] Use `skills/workflow_skills.py` for high-level operations

---

## 📚 Additional Resources

- **New Architecture**: See README.md §1 System Overview
- **Slash Commands**: See README.md §4 Usage Guide
- **Workflow Skills**: See `skills/workflow_skills.py`
- **Database Config**: See `data_lake/db_config.py`

---

## ❓ Troubleshooting

### "ImportError: cannot import name 'get_db_connection'"

**Solution**: Import from unified config
```python
from data_lake import get_db_connection  # ✅ Correct
# NOT: from data_lake.db_helpers import get_db_connection  # ❌ Old way
```

### "main_loop.py not found"

**Solution**: `main_loop.py` is deprecated
- Check `runtime/legacy/main_loop.py` if you need it
- Migrate to manual command mode instead

### "MCP ThetaData tool not found"

**Solution**: We no longer use MCP for ThetaData
- REST API is now used transparently
- Ensure `THETADATA_API_KEY` in `.env`
- Skills library handles API calls automatically

---

**Document Version**: 1.0
**Last Updated**: 2025-11-22
**Related Changes**: OpenSpec change `align-documentation`
