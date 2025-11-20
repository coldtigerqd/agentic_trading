"""
Market Data Manager for Agentic AlphaHive Runtime

Provides storage and retrieval functions for historical OHLCV market data.
Supports 5-minute base granularity with on-the-fly aggregation to larger intervals.
"""

import sqlite3
import json
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from pathlib import Path


# Database path
DB_PATH = Path(__file__).parent / "trades.db"


@dataclass
class OHLCVBar:
    """Represents a single OHLCV bar"""
    symbol: str
    timestamp: str  # ISO format
    open: float
    high: float
    low: float
    close: float
    volume: int
    vwap: Optional[float] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "timestamp": self.timestamp,
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "close": self.close,
            "volume": self.volume,
            "vwap": self.vwap
        }


def get_db_connection() -> sqlite3.Connection:
    """Get database connection with optimizations enabled"""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")  # Write-Ahead Logging for concurrency
    conn.execute("PRAGMA synchronous=NORMAL")  # Faster writes
    conn.row_factory = sqlite3.Row  # Access columns by name
    return conn


def insert_bars(symbol: str, bars: List[OHLCVBar]) -> int:
    """
    Insert OHLCV bars into the database.
    Uses batch insert with UPSERT logic (INSERT OR REPLACE).

    Args:
        symbol: Stock symbol (e.g., "AAPL")
        bars: List of OHLCVBar objects

    Returns:
        Number of bars inserted/updated
    """
    if not bars:
        return 0

    conn = get_db_connection()
    cursor = conn.cursor()

    # Batch insert with UPSERT
    insert_sql = """
    INSERT OR REPLACE INTO market_data_bars
    (symbol, timestamp, open, high, low, close, volume, vwap)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """

    batch_data = [
        (bar.symbol, bar.timestamp, bar.open, bar.high, bar.low,
         bar.close, bar.volume, bar.vwap)
        for bar in bars
    ]

    cursor.executemany(insert_sql, batch_data)
    conn.commit()

    rows_affected = cursor.rowcount

    # Update data_freshness
    _update_freshness(conn, symbol)

    conn.close()
    return rows_affected


def get_bars(
    symbol: str,
    start: datetime,
    end: datetime,
    interval: str = "5min"
) -> List[OHLCVBar]:
    """
    Query historical bars for a symbol within a date range.
    Supports on-the-fly aggregation to larger intervals.

    Args:
        symbol: Stock symbol (e.g., "AAPL")
        start: Start datetime
        end: End datetime
        interval: Bar interval - "5min", "15min", "1h", or "daily"

    Returns:
        List of OHLCVBar objects
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # Query 5-minute bars
    query = """
    SELECT symbol, timestamp, open, high, low, close, volume, vwap
    FROM market_data_bars
    WHERE symbol = ? AND timestamp >= ? AND timestamp <= ?
    ORDER BY timestamp ASC
    """

    cursor.execute(query, (symbol, start.isoformat(), end.isoformat()))
    rows = cursor.fetchall()
    conn.close()

    # Convert to OHLCVBar objects
    bars_5min = [
        OHLCVBar(
            symbol=row["symbol"],
            timestamp=row["timestamp"],
            open=row["open"],
            high=row["high"],
            low=row["low"],
            close=row["close"],
            volume=row["volume"],
            vwap=row["vwap"]
        )
        for row in rows
    ]

    # Aggregate if needed
    if interval == "5min":
        return bars_5min
    else:
        return aggregate_bars(bars_5min, interval)


def aggregate_bars(bars_5min: List[OHLCVBar], target_interval: str) -> List[OHLCVBar]:
    """
    Aggregate 5-minute bars to larger intervals.

    Args:
        bars_5min: List of 5-minute bars
        target_interval: Target interval - "15min", "1h", or "daily"

    Returns:
        List of aggregated bars
    """
    if not bars_5min or target_interval == "5min":
        return bars_5min

    # Determine aggregation period (number of 5-min bars)
    period_map = {
        "15min": 3,    # 15min = 3 × 5min
        "1h": 12,      # 1h = 12 × 5min
        "daily": 78    # 6.5 hour trading day = 78 × 5min
    }

    if target_interval not in period_map:
        raise ValueError(f"Unsupported interval: {target_interval}")

    period = period_map[target_interval]
    aggregated = []

    for i in range(0, len(bars_5min), period):
        chunk = bars_5min[i:i + period]
        if not chunk:
            continue

        # Aggregate OHLCV
        agg_bar = OHLCVBar(
            symbol=chunk[0].symbol,
            timestamp=chunk[0].timestamp,  # Use first bar's timestamp
            open=chunk[0].open,            # First bar's open
            high=max(b.high for b in chunk),  # Max high
            low=min(b.low for b in chunk),    # Min low
            close=chunk[-1].close,         # Last bar's close
            volume=sum(b.volume for b in chunk),  # Sum volume
            vwap=_calculate_vwap(chunk)    # Recalculate VWAP
        )
        aggregated.append(agg_bar)

    return aggregated


def _calculate_vwap(bars: List[OHLCVBar]) -> Optional[float]:
    """Calculate volume-weighted average price for a list of bars"""
    if not bars:
        return None

    total_volume = sum(b.volume for b in bars)
    if total_volume == 0:
        return None

    # Use typical price (H+L+C)/3 weighted by volume
    vwap = sum(
        ((b.high + b.low + b.close) / 3) * b.volume
        for b in bars
    ) / total_volume

    return round(vwap, 2)


def detect_gaps(symbol: str) -> List[Dict[str, str]]:
    """
    Detect gaps in market data for a symbol.

    Args:
        symbol: Stock symbol

    Returns:
        List of gap dictionaries with 'start', 'end', 'missing_bars'
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # Get all timestamps for symbol
    cursor.execute("""
        SELECT timestamp
        FROM market_data_bars
        WHERE symbol = ?
        ORDER BY timestamp ASC
    """, (symbol,))

    timestamps = [row["timestamp"] for row in cursor.fetchall()]
    conn.close()

    if len(timestamps) < 2:
        return []

    gaps = []
    for i in range(len(timestamps) - 1):
        current = datetime.fromisoformat(timestamps[i])
        next_ts = datetime.fromisoformat(timestamps[i + 1])

        # Expected: 5 minutes apart during trading hours
        # Simplified: flag if gap > 10 minutes (allows for market close)
        delta = (next_ts - current).total_seconds() / 60
        if delta > 10:
            # Potential gap detected
            gaps.append({
                "start": timestamps[i],
                "end": timestamps[i + 1],
                "missing_bars": int((delta - 5) / 5)  # Approximate
            })

    return gaps


