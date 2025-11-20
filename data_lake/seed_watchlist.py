"""
Seed initial watchlist with liquid ETFs and popular stocks.
"""

import sqlite3
from datetime import datetime
from pathlib import Path


DB_PATH = Path(__file__).parent / "trades.db"


# Initial watchlist: Top liquid ETFs and high-volume stocks
INITIAL_SYMBOLS = [
    # Major Index ETFs (highest priority)
    {"symbol": "SPY", "priority": 10, "notes": "S&P 500 ETF - Market benchmark"},
    {"symbol": "QQQ", "priority": 10, "notes": "Nasdaq 100 ETF - Tech heavy"},
    {"symbol": "IWM", "priority": 9, "notes": "Russell 2000 ETF - Small caps"},
    {"symbol": "DIA", "priority": 9, "notes": "Dow Jones Industrial Average ETF"},

    # Sector ETFs
    {"symbol": "XLF", "priority": 8, "notes": "Financial Select Sector SPDR"},
    {"symbol": "XLE", "priority": 8, "notes": "Energy Select Sector SPDR"},
    {"symbol": "XLK", "priority": 8, "notes": "Technology Select Sector SPDR"},

    # High Volume Stocks (for options trading)
    {"symbol": "AAPL", "priority": 7, "notes": "Apple Inc - High liquidity"},
    {"symbol": "NVDA", "priority": 7, "notes": "NVIDIA - High volatility"},
    {"symbol": "TSLA", "priority": 7, "notes": "Tesla - High IV options"},
]


def seed_initial_watchlist() -> int:
    """
    Seed the watchlist with initial symbols.

    Returns:
        Number of symbols added
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Check if watchlist already has data
    cursor.execute("SELECT COUNT(*) as count FROM watchlist")
    existing_count = cursor.fetchone()["count"]

    if existing_count > 0:
        conn.close()
        return 0  # Already seeded

    # Insert initial symbols
    now = datetime.now().isoformat()
    added = 0

    for entry in INITIAL_SYMBOLS:
        cursor.execute("""
            INSERT INTO watchlist (symbol, added_at, active, priority, notes)
            VALUES (?, ?, 1, ?, ?)
        """, (entry["symbol"], now, entry["priority"], entry["notes"]))
        added += 1

    conn.commit()
    conn.close()

    return added


if __name__ == "__main__":
    # Run seeding
    count = seed_initial_watchlist()
    if count > 0:
        print(f"✓ Seeded {count} symbols to watchlist")
    else:
        print("ℹ Watchlist already seeded")
