# market-data-storage Specification

## Purpose
TBD - created by archiving change refactor-market-data-cache. Update Purpose after archive.
## Requirements
### Requirement: 5-Minute Bar Storage
**Priority:** MUST
**Category:** Data Storage

The system MUST store 5-minute OHLCV bars for watchlist symbols with efficient indexing.

#### Scenario: Insert new market data bars

**Given** Symbol "AAPL" is in the watchlist
**When** Data fetcher retrieves 78 bars for a trading day
**Then** system inserts bars into `market_data_bars` table:
```sql
INSERT INTO market_data_bars (symbol, timestamp, open, high, low, close, volume, vwap)
VALUES ('AAPL', '2025-11-20T09:30:00', 150.25, 150.75, 149.90, 150.50, 1250000, 150.35);
```

**Verification:**
- Unique constraint on (symbol, timestamp) prevents duplicates
- Index on (symbol, timestamp) for fast queries
- VWAP (volume-weighted average price) calculated and stored
- Timestamp in ISO format for sorting

#### Scenario: Query historical bars for backtesting

**Given** "AAPL" has 3 years of 5-minute bars cached
**When** Strategy requests 30 days of data
**Then** system returns 2,340 bars in <10ms:
```python
bars = get_bars("AAPL", start="2025-10-21", end="2025-11-20", interval="5min")
assert len(bars) == 30 * 78  # 30 days × 78 bars/day
assert query_time_ms < 10
```

**Verification:**
- Query uses idx_bars_symbol_timestamp index
- Results ordered by timestamp ascending
- All OHLCV fields populated
- Performance <10ms for typical 30-day query

### Requirement: Interval Aggregation
**Priority:** MUST
**Category:** Data Transformation

The system MUST aggregate 5-minute bars to larger intervals (15min, 1h, daily) on-the-fly.

#### Scenario: Aggregate 5-min bars to 1-hour bars

**Given** Symbol "SPY" has 5-minute bars from 09:30 to 10:30
**When** Strategy requests 1-hour interval data
**Then** system aggregates 12 bars into 1 bar:
```python
bars_1h = get_bars("SPY", start="2025-11-20T09:30", end="2025-11-20T10:30", interval="1h")
assert len(bars_1h) == 1
assert bars_1h[0].open == bars_5min[0].open  # First bar's open
assert bars_1h[0].high == max(b.high for b in bars_5min)  # Max high
assert bars_1h[0].low == min(b.low for b in bars_5min)  # Min low
assert bars_1h[0].close == bars_5min[-1].close  # Last bar's close
assert bars_1h[0].volume == sum(b.volume for b in bars_5min)  # Sum volume
```

**Verification:**
- 15min interval: aggregate 3 bars (3 × 5min)
- 1h interval: aggregate 12 bars (12 × 5min)
- Daily interval: aggregate 78 bars (6.5 hour trading day)
- VWAP recalculated as volume-weighted average
- Aggregation time <2ms per symbol

### Requirement: Watchlist Management
**Priority:** MUST
**Category:** Configuration

The system MUST maintain a dynamic watchlist of symbols to track.

#### Scenario: Add symbol to watchlist

**Given** Symbol "NVDA" not in watchlist
**When** Commander adds symbol with priority 10
**Then** system inserts into watchlist table:
```sql
INSERT INTO watchlist (symbol, added_at, active, priority, notes)
VALUES ('NVDA', '2025-11-20T10:15:30', 1, 10, 'High volatility tech stock');
```

**Verification:**
- Symbol is primary key (no duplicates)
- Priority determines update order (higher first)
- Active flag enables/disables without deletion
- Notes field supports strategy metadata

#### Scenario: Query active watchlist symbols

**Given** Watchlist contains 50 symbols, 45 active
**When** Background updater queries active symbols
**Then** system returns 45 symbols ordered by priority:
```python
symbols = get_active_watchlist()
assert len(symbols) == 45
assert symbols[0].priority >= symbols[-1].priority  # Descending order
```

**Verification:**
- Only active=1 symbols returned
- Ordered by priority DESC
- Includes last_updated timestamp for each symbol

### Requirement: Data Freshness Tracking
**Priority:** MUST
**Category:** Monitoring

The system MUST track data freshness and detect gaps for each symbol.

#### Scenario: Update freshness after data fetch

**Given** "AAPL" has bars from 2023-01-01 to 2025-11-19
**When** Background updater fetches 2025-11-20 data
**Then** system updates data_freshness table:
```sql
UPDATE data_freshness
SET newest_bar = '2025-11-20T16:00:00',
    bar_count = 85410,  -- 3 years × 78 bars/day
    last_checked = '2025-11-20T16:05:00'
WHERE symbol = 'AAPL';
```

**Verification:**
- oldest_bar and newest_bar define coverage range
- bar_count matches actual rows in market_data_bars
- last_checked timestamp for monitoring staleness

#### Scenario: Detect data gap

**Given** "TSLA" missing bars from 2025-10-15 to 2025-10-16
**When** Gap detection runs
**Then** system records gap in data_freshness.gaps_detected:
```json
{
  "gaps": [
    {
      "start": "2025-10-15T09:30:00",
      "end": "2025-10-16T16:00:00",
      "missing_bars": 156
    }
  ]
}
```

**Verification:**
- Gap detected by comparing expected vs actual bar count
- Gap range recorded for backfill
- Logged to safety_events for alerting

### Requirement: Data Retention Policy
**Priority:** MUST
**Category:** Maintenance

The system MUST enforce a 3-year sliding window for historical data.

#### Scenario: Cleanup old data

**Given** Database contains bars from 2022-11-01 to 2025-11-20
**When** Cleanup task runs on 2025-11-20
**Then** system deletes bars older than 2022-11-20:
```sql
DELETE FROM market_data_bars
WHERE timestamp < '2022-11-20T00:00:00';
```

**Verification:**
- Runs monthly (first day of month)
- Deletes data older than 3 years (1095 days)
- Updates data_freshness.oldest_bar after cleanup
- Logs deleted bar count to safety_events

