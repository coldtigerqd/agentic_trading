"""
Data Fetcher Service for Market Data Cache

Provides functions for fetching and caching market data from ThetaData MCP.

IMPORTANT: These functions are designed to work with Claude Code's MCP integration.
Claude Code calls ThetaData MCP tools and passes results to these functions for processing.
"""

import asyncio
from datetime import datetime, timedelta, time
from typing import List, Dict, Optional
from zoneinfo import ZoneInfo
from data_lake.market_data_manager import (
    OHLCVBar,
    insert_bars,
    get_latest_bar,
    get_freshness_info
)
from data_lake.db_helpers import log_safety_event, get_db_connection


# US Eastern timezone for market hours
ET = ZoneInfo("America/New_York")


def is_trading_hours() -> bool:
    """
    Check if current time is during US market trading hours.

    Trading hours: Monday-Friday 09:30-16:00 ET

    Returns:
        True if market is currently open
    """
    now_et = datetime.now(ET)

    # Check if weekend
    if now_et.weekday() >= 5:  # Saturday=5, Sunday=6
        return False

    # Check if within trading hours (09:30-16:00 ET)
    market_open = time(9, 30)
    market_close = time(16, 0)
    current_time = now_et.time()

    return market_open <= current_time <= market_close


def process_thetadata_ohlc(
    symbol: str,
    thetadata_result: Dict,
    timestamp: Optional[str] = None
) -> Dict:
    """
    Process ThetaData OHLC result and cache it.

    This function should be called by Claude Code after fetching data
    from mcp__ThetaData__stock_snapshot_ohlc.

    Args:
        symbol: Stock symbol (e.g., "AAPL")
        thetadata_result: Result from ThetaData MCP tool
        timestamp: Optional timestamp (ISO format). If None, uses current 5-min interval

    Returns:
        Dict with status and cached bar info

    Example:
        ```python
        # Claude Code fetches from ThetaData MCP
        result = mcp__ThetaData__stock_snapshot_ohlc(symbol="AAPL")

        # Process and cache the result
        from runtime.data_fetcher import process_thetadata_ohlc
        cached = process_thetadata_ohlc("AAPL", result)

        if cached["success"]:
            print(f"✓ Cached AAPL bar at {cached['timestamp']}")
        ```
    """
    try:
        # Determine timestamp (round to nearest 5-min interval)
        if timestamp is None:
            now = datetime.now(ET)
            # Round down to nearest 5-minute interval
            minutes = (now.minute // 5) * 5
            timestamp = now.replace(minute=minutes, second=0, microsecond=0).isoformat()

        # Extract OHLCV data from ThetaData result
        # Note: Adjust field names based on actual ThetaData MCP response format
        bar = OHLCVBar(
            symbol=symbol,
            timestamp=timestamp,
            open=float(thetadata_result.get("open", 0)),
            high=float(thetadata_result.get("high", 0)),
            low=float(thetadata_result.get("low", 0)),
            close=float(thetadata_result.get("close", 0)),
            volume=int(thetadata_result.get("volume", 0)),
            vwap=float(thetadata_result.get("vwap")) if thetadata_result.get("vwap") else None
        )

        # Insert into database
        count = insert_bars(symbol, [bar])

        return {
            "success": True,
            "symbol": symbol,
            "timestamp": timestamp,
            "bars_added": count,
            "bar": bar.to_dict()
        }

    except Exception as e:
        # Log error to safety_events
        log_safety_event(
            event_type="DATA_FETCH_FAILED",
            details={"symbol": symbol, "error": str(e)},
            action_taken="skipped_update"
        )

        return {
            "success": False,
            "symbol": symbol,
            "error": str(e)
        }


async def update_watchlist_data() -> Dict[str, Dict]:
    """
    Update market data for all active watchlist symbols.

    This is an async task designed to run in the background.
    Claude Code should call ThetaData MCP for each symbol and
    pass results to process_thetadata_ohlc().

    Returns:
        Dictionary mapping symbols to update results

    Example usage in runtime loop:
        ```python
        # In main_loop.py:
        async def market_data_updater_task():
            while True:
                if is_trading_hours():
                    # This would be orchestrated by Claude Code
                    results = await update_watchlist_data()
                    logger.info(f"Updated {len(results)} symbols")

                await asyncio.sleep(300)  # 5 minutes
        ```
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Get active watchlist symbols ordered by priority
        cursor.execute("""
            SELECT symbol, priority FROM watchlist
            WHERE active = 1
            ORDER BY priority DESC, symbol ASC
        """)

        symbols = [(row["symbol"], row["priority"]) for row in cursor.fetchall()]

    if not symbols:
        return {}

    results = {}

    # Note: Actual fetching would be done by Claude Code calling ThetaData MCP
    # This function provides the structure for processing results

    for symbol, priority in symbols:
        # In actual runtime, Claude Code would:
        # 1. Call mcp__ThetaData__stock_snapshot_ohlc(symbol=symbol)
        # 2. Pass result to process_thetadata_ohlc()
        # 3. Store result in results dict

        # Placeholder for structure
        results[symbol] = {
            "symbol": symbol,
            "priority": priority,
            "status": "pending_mcp_call"
        }

    return results


async def backfill_symbol(symbol: str, days: int = 30) -> Dict:
    """
    Backfill historical data for a symbol.

    This function requests backfill for N days of historical data.
    Claude Code should call ThetaData MCP historical endpoint (if available)
    or fetch day-by-day snapshots.

    Args:
        symbol: Stock symbol
        days: Number of days to backfill (default 30)

    Returns:
        Dict with backfill status

    Example:
        ```python
        # Triggered when user adds new symbol to watchlist
        from runtime.data_fetcher import backfill_symbol

        result = await backfill_symbol("NVDA", days=30)

        if result["success"]:
            print(f"✓ Backfilled {result['bars_added']} bars for NVDA")
        ```
    """
    try:
        # Check if data already exists
        freshness = get_freshness_info(symbol)
        if freshness and freshness["bar_count"] > 0:
            # Data exists, calculate how many days to backfill
            newest = datetime.fromisoformat(freshness["newest_bar"])
            now = datetime.now(ET)
            days_missing = (now - newest).days

            if days_missing <= 1:
                # Data is fresh
                return {
                    "success": True,
                    "symbol": symbol,
                    "bars_added": 0,
                    "message": "Data already up to date"
                }

            # Adjust backfill days
            days = min(days, days_missing)

        # In actual implementation, Claude Code would:
        # 1. Calculate date range (now - days to now)
        # 2. Call ThetaData MCP historical endpoint
        # 3. Process results with process_thetadata_ohlc()

        return {
            "success": True,
            "symbol": symbol,
            "bars_requested": days * 78,  # ~78 bars per trading day
            "status": "pending_mcp_historical_call"
        }

    except Exception as e:
        log_safety_event(
            event_type="BACKFILL_FAILED",
            details={"symbol": symbol, "days": days, "error": str(e)},
            action_taken="backfill_skipped"
        )

        return {
            "success": False,
            "symbol": symbol,
            "error": str(e)
        }


async def fetch_with_retry(
    fetch_func,
    max_retries: int = 5,
    initial_delay: float = 1.0
) -> Dict:
    """
    Retry a fetch operation with exponential backoff.

    Args:
        fetch_func: Async function to call (should return Dict)
        max_retries: Maximum number of retries
        initial_delay: Initial delay in seconds

    Returns:
        Result from fetch_func or error dict
    """
    delay = initial_delay

    for attempt in range(max_retries):
        try:
            result = await fetch_func()
            return result
        except Exception as e:
            if attempt == max_retries - 1:
                # Last attempt failed
                return {
                    "success": False,
                    "error": f"Max retries exceeded: {str(e)}",
                    "attempts": attempt + 1
                }

            # Log retry
            log_safety_event(
                event_type="DATA_FETCH_RETRY",
                details={"attempt": attempt + 1, "delay": delay, "error": str(e)},
                action_taken="retrying"
            )

            # Exponential backoff
            await asyncio.sleep(delay)
            delay *= 2  # 1s, 2s, 4s, 8s, 16s

    return {
        "success": False,
        "error": "Unexpected retry loop exit"
    }


def get_active_watchlist() -> List[Dict]:
    """
    Get all active symbols in the watchlist.

    Returns:
        List of dictionaries with symbol info
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT symbol, priority, added_at, last_updated, notes
            FROM watchlist
            WHERE active = 1
            ORDER BY priority DESC, symbol ASC
        """)

        symbols = [
            {
                "symbol": row["symbol"],
                "priority": row["priority"],
                "added_at": row["added_at"],
                "last_updated": row["last_updated"],
                "notes": row["notes"]
            }
            for row in cursor.fetchall()
        ]

    return symbols


def add_to_watchlist(
    symbol: str,
    priority: int = 0,
    notes: str = ""
) -> Dict:
    """
    Add a symbol to the watchlist.

    Args:
        symbol: Stock symbol (uppercase)
        priority: Priority level (higher = updated first)
        notes: Optional notes/tags

    Returns:
        Dict with status
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                INSERT OR REPLACE INTO watchlist
                (symbol, added_at, active, priority, notes)
                VALUES (?, ?, 1, ?, ?)
            """, (symbol.upper(), datetime.now().isoformat(), priority, notes))

            conn.commit()

        return {
            "success": True,
            "symbol": symbol.upper(),
            "priority": priority,
            "message": f"Added {symbol} to watchlist"
        }

    except Exception as e:
        return {
            "success": False,
            "symbol": symbol,
            "error": str(e)
        }


def remove_from_watchlist(symbol: str) -> Dict:
    """
    Remove a symbol from the watchlist (soft delete).

    Sets active=0 but retains cached data.

    Args:
        symbol: Stock symbol

    Returns:
        Dict with status
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE watchlist
                SET active = 0
                WHERE symbol = ?
            """, (symbol.upper(),))

            conn.commit()
            rows_affected = cursor.rowcount

        if rows_affected > 0:
            return {
                "success": True,
                "symbol": symbol.upper(),
                "message": f"Removed {symbol} from watchlist (data retained)"
            }
        else:
            return {
                "success": False,
                "symbol": symbol,
                "error": "Symbol not found in watchlist"
            }

    except Exception as e:
        return {
            "success": False,
            "symbol": symbol,
            "error": str(e)
        }


# === USAGE GUIDE FOR CLAUDE CODE ===
"""
Background Market Data Updater Pattern:

```python
# In runtime/main_loop.py, add this async task:

async def market_data_updater_task():
    from runtime.data_fetcher import (
        is_trading_hours,
        get_active_watchlist,
        process_thetadata_ohlc
    )
    import asyncio

    while True:
        try:
            if is_trading_hours():
                # Get symbols to update
                watchlist = get_active_watchlist()

                for symbol_info in watchlist:
                    symbol = symbol_info["symbol"]

                    try:
                        # Fetch from ThetaData MCP
                        ohlc_data = mcp__ThetaData__stock_snapshot_ohlc(symbol=symbol)

                        # Process and cache
                        result = process_thetadata_ohlc(symbol, ohlc_data)

                        if result["success"]:
                            print(f"✓ Updated {symbol} at {result['timestamp']}")
                        else:
                            print(f"✗ Failed to update {symbol}: {result['error']}")

                    except Exception as e:
                        print(f"✗ Error fetching {symbol}: {e}")
                        continue

            # Wait 5 minutes before next update
            await asyncio.sleep(300)

        except Exception as e:
            print(f"✗ Market data updater error: {e}")
            await asyncio.sleep(60)  # Retry after 1 minute on error


# Start the updater in main loop
asyncio.create_task(market_data_updater_task())
```

Manual Backfill Pattern:

```python
# Add symbol and backfill
from runtime.data_fetcher import add_to_watchlist, backfill_symbol

# Add to watchlist
result = add_to_watchlist("TSLA", priority=8, notes="High momentum stock")

if result["success"]:
    # Backfill 30 days of data
    backfill_result = await backfill_symbol("TSLA", days=30)
    print(f"Backfill status: {backfill_result}")
```
"""
