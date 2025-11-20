#!/usr/bin/env python3
"""
Fetch Real Market Data via MCP Tools

Uses existing ThetaData MCP server to fetch real market data
and populate the database.

This script is designed to be called by Claude Code, which has access
to MCP tools.
"""

import sys
sys.path.insert(0, '.')

from datetime import datetime, timedelta
from data_lake.market_data_manager import insert_bars, OHLCVBar
from skills.watchlist_manager import get_current_watchlist


def fetch_and_store_market_data_via_mcp():
    """
    Instructions for Claude Code to fetch real market data.

    Claude Code should:
    1. Get the watchlist
    2. For each symbol, call mcp__ThetaData__stock_snapshot_ohlc
    3. Process and store the data

    This function provides the structure and processing logic.
    """

    print("=" * 80)
    print("FETCHING REAL MARKET DATA VIA MCP")
    print("=" * 80)

    # Get watchlist
    watchlist = get_current_watchlist()
    print(f"\nWatchlist: {len(watchlist)} symbols")
    print(f"Symbols: {', '.join(watchlist)}\n")

    print("INSTRUCTIONS FOR CLAUDE CODE:")
    print("-" * 80)
    print("""
To fetch real market data, Claude Code should execute:

```python
# For each symbol in watchlist
for symbol in watchlist:
    # 1. Fetch OHLC snapshot from ThetaData MCP
    result = mcp__ThetaData__stock_snapshot_ohlc(symbol=symbol)

    # 2. Process and store the data
    if result and 'data' in result:
        # Create OHLCV bar from MCP result
        bar = OHLCVBar(
            symbol=symbol,
            timestamp=datetime.now().isoformat(),
            open=result['data'].get('open', 0),
            high=result['data'].get('high', 0),
            low=result['data'].get('low', 0),
            close=result['data'].get('close', 0),
            volume=result['data'].get('volume', 0),
            vwap=result['data'].get('vwap')
        )

        # Insert into database
        count = insert_bars(symbol, [bar])
        print(f"  ✓ {symbol}: Inserted {count} bar(s)")
    else:
        print(f"  ✗ {symbol}: Failed to fetch data")
```

Expected MCP call format:
    mcp__ThetaData__stock_snapshot_ohlc(symbol="AAPL")

MCP response structure (example):
    {
        "data": {
            "open": 180.50,
            "high": 181.20,
            "low": 179.80,
            "close": 180.95,
            "volume": 52000000,
            "vwap": 180.65
        },
        "timestamp": "2025-11-20T09:30:00"
    }
""")

    print("-" * 80)
    print("\nReturning watchlist for Claude Code to process...")

    return {
        "watchlist": watchlist,
        "instructions": "Use mcp__ThetaData__stock_snapshot_ohlc for each symbol",
        "processing_function": "See code above for data processing"
    }


if __name__ == "__main__":
    result = fetch_and_store_market_data_via_mcp()
    print(f"\n✓ Ready for Claude Code MCP execution")
    print(f"  Symbols to fetch: {len(result['watchlist'])}")
