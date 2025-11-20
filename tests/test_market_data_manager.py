"""
Unit tests for market_data_manager.py
"""

import pytest
from datetime import datetime, timedelta
from data_lake.market_data_manager import (
    OHLCVBar,
    insert_bars,
    get_bars,
    aggregate_bars,
    detect_gaps,
    get_latest_bar,
    get_freshness_info
)


def test_insert_and_query_bars():
    """Test inserting and querying 5-minute bars"""
    # Create test bars
    symbol = "TEST"
    start_time = datetime(2025, 11, 20, 9, 30)

    test_bars = [
        OHLCVBar(
            symbol=symbol,
            timestamp=(start_time + timedelta(minutes=5*i)).isoformat(),
            open=100.0 + i,
            high=101.0 + i,
            low=99.0 + i,
            close=100.5 + i,
            volume=1000000 + i*10000,
            vwap=100.3 + i
        )
        for i in range(10)
    ]

    # Insert bars
    count = insert_bars(symbol, test_bars)
    assert count == 10

    # Query bars
    end_time = start_time + timedelta(minutes=50)
    queried_bars = get_bars(symbol, start_time, end_time, interval="5min")

    assert len(queried_bars) == 10
    assert queried_bars[0].symbol == symbol
    assert queried_bars[0].open == 100.0
    assert queried_bars[9].close == 109.5


def test_aggregate_bars_to_1h():
    """Test aggregating 5-min bars to 1-hour bars"""
    symbol = "AAPL"
    start_time = datetime(2025, 11, 20, 9, 30)

    # Create 12 bars (1 hour)
    bars_5min = [
        OHLCVBar(
            symbol=symbol,
            timestamp=(start_time + timedelta(minutes=5*i)).isoformat(),
            open=150.0,
            high=151.0 + i*0.1,
            low=149.0,
            close=150.5,
            volume=100000,
            vwap=150.3
        )
        for i in range(12)
    ]

    # Aggregate to 1h
    bars_1h = aggregate_bars(bars_5min, "1h")

    assert len(bars_1h) == 1
    assert bars_1h[0].open == 150.0
    assert bars_1h[0].high == 152.1  # max of all highs
    assert bars_1h[0].low == 149.0
    assert bars_1h[0].close == 150.5
    assert bars_1h[0].volume == 1200000  # sum of all volumes


def test_get_latest_bar():
    """Test getting the most recent bar"""
    symbol = "SPY"
    now = datetime.now()

    bars = [
        OHLCVBar(
            symbol=symbol,
            timestamp=(now - timedelta(minutes=10)).isoformat(),
            open=450.0,
            high=451.0,
            low=449.0,
            close=450.5,
            volume=1000000,
            vwap=450.3
        ),
        OHLCVBar(
            symbol=symbol,
            timestamp=(now - timedelta(minutes=5)).isoformat(),
            open=450.5,
            high=452.0,
            low=450.0,
            close=451.5,
            volume=1100000,
            vwap=451.2
        )
    ]

    insert_bars(symbol, bars)
    latest = get_latest_bar(symbol)

    assert latest is not None
    assert latest.close == 451.5
    assert latest.volume == 1100000


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