def cleanup_old_data(cutoff_date: datetime) -> int:
    """
    Delete market data older than cutoff_date (3-year retention policy).

    Args:
        cutoff_date: Delete data before this date

    Returns:
        Number of rows deleted
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    delete_sql = """
    DELETE FROM market_data_bars
    WHERE timestamp < ?
    """

    cursor.execute(delete_sql, (cutoff_date.isoformat(),))
    conn.commit()

    rows_deleted = cursor.rowcount

    # Update freshness for affected symbols
    cursor.execute("SELECT DISTINCT symbol FROM watchlist WHERE active = 1")
    symbols = [row["symbol"] for row in cursor.fetchall()]

    for symbol in symbols:
        _update_freshness(conn, symbol)

    conn.close()
    return rows_deleted


def _update_freshness(conn: sqlite3.Connection, symbol: str):
    """Update data_freshness table for a symbol"""
    cursor = conn.cursor()

    # Get oldest and newest bar timestamps
    cursor.execute("""
        SELECT
            MIN(timestamp) as oldest,
            MAX(timestamp) as newest,
            COUNT(*) as count
        FROM market_data_bars
        WHERE symbol = ?
    """, (symbol,))

    row = cursor.fetchone()
    if not row or not row["oldest"]:
        # No data for this symbol
        return

    oldest_bar = row["oldest"]
    newest_bar = row["newest"]
    bar_count = row["count"]

    # Detect gaps
    gaps = detect_gaps(symbol)
    gaps_json = json.dumps({"gaps": gaps}) if gaps else None

    # Upsert freshness record
    cursor.execute("""
        INSERT OR REPLACE INTO data_freshness
        (symbol, oldest_bar, newest_bar, bar_count, last_checked, gaps_detected)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (symbol, oldest_bar, newest_bar, bar_count,
          datetime.now().isoformat(), gaps_json))

    conn.commit()


def get_freshness_info(symbol: str) -> Optional[Dict]:
    """Get data freshness information for a symbol"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM data_freshness WHERE symbol = ?
    """, (symbol,))

    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    return {
        "symbol": row["symbol"],
        "oldest_bar": row["oldest_bar"],
        "newest_bar": row["newest_bar"],
        "bar_count": row["bar_count"],
        "last_checked": row["last_checked"],
        "gaps_detected": json.loads(row["gaps_detected"]) if row["gaps_detected"] else {"gaps": []}
    }


def get_latest_bar(symbol: str) -> Optional[OHLCVBar]:
    """Get the most recent bar for a symbol"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT symbol, timestamp, open, high, low, close, volume, vwap
        FROM market_data_bars
        WHERE symbol = ?
        ORDER BY timestamp DESC
        LIMIT 1
    """, (symbol,))

    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    return OHLCVBar(
        symbol=row["symbol"],
        timestamp=row["timestamp"],
        open=row["open"],
        high=row["high"],
        low=row["low"],
        close=row["close"],
        volume=row["volume"],
        vwap=row["vwap"]
    )
