# Design Document: Market Data Cache Architecture

**Change ID:** `refactor-market-data-cache`
**Status:** Draft
**Last Updated:** 2025-11-20

## Overview

This document describes the architectural decisions and technical design for implementing a high-performance market data cache that stores 3 years of historical OHLCV data at 5-minute intervals.

## Architecture Decisions

### 1. Storage: Same DB vs Separate DB

**Decision:** Extend existing `data_lake/trades.db` (rename to `trading_data.db`)

**Rationale:**
- Single database simplifies backup and atomic transactions
- Can correlate trades with market conditions in single query
- SQLite handles millions of rows efficiently with proper indexing
- Easier operational management (one file vs two)

**Migration Path:**
```sql
-- No actual rename needed - just add new tables to trades.db
-- Keep backward compatibility with existing code
```

**Trade-offs:**
- **Pro**: Simpler operations, atomic cross-table queries
- **Con**: Single point of failure (mitigated by WAL mode + backups)

---

### 2. Data Granularity: Store Multiple Intervals vs Compute On-the-Fly

**Decision:** Store only 5-minute bars, compute larger intervals (15min, 1h, daily) on-the-fly

**Rationale:**
- 5-minute is base granularity (user requirement)
- Aggregating 5min → 15min/1h/daily is fast (<1ms per symbol)
- Saves storage: 1 interval vs 4 intervals = 75% storage reduction
- Reduces API calls during backfill
- Flexible: can add new intervals without re-fetching

**Implementation:**
```python
def aggregate_bars(bars_5min, target_interval):
    """Aggregate 5-min bars to larger interval"""
    if target_interval == "5min":
        return bars_5min
    elif target_interval == "15min":
        return resample_ohlcv(bars_5min, period=3)
    elif target_interval == "1h":
        return resample_ohlcv(bars_5min, period=12)
    elif target_interval == "1d":
        return resample_ohlcv(bars_5min, period=78)  # 6.5hr trading day
```

**Trade-offs:**
- **Pro**: 75% storage savings, flexible interval support
- **Con**: 1-2ms compute overhead per query (acceptable)

---

### 3. Background Updater: Separate Process vs Asyncio Task

**Decision:** Asyncio task in runtime/main_loop.py (same pattern as swarm execution)

**Rationale:**
- Consistent with existing swarm concurrency model
- Shares database connection pool with main runtime
- Easy to coordinate with trading hours logic
- Simpler error handling and logging
- Can be disabled/enabled without separate process management

**Implementation:**
```python
async def market_data_updater_task():
    """Background task that updates watchlist data every 5 minutes"""
    while True:
        try:
            if is_trading_hours():
                await update_watchlist_data()
            await asyncio.sleep(300)  # 5 minutes
        except Exception as e:
            logger.error(f"Market data updater failed: {e}")
            await asyncio.sleep(60)  # Retry after 1 minute on error
```

**Trade-offs:**
- **Pro**: No additional process overhead, consistent patterns
- **Con**: Shares runtime resources (mitigated by non-blocking async)

---

### 4. Watchlist Management: Static Config vs Dynamic

**Decision:** Dynamic watchlist in SQLite table with add/remove skill functions

**Rationale:**
- Different strategies need different symbols
- Commander can dynamically add symbols as new signals emerge
- Avoids hardcoding symbol lists in config files
- Supports evolutionary learning (dream mode can adjust watchlist)

**Schema:**
```sql
CREATE TABLE watchlist (
    symbol TEXT PRIMARY KEY,
    added_at TEXT NOT NULL,
    active BOOLEAN DEFAULT 1,
    last_updated TEXT,
    priority INTEGER DEFAULT 0  -- Higher priority symbols updated first
);
```

**Trade-offs:**
- **Pro**: Flexible, supports dynamic strategy evolution
- **Con**: Requires database migration (minimal impact)

---

### 5. Data Backfill: Eager vs Lazy

**Decision:** Lazy backfill (fetch on-demand, then cache)

