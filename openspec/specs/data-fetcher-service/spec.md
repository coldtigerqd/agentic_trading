# data-fetcher-service Specification

## Purpose
TBD - created by archiving change refactor-market-data-cache. Update Purpose after archive.
## Requirements
### Requirement: Incremental Data Updates
**Priority:** MUST
**Category:** Background Task

The system MUST update watchlist symbols every 5 minutes during trading hours without blocking the main runtime.

#### Scenario: Update watchlist during trading hours

**Given** Current time is 2025-11-20 10:30 ET (market open)
**And** Watchlist contains 50 active symbols
**When** Background updater task runs
**Then** system fetches latest bars for all symbols:
```python
# Asyncio task in runtime/main_loop.py
async def market_data_updater_task():
    while True:
        if is_trading_hours():
            results = await update_watchlist_data()
            logger.info(f"Updated {len(results)} symbols")
        await asyncio.sleep(300)  # 5 minutes
```

**Verification:**
- Runs every 300 seconds (5 minutes)
- Only executes during market hours (09:30-16:00 ET)
- Non-blocking asyncio task
- Updates all active watchlist symbols
- Logs success/failure for each symbol

#### Scenario: Handle partial update failure

**Given** Watchlist has symbols ["AAPL", "GOOGL", "TSLA"]
**When** "GOOGL" fetch fails due to API error
**Then** system continues updating other symbols:
```python
results = {
    "AAPL": {"success": True, "bars_added": 1},
    "GOOGL": {"success": False, "error": "Rate limit exceeded"},
    "TSLA": {"success": True, "bars_added": 1}
}
```

**Verification:**
- Partial failures don't stop entire update
- Each symbol updated independently
- Errors logged to safety_events table
- Failed symbols retried on next cycle

### Requirement: ThetaData MCP Integration
**Priority:** MUST
**Category:** External API

The system MUST fetch historical and real-time data from ThetaData MCP server.

#### Scenario: Fetch historical data for new symbol

**Given** "NVDA" added to watchlist with no cached data
**When** Backfill task runs
**Then** system fetches 3 years of 5-minute bars via MCP:
```python
# Using ThetaData MCP tools (need to verify exact API)
bars = await fetch_historical_ohlc(
    symbol="NVDA",
    interval="5min",
    start_date="2022-11-20",
    end_date="2025-11-20"
)
# Expected: 85,410 bars (3 years × 78 bars/day)
```

**Verification:**
- Uses ThetaData MCP server at http://localhost:25503/mcp/sse
- Handles pagination if response size limited
- Converts ThetaData format to internal schema
- Inserts bars in batches of 100 for efficiency

#### Scenario: Fetch incremental update

**Given** "AAPL" has data up to 2025-11-20 09:25:00
**When** Updater runs at 09:30:00
**Then** system fetches only new bar:
```python
last_bar = get_newest_bar("AAPL")  # 09:25:00
new_bars = await fetch_ohlc_since(
    symbol="AAPL",
    since=last_bar.timestamp
)
assert len(new_bars) == 1  # Only 09:30:00 bar
```

**Verification:**
- Incremental fetch reduces API calls
- Only fetches bars newer than cached data
- Handles overlapping timestamps (upsert logic)

### Requirement: Trading Hours Detection
**Priority:** MUST
**Category:** Scheduling

The system MUST only update data during US market trading hours.

#### Scenario: Detect market open hours

**Given** Current datetime is 2025-11-20 10:30:00 ET (Wednesday)
**When** `is_trading_hours()` is called
**Then** function returns True

**Given** Current datetime is 2025-11-20 17:00:00 ET (after close)
**When** `is_trading_hours()` is called
**Then** function returns False

**Given** Current datetime is 2025-11-23 10:30:00 ET (Saturday)
**When** `is_trading_hours()` is called
**Then** function returns False

**Verification:**
- Trading hours: Mon-Fri 09:30-16:00 ET
- Handles timezone conversion correctly
- Considers market holidays (optional: use NYSE calendar)
- Pauses updates outside trading hours

### Requirement: Error Handling & Retry Logic
**Priority:** MUST
**Category:** Resilience

The system MUST handle API failures with exponential backoff and logging.

#### Scenario: Retry on API rate limit

**Given** ThetaData API returns 429 (rate limit exceeded)
**When** Fetcher attempts to update "AAPL"
**Then** system retries with exponential backoff:
```python
async def fetch_with_retry(symbol, max_retries=5):
    for attempt in range(max_retries):
        try:
            return await fetch_ohlc(symbol)
        except RateLimitError:
            wait_time = 2 ** attempt  # 1s, 2s, 4s, 8s, 16s
            logger.warning(f"Rate limit, retry in {wait_time}s")
            await asyncio.sleep(wait_time)
    raise MaxRetriesExceeded(symbol)
```

**Verification:**
- Exponential backoff: 1s, 2s, 4s, 8s, 16s
- Max 5 retries before giving up
- Logs each retry attempt
- Records final failure to safety_events

#### Scenario: Log API error

**Given** ThetaData API returns 500 (server error)
**When** Fetcher attempts to update "TSLA"
**Then** system logs error to safety_events:
```sql
INSERT INTO safety_events (timestamp, event_type, details, action_taken)
VALUES (
    '2025-11-20T10:35:00',
    'DATA_FETCH_FAILED',
    '{"symbol": "TSLA", "error": "API server error 500"}',
    'skipped_update'
);
```

**Verification:**
- All API errors logged
- Includes symbol, error message, timestamp
- Action taken recorded (retry, skip, etc.)

### Requirement: Lazy Backfill
**Priority:** MUST
**Category:** Optimization

The system MUST support on-demand backfill when data is first requested.

#### Scenario: Trigger backfill on first query

**Given** "META" is in watchlist but has no cached data
**When** Strategy calls `get_historical_bars("META", lookback_days=30)`
**Then** system triggers backfill for 30 days:
```python
def get_historical_bars(symbol, interval, lookback_days):
    bars = query_cached_bars(symbol, lookback_days)
    if len(bars) < expected_count:
        # Cache miss - fetch and cache
        bars = await backfill_symbol(symbol, days=lookback_days)
    return aggregate_bars(bars, interval)
```

**Verification:**
- Detects cache miss by bar count
- Fetches only requested range (not full 3 years)
- Subsequent queries use cached data
- Background updater maintains freshness

