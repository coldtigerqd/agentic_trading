#!/usr/bin/env python3
"""
Market Data Population Script

Fetches historical market data and populates the market_data_cache.db database.

Usage:
    python scripts/populate_market_data.py --symbols AAPL,NVDA,SPY --days 30
    python scripts/populate_market_data.py --watchlist --days 60
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from typing import List
import time

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from data_lake.market_data_manager import insert_bars, OHLCVBar
from runtime.data_fetcher import get_active_watchlist, add_to_watchlist
from skills.watchlist_manager import get_current_watchlist


def generate_sample_data(symbol: str, days: int = 30) -> List[OHLCVBar]:
    """
    Generate sample OHLCV data for testing.

    In production, this would be replaced with actual ThetaData MCP calls.
    For now, generates realistic-looking random walk data.
    """
    import random

    bars = []
    base_price = {
        "AAPL": 180.0,
        "NVDA": 145.0,
        "SPY": 451.0,
        "QQQ": 395.0,
        "TSLA": 245.0,
        "AMD": 125.0,
        "MSFT": 380.0,
        "GOOGL": 140.0,
        "META": 485.0,
        "AMZN": 175.0,
    }.get(symbol, 100.0)

    current_price = base_price
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)

    # Generate daily bars
    current_date = start_date
    while current_date <= end_date:
        # Skip weekends
        if current_date.weekday() >= 5:
            current_date += timedelta(days=1)
            continue

        # Random walk for the day
        daily_change = random.uniform(-0.03, 0.03)  # ±3% daily
        open_price = current_price

        high_price = open_price * (1 + abs(daily_change) * random.uniform(0.5, 1.5))
        low_price = open_price * (1 - abs(daily_change) * random.uniform(0.5, 1.5))
        close_price = open_price * (1 + daily_change)

        volume = int(random.uniform(50_000_000, 150_000_000))
        vwap = (high_price + low_price + close_price) / 3

        # Generate 5-minute bars for the trading day (9:30 AM - 4:00 PM ET)
        # That's 6.5 hours = 390 minutes = 78 bars
        trading_start = current_date.replace(hour=9, minute=30, second=0, microsecond=0)

        for bar_num in range(78):
            bar_time = trading_start + timedelta(minutes=bar_num * 5)

            # Interpolate prices throughout the day
            progress = bar_num / 78
            bar_close = open_price + (close_price - open_price) * progress
            bar_close += random.uniform(-0.01, 0.01) * bar_close  # Add noise

            bar_open = bar_close + random.uniform(-0.005, 0.005) * bar_close
            bar_high = max(bar_open, bar_close) * random.uniform(1.0, 1.01)
            bar_low = min(bar_open, bar_close) * random.uniform(0.99, 1.0)
            bar_volume = int(volume / 78 * random.uniform(0.5, 1.5))
            bar_vwap = (bar_high + bar_low + bar_close) / 3

            bar = OHLCVBar(
                symbol=symbol,
                timestamp=bar_time.isoformat(),
                open=round(bar_open, 2),
                high=round(bar_high, 2),
                low=round(bar_low, 2),
                close=round(bar_close, 2),
                volume=bar_volume,
                vwap=round(bar_vwap, 2)
            )

            bars.append(bar)

        current_price = close_price
        current_date += timedelta(days=1)

    return bars


def populate_symbol(symbol: str, days: int = 30, verbose: bool = True) -> dict:
    """
    Populate market data for a single symbol.

    Args:
        symbol: Stock symbol
        days: Number of days of history to generate
        verbose: Print progress

    Returns:
        Dict with status and bar count
    """
    if verbose:
        print(f"Populating {symbol} with {days} days of data...")

    start_time = time.time()

    # Generate sample data
    # TODO: Replace with actual ThetaData MCP calls
    bars = generate_sample_data(symbol, days)

    # Insert into database
    inserted_count = insert_bars(symbol, bars)

    elapsed = time.time() - start_time

    if verbose:
        print(f"  ✓ Inserted {inserted_count} bars for {symbol} in {elapsed:.2f}s")

    return {
        "success": True,
        "symbol": symbol,
        "bars_inserted": inserted_count,
        "elapsed_seconds": elapsed
    }


def main():
    parser = argparse.ArgumentParser(description="Populate market data cache")
    parser.add_argument(
        "--symbols",
        type=str,
        help="Comma-separated list of symbols (e.g., AAPL,NVDA,SPY)"
    )
    parser.add_argument(
        "--watchlist",
        action="store_true",
        help="Populate all symbols in the current watchlist"
    )
    parser.add_argument(
        "--days",
        type=int,
        default=30,
        help="Number of days of historical data to generate (default: 30)"
    )
    parser.add_argument(
        "--add-default",
        action="store_true",
        help="Add default watchlist symbols if none exist"
    )

    args = parser.parse_args()

    # Determine which symbols to populate
    symbols = []

    if args.add_default:
        # Add default watchlist symbols
        default_symbols = [
            ("SPY", 10, "S&P 500 ETF"),
            ("QQQ", 9, "Nasdaq 100 ETF"),
            ("AAPL", 8, "Apple Inc."),
            ("NVDA", 8, "NVIDIA Corp."),
            ("TSLA", 7, "Tesla Inc."),
            ("AMD", 7, "Advanced Micro Devices"),
            ("MSFT", 8, "Microsoft Corp."),
            ("DIA", 6, "Dow Jones ETF"),
            ("IWM", 6, "Russell 2000 ETF"),
            ("XLE", 5, "Energy Sector ETF"),
        ]

        print("Adding default watchlist symbols...")
        for symbol, priority, notes in default_symbols:
            result = add_to_watchlist(symbol, priority=priority, notes=notes)
            if result["success"]:
                print(f"  ✓ Added {symbol} (priority {priority})")
                symbols.append(symbol)

    if args.symbols:
        # User-specified symbols
        symbols.extend([s.strip().upper() for s in args.symbols.split(",")])

    if args.watchlist:
        # Get symbols from current watchlist
        watchlist_symbols = get_current_watchlist()
        symbols.extend(watchlist_symbols)

    if not symbols:
        print("Error: No symbols specified.")
        print("Use --symbols, --watchlist, or --add-default")
        return 1

    # Remove duplicates
    symbols = list(set(symbols))

    print(f"\n{'='*60}")
    print(f"Populating Market Data Cache")
    print(f"{'='*60}")
    print(f"Symbols: {', '.join(symbols)}")
    print(f"History: {args.days} days")
    print(f"Expected bars per symbol: ~{args.days * 78} (5-min intervals)")
    print(f"{'='*60}\n")

    # Populate each symbol
    results = []
    total_start = time.time()

    for symbol in symbols:
        try:
            result = populate_symbol(symbol, args.days, verbose=True)
            results.append(result)
        except Exception as e:
            print(f"  ✗ Error populating {symbol}: {e}")
            results.append({
                "success": False,
                "symbol": symbol,
                "error": str(e)
            })

    total_elapsed = time.time() - total_start

    # Summary
    print(f"\n{'='*60}")
    print("Population Complete")
    print(f"{'='*60}")

    successful = [r for r in results if r.get("success")]
    failed = [r for r in results if not r.get("success")]
    total_bars = sum(r.get("bars_inserted", 0) for r in successful)

    print(f"Symbols processed: {len(symbols)}")
    print(f"Successful: {len(successful)}")
    print(f"Failed: {len(failed)}")
    print(f"Total bars inserted: {total_bars:,}")
    print(f"Total time: {total_elapsed:.2f}s")
    print(f"Average: {total_elapsed/len(symbols):.2f}s per symbol")

    if failed:
        print(f"\nFailed symbols:")
        for result in failed:
            print(f"  ✗ {result['symbol']}: {result.get('error', 'Unknown error')}")

    print(f"\n{'='*60}")
    print("✓ Database ready for trading analysis!")
    print(f"{'='*60}\n")

    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