**Rationale:**
- 3 years × 50 symbols × 78 bars/day = 11.7M bars (hours of API time)
- ThetaData rate limits make full backfill slow
- Most strategies only need recent data initially
- On-demand fetching provides instant gratification

**Workflow:**
1. User/Swarm calls `get_historical_bars("AAPL", interval="5min", lookback_days=30)`
2. Check cache: if missing data, fetch from ThetaData and cache
3. Subsequent calls use cached data
4. Background updater maintains freshness for active watchlist

**Optimization:**
- Optional background backfill task during market close (22:00-09:00 ET)
- Prioritize recently added watchlist symbols

**Trade-offs:**
- **Pro**: Fast initial setup, efficient API usage
- **Con**: First query may be slow (one-time cost)

---

### 6. ThetaData MCP Integration

**Decision:** Use existing ThetaData MCP server (http://localhost:25503/mcp/sse)

**Rationale:**
- Already configured in project's MCP settings
- Consistent with project's MCP-first architecture
- Avoids direct API dependencies in skills code
- Benefits from MCP's error handling and retry logic

**Available Tools:**
```python
# From MCP server (confirmed in initial instructions)
- mcp__ThetaData__stock_snapshot_quote
- mcp__ThetaData__stock_snapshot_ohlc
- mcp__ThetaData__option_list_expirations
- mcp__ThetaData__option_list_strikes
- mcp__ThetaData__option_snapshot_quote
```

**Note:** Need to verify which historical data tools are available

**Trade-offs:**
- **Pro**: Consistent architecture, built-in error handling
- **Con**: Limited by MCP tool availability (need to check historical data access)

---

## Data Schema Design

### Market Data Tables

```sql
-- 5-minute OHLCV bars (base granularity)
CREATE TABLE market_data_bars (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    timestamp TEXT NOT NULL,  -- ISO format: 2025-11-20T09:30:00
    open REAL NOT NULL,
    high REAL NOT NULL,
    low REAL NOT NULL,
    close REAL NOT NULL,
    volume INTEGER NOT NULL,
    vwap REAL,  -- Volume-weighted average price
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(symbol, timestamp)
);

-- Watchlist for symbols to track
CREATE TABLE watchlist (
    symbol TEXT PRIMARY KEY,
    added_at TEXT NOT NULL,
    active BOOLEAN DEFAULT 1,
    last_updated TEXT,
    priority INTEGER DEFAULT 0,
    notes TEXT  -- Optional metadata (strategy tags, etc.)
);

-- Data freshness tracking
CREATE TABLE data_freshness (
    symbol TEXT PRIMARY KEY,
    oldest_bar TEXT,  -- Oldest bar timestamp in cache
    newest_bar TEXT,  -- Newest bar timestamp in cache
    bar_count INTEGER DEFAULT 0,
    last_checked TEXT,
    gaps_detected TEXT  -- JSON array of detected gap ranges
);

-- Indexes for performance
CREATE INDEX idx_bars_symbol ON market_data_bars(symbol);
CREATE INDEX idx_bars_timestamp ON market_data_bars(timestamp);
CREATE INDEX idx_bars_symbol_timestamp ON market_data_bars(symbol, timestamp);
CREATE INDEX idx_watchlist_active ON watchlist(active);
CREATE INDEX idx_watchlist_priority ON watchlist(priority DESC);
```

**Storage Estimates:**
- 1 bar = ~100 bytes (7 floats + metadata)
- 1 symbol × 3 years × 78 bars/day = 85,410 bars = ~8.5MB
- 50 symbols = ~425MB (under 500MB target)

---

## Component Design

### 1. Market Data Manager (`data_lake/market_data_manager.py`)

**Responsibilities:**
- Insert/query market data bars
- Aggregate 5min bars to larger intervals
- Detect and report data gaps
- Manage data retention (3-year sliding window)

**Key Functions:**
```python
def insert_bars(symbol: str, bars: List[OHLCVBar]) -> int
def get_bars(symbol: str, start: datetime, end: datetime, interval: str = "5min") -> List[OHLCVBar]
def detect_gaps(symbol: str) -> List[Tuple[datetime, datetime]]
def cleanup_old_data(cutoff_date: datetime) -> int
```

---

### 2. Data Fetcher Service (`runtime/data_fetcher.py`)

**Responsibilities:**
- Fetch historical data from ThetaData MCP
- Incremental updates every 5 minutes
- Handle API errors and rate limits
- Track data freshness

**Key Functions:**
```python
async def update_watchlist_data() -> Dict[str, UpdateResult]
async def backfill_symbol(symbol: str, days: int = 1095) -> int
def is_trading_hours() -> bool
```

---

### 3. Market Data Skill (`skills/market_data.py`)

**Responsibilities:**
- Expose market data to Claude Code
- Handle lazy loading (fetch if missing)
- Support multi-timeframe queries

**Key Functions:**
```python
def get_historical_bars(symbol: str, interval: str = "5min", lookback_days: int = 30) -> Dict
def get_latest_price(symbol: str) -> Dict
def add_to_watchlist(symbol: str, priority: int = 0, notes: str = "") -> Dict
def remove_from_watchlist(symbol: str) -> Dict
def get_watchlist() -> List[Dict]
def get_multi_timeframe_data(symbol: str, intervals: List[str], lookback_days: int = 30) -> Dict
```

---

## Error Handling & Resilience

### API Failures
- **Exponential backoff**: 1s, 2s, 4s, 8s, 16s max
- **Partial success**: Continue updating other symbols if one fails
- **Logging**: Record all API failures to safety_events table

### Data Gaps
- **Detection**: Compare expected vs actual bar count
- **Backfill**: Automatically fetch missing data on next update
- **Alerting**: Log gaps to data_freshness.gaps_detected

### Database Errors
- **WAL mode**: Enable for concurrent reads during writes
- **Atomic transactions**: Use BEGIN/COMMIT for multi-bar inserts
- **Backup**: Daily snapshot to data_lake/backups/

---

## Performance Optimization

### Query Optimization
```sql
-- Optimized query for 30-day lookback (typical use case)
SELECT * FROM market_data_bars
WHERE symbol = ? AND timestamp >= ?
ORDER BY timestamp ASC;

-- Uses idx_bars_symbol_timestamp for fast retrieval
-- Expected: <5ms for 2,340 bars (30 days × 78 bars/day)
```

### Batch Operations
- Insert bars in batches of 100 (reduce transaction overhead)
- Update multiple symbols in parallel (asyncio.gather)

### Caching
- In-memory cache for last 24 hours of frequently accessed symbols
- LRU eviction policy (max 100MB memory)

---

## Validation Strategy

### Phase 1: Schema & Storage (Unit Tests)
```python
def test_insert_bars()
def test_query_performance()
def test_interval_aggregation()
def test_gap_detection()
```

### Phase 2: ThetaData Integration (Integration Tests)
```python
def test_fetch_historical_data()
def test_data_format_conversion()
def test_error_handling()
```

### Phase 3: Background Updater (System Tests)
```python
def test_updater_task_lifecycle()
def test_trading_hours_detection()
def test_incremental_updates()
```

### Phase 4: Skill Integration (End-to-End)
```python
def test_skill_query_performance()
def test_lazy_loading()
def test_multi_timeframe_query()
```

---

## Risks & Mitigation

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| ThetaData API rate limits | High | Medium | Exponential backoff, batch requests, lazy loading |
| SQLite database corruption | Critical | Low | WAL mode, atomic transactions, daily backups |
| Background updater blocks runtime | High | Low | Asyncio non-blocking, timeout on API calls |
| Storage exceeds 500MB | Medium | Low | Monitor DB size, 3-year retention policy |
| Data gaps during market hours | Medium | Medium | Gap detection, auto-backfill, alerting |

---

## Future Enhancements

1. **Compressed storage**: Use delta encoding for OHLC values (50% size reduction)
2. **Multi-asset support**: Extend to crypto, futures (requires new ThetaData endpoints)
3. **Real-time streaming**: WebSocket integration for sub-minute updates
4. **Distributed cache**: Redis for multi-instance deployments
