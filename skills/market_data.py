"""
Market Data Skill - Claude Code callable market data functions.

Provides historical OHLCV data access, watchlist management, and data quality indicators.
"""

import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from data_lake.market_data_manager import (
    get_bars,
    get_latest_bar,
    get_freshness_info,
    OHLCVBar
)
from runtime.data_fetcher import (
    get_active_watchlist,
    add_to_watchlist as _add_to_watchlist,
    remove_from_watchlist as _remove_from_watchlist
)


def get_historical_bars(
    symbol: str,
    interval: str = "5min",
    lookback_days: int = 30
) -> Dict:
    """
    Query historical OHLCV bars for a symbol.

    Supports multiple intervals with on-the-fly aggregation from 5-minute base data.
    If data is missing, returns cache_hit=false to signal lazy backfill needed.

    Args:
        symbol: Stock symbol (e.g., "AAPL")
        interval: Bar interval - "5min", "15min", "1h", or "daily"
        lookback_days: Number of days to look back

    Returns:
        Dictionary with bars and metadata

    Example:
        ```python
        # Get 30 days of 5-minute bars
        result = get_historical_bars("AAPL", interval="5min", lookback_days=30)

        if result["cache_hit"]:
            print(f"Retrieved {result['bar_count']} bars")
            for bar in result["bars"][:5]:  # First 5 bars
                print(f"{bar['timestamp']}: ${bar['close']}")
        else:
            print(f"Cache miss - need to backfill {symbol}")
        ```
    """
    start_time = time.time()

    # Calculate date range
    end = datetime.now()
    start = end - timedelta(days=lookback_days)

    # Query bars
    try:
        bars = get_bars(symbol.upper(), start, end, interval)

        # Convert to dict format
        bars_dict = [bar.to_dict() for bar in bars]

        # Expected bar count (approximate)
        trading_days = lookback_days * (5/7)  # ~5 trading days per week
        if interval == "5min":
            expected_bars = int(trading_days * 78)  # 78 bars per day
        elif interval == "15min":
            expected_bars = int(trading_days * 26)  # 26 bars per day
        elif interval == "1h":
            expected_bars = int(trading_days * 6.5)  # 6.5 hours per day
        else:  # daily
            expected_bars = int(trading_days)

        # Check cache hit rate
        cache_hit = len(bars) >= (expected_bars * 0.8)  # 80% threshold

        # Get data quality info
        freshness = get_freshness_info(symbol.upper())

        query_time_ms = int((time.time() - start_time) * 1000)

        return {
            "symbol": symbol.upper(),
            "interval": interval,
            "lookback_days": lookback_days,
            "bars": bars_dict,
            "bar_count": len(bars),
            "expected_bars": expected_bars,
            "cache_hit": cache_hit,
            "query_time_ms": query_time_ms,
            "data_quality": {
                "freshness_seconds": _calculate_freshness_seconds(freshness) if freshness else None,
                "coverage_start": freshness["oldest_bar"] if freshness else None,
                "coverage_end": freshness["newest_bar"] if freshness else None,
                "total_bars_cached": freshness["bar_count"] if freshness else 0,
                "gaps_detected": len(freshness["gaps_detected"]["gaps"]) if freshness else 0
            }
        }

    except Exception as e:
        return {
            "symbol": symbol.upper(),
            "interval": interval,
            "lookback_days": lookback_days,
            "bars": [],
            "bar_count": 0,
            "cache_hit": False,
            "error": str(e),
            "message": "Failed to query historical bars - may need backfill"
        }


def get_latest_price(symbol: str) -> Dict:
    """
    Get the most recent cached price for a symbol.

    Args:
        symbol: Stock symbol (e.g., "NVDA")

    Returns:
        Dictionary with latest bar and staleness info

    Example:
        ```python
        result = get_latest_price("NVDA")

        if result["success"]:
            print(f"NVDA: ${result['price']}")
            print(f"Data age: {result['age_seconds']}s")

            if result["age_seconds"] > 600:  # 10 minutes
                print("⚠️ Data is stale - consider updating")
        ```
    """
    try:
        latest = get_latest_bar(symbol.upper())

        if not latest:
            return {
                "success": False,
                "symbol": symbol.upper(),
                "error": "No data available",
                "message": "Symbol not in cache - add to watchlist and backfill"
            }

        # Calculate age
        bar_time = datetime.fromisoformat(latest.timestamp)
        age_seconds = int((datetime.now() - bar_time).total_seconds())

        return {
            "success": True,
            "symbol": latest.symbol,
            "timestamp": latest.timestamp,
            "price": latest.close,
            "open": latest.open,
            "high": latest.high,
            "low": latest.low,
            "close": latest.close,
            "volume": latest.volume,
            "vwap": latest.vwap,
            "age_seconds": age_seconds,
            "is_stale": age_seconds > 600  # 10 minutes threshold
        }

    except Exception as e:
        return {
            "success": False,
            "symbol": symbol.upper(),
            "error": str(e)
        }


