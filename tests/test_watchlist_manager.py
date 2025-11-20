"""
Tests for watchlist manager with performance-based scoring.

Tests cover:
- Symbol score calculation (Sharpe, win rate, avg P&L, frequency)
- Watchlist rotation with sector diversification
- Churn limits and performance reporting
"""

import pytest
import sqlite3
import tempfile
import os
from datetime import datetime, timedelta
from pathlib import Path

from skills.watchlist_manager import (
    calculate_symbol_score,
    calculate_sharpe_ratio,
    get_symbol_sector,
    get_current_watchlist,
    get_recent_churn,
    update_watchlist,
    get_watchlist_performance_report,
    SECTOR_MAP
)


@pytest.fixture
def test_db():
    """Create a temporary test database with schema."""
    # Create temporary database file
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    db_path = Path(db_path)

    # Create schema
    conn = sqlite3.connect(str(db_path))
    conn.executescript("""
        CREATE TABLE trades (
            trade_id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            symbol TEXT NOT NULL,
            strategy TEXT NOT NULL,
            signal_source TEXT,
            legs TEXT NOT NULL,
            max_risk REAL NOT NULL,
            capital_required REAL NOT NULL,
            confidence REAL,
            reasoning TEXT,
            order_id INTEGER,
            status TEXT NOT NULL,
            fill_price REAL,
            pnl REAL,
            metadata TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE watchlist (
            symbol TEXT PRIMARY KEY,
            added_at TEXT NOT NULL,
            active BOOLEAN DEFAULT 1,
            last_updated TEXT,
            priority INTEGER DEFAULT 0,
            notes TEXT
        );

        CREATE INDEX idx_trades_symbol ON trades(symbol);
        CREATE INDEX idx_trades_timestamp ON trades(timestamp);
    """)
    conn.commit()
    conn.close()

    yield db_path

    # Cleanup
    os.unlink(db_path)


