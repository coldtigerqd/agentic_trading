# market-data-skill Specification

## Purpose
TBD - created by archiving change refactor-market-data-cache. Update Purpose after archive.
## Requirements
### Requirement: Historical Bars Query
**Priority:** MUST
**Category:** Skill Function

The system MUST provide a skill function to query historical bars with flexible parameters.

#### Scenario: Query 30 days of 5-minute bars

**Given** "AAPL" has 3 years of cached data
**When** Commander calls skill function:
```python
result = get_historical_bars(
    symbol="AAPL",
    interval="5min",
    lookback_days=30
)
```
**Then** system returns dictionary with bars:
```python
{
    "symbol": "AAPL",
    "interval": "5min",
    "bars": [
        {
            "timestamp": "2025-10-21T09:30:00",
            "open": 150.25,
            "high": 150.75,
            "low": 149.90,
            "close": 150.50,
            "volume": 1250000,
            "vwap": 150.35
        },
        # ... 2,339 more bars
    ],
    "bar_count": 2340,
    "query_time_ms": 8,
    "cache_hit": true
}
```

**Verification:**
- Returns all OHLCV fields plus VWAP
- Bar count matches expected (30 days × 78 bars/day)
- Query time <10ms for cached data
- Handles cache miss with lazy backfill

#### Scenario: Query 1-hour bars

**Given** "SPY" has 5-minute bars cached
**When** Swarm agent requests 1-hour interval:
```python
result = get_historical_bars(
    symbol="SPY",
    interval="1h",
    lookback_days=7
)
```
**Then** system aggregates and returns:
```python
{
    "symbol": "SPY",
    "interval": "1h",
    "bars": [
        # 7 days × 6.5 hours/day = 45.5 hours ≈ 46 bars
    ],
    "bar_count": 46,
    "query_time_ms": 12,
    "cache_hit": true,
    "aggregated_from": "5min"
}
```

**Verification:**
- Supports intervals: "5min", "15min", "1h", "daily"
- Aggregation preserves OHLCV correctness
- Query time <15ms including aggregation

### Requirement: Latest Price Query
**Priority:** MUST
**Category:** Skill Function

The system MUST provide a skill function to get the latest price for a symbol.

#### Scenario: Get current price

**Given** "NVDA" has latest bar at 2025-11-20 15:55:00
**When** Commander calls:
```python
result = get_latest_price(symbol="NVDA")
```
**Then** system returns latest bar:
```python
{
    "symbol": "NVDA",
    "timestamp": "2025-11-20T15:55:00",
    "price": 495.75,
    "open": 493.50,
    "high": 496.20,
    "low": 492.80,
    "close": 495.75,
    "volume": 875000,
    "vwap": 494.90,
    "age_seconds": 300  # 5 minutes old
}
```

**Verification:**
- Returns most recent cached bar
- Includes age_seconds for staleness check
- Fast query (<5ms)

### Requirement: Watchlist Management Skills
**Priority:** MUST
**Category:** Skill Function

The system MUST provide skill functions to manage the watchlist dynamically.

#### Scenario: Add symbol to watchlist

**Given** "TSLA" not in watchlist
**When** Commander decides to track new symbol:
```python
result = add_to_watchlist(
    symbol="TSLA",
    priority=8,
    notes="High volume momentum stock"
)
```
**Then** system adds to watchlist and triggers backfill:
```python
{
    "symbol": "TSLA",
    "added": true,
    "priority": 8,
    "backfill_started": true,
    "backfill_days": 30  # Default initial backfill
}
```

**Verification:**
- Symbol added to watchlist table
- Background updater will maintain freshness
- Optional immediate backfill for recent data
- Returns confirmation with status

#### Scenario: Remove symbol from watchlist

**Given** "GME" in watchlist with low priority
**When** Commander removes low-priority symbol:
```python
result = remove_from_watchlist(symbol="GME")
```
**Then** system marks as inactive (soft delete):
```python
{
    "symbol": "GME",
    "removed": true,
    "data_retained": true,  # Cached data not deleted
    "can_reactivate": true
}
```

**Verification:**
- Sets active=0 in watchlist table
- Cached data retained for potential reactivation
- Background updater stops updating this symbol

#### Scenario: Get current watchlist

**Given** Watchlist has 50 symbols
**When** Commander queries watchlist:
```python
result = get_watchlist()
```
**Then** system returns all active symbols:
```python
{
    "symbols": [
        {
            "symbol": "SPY",
            "priority": 10,
            "added_at": "2025-11-01T10:00:00",
            "last_updated": "2025-11-20T15:55:00",
            "notes": "S&P 500 ETF"
        },
        # ... 49 more
    ],
    "total_count": 50
}
```

**Verification:**
- Only returns active symbols
- Ordered by priority descending
- Includes last_updated for staleness check

### Requirement: Multi-Timeframe Query
**Priority:** MUST
**Category:** Skill Function

The system MUST support querying multiple intervals in a single call.

#### Scenario: Get multi-timeframe data for technical analysis

**Given** "AAPL" has complete historical data
**When** Swarm agent needs multiple timeframes:
```python
result = get_multi_timeframe_data(
    symbol="AAPL",
    intervals=["5min", "1h", "daily"],
    lookback_days=30
)
```
**Then** system returns data for all intervals:
```python
{
    "symbol": "AAPL",
    "lookback_days": 30,
    "timeframes": {
        "5min": {
            "bars": [...],  # 2,340 bars
            "bar_count": 2340
        },
        "1h": {
            "bars": [...],  # 195 bars
            "bar_count": 195
        },
        "daily": {
            "bars": [...],  # 30 bars
            "bar_count": 30
        }
    },
    "query_time_ms": 25
}
```

**Verification:**
- Single database query + multiple aggregations
- More efficient than separate calls
- Useful for multi-timeframe analysis strategies

### Requirement: Data Quality Indicators
**Priority:** MUST
**Category:** Monitoring

The system MUST include data quality indicators in skill responses.

#### Scenario: Return data freshness info

**Given** "GOOGL" last updated 10 minutes ago
**When** Swarm queries historical data
**Then** response includes freshness indicators:
```python
{
    "symbol": "GOOGL",
    "bars": [...],
    "data_quality": {
        "freshness_seconds": 600,  # 10 minutes old
        "coverage_start": "2022-11-20T09:30:00",
        "coverage_end": "2025-11-20T15:55:00",
        "total_bars": 85410,
        "gaps_detected": 0,
        "last_updated": "2025-11-20T15:55:00"
    }
}
```

**Verification:**
- Freshness measured from newest bar timestamp
- Coverage range shows available data
- Gaps indicator warns of incomplete data