def add_to_watchlist(
    symbol: str,
    priority: int = 0,
    notes: str = ""
) -> Dict:
    """
    Add a symbol to the active watchlist.

    Once added, the background updater will maintain fresh data for this symbol.

    Args:
        symbol: Stock symbol (uppercase)
        priority: Priority level (0-10, higher = updated first)
        notes: Optional notes/tags for organizing symbols

    Returns:
        Dictionary with status and next steps

    Example:
        ```python
        # Add TSLA to watchlist with high priority
        result = add_to_watchlist("TSLA", priority=8, notes="High momentum stock")

        if result["success"]:
            print(f"✓ Added {result['symbol']} to watchlist")
            print(f"  Next: Trigger backfill for historical data")
        ```
    """
    result = _add_to_watchlist(symbol.upper(), priority, notes)

    if result["success"]:
        result["next_steps"] = [
            "1. Symbol added to watchlist",
            "2. Background updater will fetch new bars every 5 minutes",
            "3. Consider calling backfill_symbol() for historical data"
        ]

    return result


def remove_from_watchlist(symbol: str) -> Dict:
    """
    Remove a symbol from the watchlist (soft delete).

    Stops background updates but retains cached data.

    Args:
        symbol: Stock symbol

    Returns:
        Dictionary with status

    Example:
        ```python
        result = remove_from_watchlist("GME")

        if result["success"]:
            print(f"✓ Removed {symbol} from active watchlist")
            print(f"  Cached data retained for queries")
        ```
    """
    return _remove_from_watchlist(symbol.upper())


def get_watchlist() -> Dict:
    """
    Get all active symbols in the watchlist with status info.

    Returns:
        Dictionary with watchlist symbols and metadata

    Example:
        ```python
        result = get_watchlist()

        print(f"Active symbols: {result['total_count']}")
        for symbol_info in result["symbols"]:
            print(f"  {symbol_info['symbol']:6s} (P={symbol_info['priority']})")
        ```
    """
    try:
        symbols = get_active_watchlist()

        # Add freshness info for each symbol
        for symbol_info in symbols:
            freshness = get_freshness_info(symbol_info["symbol"])
            if freshness:
                symbol_info["data_status"] = {
                    "bars_cached": freshness["bar_count"],
                    "newest_bar": freshness["newest_bar"],
                    "freshness_seconds": _calculate_freshness_seconds(freshness)
                }
            else:
                symbol_info["data_status"] = {
                    "bars_cached": 0,
                    "newest_bar": None,
                    "freshness_seconds": None
                }

        return {
            "success": True,
            "symbols": symbols,
            "total_count": len(symbols)
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "symbols": [],
            "total_count": 0
        }


def get_multi_timeframe_data(
    symbol: str,
    intervals: List[str],
    lookback_days: int = 30
) -> Dict:
    """
    Get historical data for multiple timeframes in a single call.

    More efficient than calling get_historical_bars() multiple times.

    Args:
        symbol: Stock symbol
        intervals: List of intervals (e.g., ["5min", "1h", "daily"])
        lookback_days: Number of days to look back

    Returns:
        Dictionary with data for each timeframe

    Example:
        ```python
        # Get multi-timeframe data for technical analysis
        result = get_multi_timeframe_data(
            symbol="AAPL",
            intervals=["5min", "1h", "daily"],
            lookback_days=30
        )

        if result["success"]:
            print(f"5min bars: {result['timeframes']['5min']['bar_count']}")
            print(f"1h bars: {result['timeframes']['1h']['bar_count']}")
            print(f"Daily bars: {result['timeframes']['daily']['bar_count']}")
        ```
    """
    start_time = time.time()

    try:
        timeframes = {}

        for interval in intervals:
            data = get_historical_bars(symbol, interval, lookback_days)
            timeframes[interval] = {
                "bars": data["bars"],
                "bar_count": data["bar_count"],
                "cache_hit": data["cache_hit"]
            }

        query_time_ms = int((time.time() - start_time) * 1000)

        return {
            "success": True,
            "symbol": symbol.upper(),
            "lookback_days": lookback_days,
            "timeframes": timeframes,
            "query_time_ms": query_time_ms
        }

    except Exception as e:
        return {
            "success": False,
            "symbol": symbol.upper(),
            "error": str(e),
            "timeframes": {}
        }


def _calculate_freshness_seconds(freshness_info: Dict) -> Optional[int]:
    """Calculate how many seconds old the newest bar is"""
    if not freshness_info or not freshness_info.get("newest_bar"):
        return None

    newest = datetime.fromisoformat(freshness_info["newest_bar"])
    age = datetime.now() - newest
    return int(age.total_seconds())


# === SKILL REGISTRATION INFO ===
"""
These functions are designed to be called by Claude Code:

**Historical Analysis:**
- get_historical_bars(symbol, interval, lookback_days)
- get_multi_timeframe_data(symbol, intervals, lookback_days)

**Real-time Queries:**
- get_latest_price(symbol)
- get_watchlist()

**Watchlist Management:**
- add_to_watchlist(symbol, priority, notes)
- remove_from_watchlist(symbol)

**Example Commander Workflow:**

```python
# Check watchlist status
watchlist = get_watchlist()
print(f"Tracking {watchlist['total_count']} symbols")

# Add new symbol for analysis
add_result = add_to_watchlist("MSFT", priority=7, notes="Big tech")

# Get multi-timeframe data for strategy analysis
mtf_data = get_multi_timeframe_data(
    symbol="AAPL",
    intervals=["5min", "1h", "daily"],
    lookback_days=30
)

# Pass to swarm for analysis
from skills import consult_swarm
signals = consult_swarm(
    sector="TECH",
    market_data={
        "multi_timeframe": mtf_data,
        "watchlist": watchlist
    }
)
```
"""