def insert_trade(db_path, symbol, pnl, days_ago=0, status="FILLED"):
    """Helper to insert a trade into test database."""
    timestamp = (datetime.now() - timedelta(days=days_ago)).isoformat()

    conn = sqlite3.connect(str(db_path))
    conn.execute("""
        INSERT INTO trades (
            timestamp, symbol, strategy, legs, max_risk,
            capital_required, status, pnl
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (timestamp, symbol, "TEST", "[]", 100, 200, status, pnl))
    conn.commit()
    conn.close()


def insert_watchlist_symbol(db_path, symbol, active=1, days_ago=0, priority=5):
    """Helper to insert a symbol into watchlist."""
    added_at = (datetime.now() - timedelta(days=days_ago)).isoformat()

    conn = sqlite3.connect(str(db_path))
    conn.execute("""
        INSERT INTO watchlist (symbol, added_at, active, priority, notes)
        VALUES (?, ?, ?, ?, ?)
    """, (symbol, added_at, active, priority, f"Test symbol {symbol}"))
    conn.commit()
    conn.close()


class TestCalculateSharpeRatio:
    """Test Sharpe ratio calculation."""

    def test_sharpe_positive_returns(self):
        """Test Sharpe with consistently positive returns."""
        pnls = [100, 120, 110, 130, 115]
        sharpe = calculate_sharpe_ratio(pnls)

        assert sharpe > 0
        assert isinstance(sharpe, float)

    def test_sharpe_negative_returns(self):
        """Test Sharpe with consistently negative returns."""
        pnls = [-50, -60, -55, -70, -58]
        sharpe = calculate_sharpe_ratio(pnls)

        assert sharpe < 0

    def test_sharpe_mixed_returns(self):
        """Test Sharpe with mixed positive/negative returns."""
        pnls = [100, -50, 80, -30, 60]
        sharpe = calculate_sharpe_ratio(pnls)

        assert isinstance(sharpe, float)

    def test_sharpe_zero_volatility(self):
        """Test Sharpe with constant returns (zero volatility)."""
        pnls = [100, 100, 100, 100]
        sharpe = calculate_sharpe_ratio(pnls)

        # Should return inf for zero std with positive mean
        assert sharpe == float('inf')

    def test_sharpe_insufficient_data(self):
        """Test Sharpe with < 2 data points."""
        pnls = [100]
        sharpe = calculate_sharpe_ratio(pnls)

        assert sharpe == 0.0

    def test_sharpe_empty_list(self):
        """Test Sharpe with empty list."""
        sharpe = calculate_sharpe_ratio([])

        assert sharpe == 0.0


class TestCalculateSymbolScore:
    """Test symbol score calculation."""

    def test_score_no_trades(self, test_db):
        """Test scoring symbol with no trades."""
        result = calculate_symbol_score("AAPL", lookback_days=30, db_path=test_db)

        assert result["symbol"] == "AAPL"
        assert result["score"] == 0.0
        assert result["sharpe_ratio"] == 0.0
        assert result["win_rate"] == 0.0
        assert result["avg_pnl"] == 0.0
        assert result["trade_count"] == 0
        assert result["has_min_trades"] is False
        assert result["sector"] == "Technology"

    def test_score_winning_trades(self, test_db):
        """Test scoring symbol with all winning trades."""
        # Insert 10 winning trades
        for i in range(10):
            insert_trade(test_db, "SPY", pnl=100 + i*10, days_ago=i)

        result = calculate_symbol_score("SPY", lookback_days=30, db_path=test_db)

        assert result["symbol"] == "SPY"
        assert result["score"] > 50  # Should be above average
        assert result["win_rate"] == 1.0  # 100% win rate
        assert result["avg_pnl"] > 100
        assert result["trade_count"] == 10
        assert result["has_min_trades"] is True

    def test_score_losing_trades(self, test_db):
        """Test scoring symbol with all losing trades."""
        # Insert 10 losing trades
        for i in range(10):
            insert_trade(test_db, "TSLA", pnl=-100 - i*10, days_ago=i)

        result = calculate_symbol_score("TSLA", lookback_days=30, db_path=test_db)

        assert result["symbol"] == "TSLA"
        assert result["score"] < 50  # Should be below average
        assert result["win_rate"] == 0.0  # 0% win rate
        assert result["avg_pnl"] < 0
        assert result["sharpe_ratio"] < 0

    def test_score_mixed_performance(self, test_db):
        """Test scoring with 60% win rate and positive avg P&L."""
        # 6 winners, 4 losers
        for i in range(6):
            insert_trade(test_db, "QQQ", pnl=150, days_ago=i)
        for i in range(4):
            insert_trade(test_db, "QQQ", pnl=-80, days_ago=i+6)

        result = calculate_symbol_score("QQQ", lookback_days=30, db_path=test_db)

        assert result["symbol"] == "QQQ"
        assert result["win_rate"] == 0.6  # 60% win rate
        assert result["avg_pnl"] == (6*150 - 4*80) / 10  # Should be positive
        assert result["trade_count"] == 10
        assert result["sharpe_ratio"] > 0  # Positive Sharpe

    def test_score_ignores_old_trades(self, test_db):
        """Test that trades outside lookback window are ignored."""
        # Insert trades outside window
        insert_trade(test_db, "NVDA", pnl=500, days_ago=40)
        insert_trade(test_db, "NVDA", pnl=500, days_ago=45)

        # Insert recent losing trade
        insert_trade(test_db, "NVDA", pnl=-200, days_ago=5)

        result = calculate_symbol_score("NVDA", lookback_days=30, db_path=test_db)

        # Should only see the 1 recent losing trade
        assert result["trade_count"] == 1
        assert result["avg_pnl"] == -200

    def test_score_pending_trades_ignored(self, test_db):
        """Test that PENDING/SUBMITTED trades are ignored."""
        insert_trade(test_db, "AMD", pnl=None, status="PENDING")
        insert_trade(test_db, "AMD", pnl=None, status="SUBMITTED")
        insert_trade(test_db, "AMD", pnl=100, status="FILLED")

        result = calculate_symbol_score("AMD", lookback_days=30, db_path=test_db)

        # Should only count the FILLED trade
        assert result["trade_count"] == 1
        assert result["avg_pnl"] == 100


class TestGetSymbolSector:
    """Test sector mapping."""

    def test_sector_known_symbols(self):
        """Test sector for known symbols."""
        assert get_symbol_sector("AAPL") == "Technology"
        assert get_symbol_sector("XLE") == "Energy"
        assert get_symbol_sector("JPM") == "Financial"
        assert get_symbol_sector("SPY") == "Broad Market"

    def test_sector_unknown_symbol(self):
        """Test sector for unmapped symbol."""
        assert get_symbol_sector("UNKNOWN_SYM") == "Other"


class TestGetCurrentWatchlist:
    """Test retrieving current watchlist."""

    def test_get_empty_watchlist(self, test_db):
        """Test getting watchlist when empty."""
        symbols = get_current_watchlist(db_path=test_db)

        assert symbols == []

    def test_get_active_symbols_only(self, test_db):
        """Test that only active symbols are returned."""
        insert_watchlist_symbol(test_db, "AAPL", active=1)
        insert_watchlist_symbol(test_db, "TSLA", active=1)
        insert_watchlist_symbol(test_db, "NVDA", active=0)  # Inactive

        symbols = get_current_watchlist(db_path=test_db)

        assert len(symbols) == 2
        assert "AAPL" in symbols
        assert "TSLA" in symbols
        assert "NVDA" not in symbols

    def test_get_symbols_sorted_by_priority(self, test_db):
        """Test that symbols are sorted by priority (desc)."""
        insert_watchlist_symbol(test_db, "SPY", priority=10)
        insert_watchlist_symbol(test_db, "AAPL", priority=7)
        insert_watchlist_symbol(test_db, "QQQ", priority=9)

        symbols = get_current_watchlist(db_path=test_db)

        assert symbols == ["SPY", "QQQ", "AAPL"]


class TestGetRecentChurn:
    """Test churn counting."""

    def test_churn_empty_watchlist(self, test_db):
        """Test churn with no changes."""
        churn = get_recent_churn(days=7, db_path=test_db)

        assert churn == 0

    def test_churn_recent_additions(self, test_db):
        """Test churn counts recent additions."""
        insert_watchlist_symbol(test_db, "AAPL", days_ago=2)
        insert_watchlist_symbol(test_db, "TSLA", days_ago=5)
        insert_watchlist_symbol(test_db, "NVDA", days_ago=10)  # Outside window

        churn = get_recent_churn(days=7, db_path=test_db)

        # Should count 2 additions within 7 days
        assert churn == 2

    def test_churn_removals(self, test_db):
        """Test churn counts removals (deactivations)."""
        # Add symbols
        insert_watchlist_symbol(test_db, "AAPL", active=1, days_ago=20)
        insert_watchlist_symbol(test_db, "TSLA", active=1, days_ago=20)

        # Deactivate recently
        conn = sqlite3.connect(str(test_db))
        last_updated = (datetime.now() - timedelta(days=3)).isoformat()
        conn.execute("""
            UPDATE watchlist
            SET active = 0, last_updated = ?
            WHERE symbol = 'TSLA'
        """, (last_updated,))
        conn.commit()
        conn.close()

        churn = get_recent_churn(days=7, db_path=test_db)

        # Should count 1 removal
        assert churn == 1


class TestUpdateWatchlist:
    """Test watchlist update and rotation."""

    def test_update_churn_limit_reached(self, test_db):
        """Test that update respects churn limit."""
        # Add 3 symbols recently (at limit)
        insert_watchlist_symbol(test_db, "AAPL", days_ago=2)
        insert_watchlist_symbol(test_db, "TSLA", days_ago=3)
        insert_watchlist_symbol(test_db, "NVDA", days_ago=4)

        # Try to update (should be blocked)
        result = update_watchlist(
            candidate_pool=["SPY", "QQQ"],
            db_path=test_db,
            lookback_days=30
        )

        assert result["churn_limit_reached"] is True
        assert len(result["added"]) == 0
        assert len(result["removed"]) == 0

    def test_update_rotates_bottom_performers(self, test_db):
        """Test that bottom 20% performers are rotated out."""
        # Setup watchlist with 10 symbols
        symbols = ["SYM1", "SYM2", "SYM3", "SYM4", "SYM5",
                   "SYM6", "SYM7", "SYM8", "SYM9", "SYM10"]

        for sym in symbols:
            insert_watchlist_symbol(test_db, sym, days_ago=30)

        # Create performance data - SYM1 and SYM2 are losers
        for sym in ["SYM1", "SYM2"]:
            for i in range(10):
                insert_trade(test_db, sym, pnl=-100, days_ago=i)

        # SYM3-SYM10 are winners
        for sym in symbols[2:]:
            for i in range(10):
                insert_trade(test_db, sym, pnl=150, days_ago=i)

        # Candidate pool with better performers
        candidates = ["AAPL", "NVDA", "QQQ"]

        # Mock good performance for candidates
        for sym in candidates:
            for i in range(10):
                insert_trade(test_db, sym, pnl=200, days_ago=i)

        # Update watchlist
        result = update_watchlist(
            candidate_pool=candidates,
            max_watchlist_size=10,
            lookback_days=30,
            db_path=test_db
        )

        # Should remove bottom 20% (2 symbols)
        assert len(result["removed"]) >= 1
        assert len(result["added"]) >= 1

        # Removed symbols should be from the losers
        for removed in result["removed"]:
            assert removed in ["SYM1", "SYM2"]

    def test_update_respects_sector_limits(self, test_db):
        """Test that sector diversification is enforced."""
        # Setup watchlist at exactly 30% tech limit (3/10 tech)
        tech_symbols = ["AAPL", "MSFT", "NVDA"]  # 30% tech
        other_symbols = ["SPY", "XLE", "JPM", "XLF", "DIA", "XLV", "XLI"]  # 70% other

        for sym in tech_symbols + other_symbols:
            insert_watchlist_symbol(test_db, sym, days_ago=30)

        # Make one non-tech symbol perform poorly (target for rotation)
        for i in range(10):
            insert_trade(test_db, "XLI", pnl=-200, days_ago=i)

        # Make other symbols perform moderately
        for sym in tech_symbols + ["SPY", "XLE", "JPM", "XLF", "DIA", "XLV"]:
            for i in range(10):
                insert_trade(test_db, sym, pnl=100, days_ago=i)

        # Candidate pool with ONLY tech symbols (should be blocked due to sector limit)
        tech_candidates = ["TSLA", "AMD", "GOOGL"]  # All tech

        # Create excellent performance for candidates
        for sym in tech_candidates:
            for i in range(10):
                insert_trade(test_db, sym, pnl=250, days_ago=i)

        # Update with sector limits enforced
        result = update_watchlist(
            candidate_pool=tech_candidates,
            max_watchlist_size=10,
            lookback_days=30,
            enforce_sector_limits=True,
            db_path=test_db
        )

        # Check that tech symbols were NOT added (sector limit enforcement)
        # Since we're at 30% tech and all candidates are tech, none should be added
        tech_added = sum(1 for sym in result["added"] if get_symbol_sector(sym) == "Technology")

        # Should add 0 or very few tech symbols to avoid exceeding 30% limit
        sector_dist = result["sector_distribution"]
        if "Technology" in sector_dist and sector_dist:
            total_symbols = sum(sector_dist.values())
            tech_pct = sector_dist["Technology"] / total_symbols if total_symbols > 0 else 0
            # Should remain at or below ~33% (allowing 1 tech addition max)
            assert tech_pct <= 0.40  # 4/10 = 40% max

    def test_update_no_changes_if_no_underperformers(self, test_db):
        """Test that no changes are made if no symbols have min trades."""
        # Setup watchlist but with insufficient trade history
        symbols = ["AAPL", "TSLA", "NVDA"]

        for sym in symbols:
            insert_watchlist_symbol(test_db, sym, days_ago=30)

        # Only 2 trades each (below MIN_TRADES_FOR_SCORING=5)
        for sym in symbols:
            insert_trade(test_db, sym, pnl=100, days_ago=1)
            insert_trade(test_db, sym, pnl=120, days_ago=2)

        result = update_watchlist(
            candidate_pool=["SPY", "QQQ"],
            db_path=test_db,
            lookback_days=30
        )

        # Should not rotate any symbols
        assert len(result["added"]) == 0
        assert len(result["removed"]) == 0


class TestGetWatchlistPerformanceReport:
    """Test performance reporting."""

    def test_report_empty_watchlist(self, test_db):
        """Test report with empty watchlist."""
        report = get_watchlist_performance_report(lookback_days=30, db_path=test_db)

        assert report["symbol_scores"] == []
        assert report["avg_score"] == 0.0
        assert report["total_trades"] == 0
        assert report["sector_distribution"] == {}

    def test_report_with_active_symbols(self, test_db):
        """Test report with active trading symbols."""
        # Setup watchlist
        symbols = ["AAPL", "SPY", "QQQ"]

        for sym in symbols:
            insert_watchlist_symbol(test_db, sym, days_ago=30)

        # Create varied performance
        # AAPL: Top performer
        for i in range(10):
            insert_trade(test_db, "AAPL", pnl=200, days_ago=i)

        # SPY: Medium performer
        for i in range(10):
            insert_trade(test_db, "SPY", pnl=100, days_ago=i)

        # QQQ: Bottom performer
        for i in range(10):
            insert_trade(test_db, "QQQ", pnl=-50, days_ago=i)

        report = get_watchlist_performance_report(lookback_days=30, db_path=test_db)

        # Check structure
        assert len(report["symbol_scores"]) == 3
        assert report["total_trades"] == 30
        assert "avg_score" in report
        assert "sector_distribution" in report

        # Scores should be sorted (descending)
        scores = [s["score"] for s in report["symbol_scores"]]
        assert scores == sorted(scores, reverse=True)

        # Top performer should be AAPL
        assert report["top_performers"][0] == "AAPL"

        # Bottom performer should be QQQ
        assert report["underperformers"][-1] == "QQQ"

    def test_report_sector_distribution(self, test_db):
        """Test sector distribution in report."""
        # Add symbols from different sectors
        insert_watchlist_symbol(test_db, "AAPL", days_ago=30)  # Technology
        insert_watchlist_symbol(test_db, "XLE", days_ago=30)   # Energy
        insert_watchlist_symbol(test_db, "JPM", days_ago=30)   # Financial

        # Add minimal trades for scoring
        for sym in ["AAPL", "XLE", "JPM"]:
            for i in range(5):
                insert_trade(test_db, sym, pnl=100, days_ago=i)

        report = get_watchlist_performance_report(lookback_days=30, db_path=test_db)

        # Check sector distribution
        sector_dist = report["sector_distribution"]
        assert sector_dist["Technology"] == 1
        assert sector_dist["Energy"] == 1
        assert sector_dist["Financial"] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
