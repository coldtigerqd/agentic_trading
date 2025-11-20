"""
Automated watchlist management with performance-based scoring and rotation.

Manages symbol watchlist by tracking trading performance and rotating
underperformers. Uses composite scoring with Sharpe ratio, win rate,
average P&L, and trade frequency.
"""

import sqlite3
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import warnings

# Database path
DB_PATH = Path(__file__).parent.parent / "data_lake" / "trades.db"

# Sector mapping for diversification enforcement
SECTOR_MAP = {
    # Broad Market ETFs
    "SPY": "Broad Market", "QQQ": "Technology", "IWM": "Broad Market",
    "DIA": "Broad Market", "VTI": "Broad Market",

    # Sector ETFs
    "XLF": "Financial", "XLE": "Energy", "XLK": "Technology",
    "XLV": "Healthcare", "XLI": "Industrial", "XLP": "Consumer Staples",
    "XLY": "Consumer Discretionary", "XLU": "Utilities", "XLRE": "Real Estate",
    "XLB": "Materials", "XLC": "Communication",

    # Tech Stocks
    "AAPL": "Technology", "MSFT": "Technology", "GOOGL": "Technology",
    "META": "Technology", "NVDA": "Technology", "AMD": "Technology",
    "TSLA": "Consumer Discretionary", "NFLX": "Communication",
    "AMZN": "Consumer Discretionary", "SHOP": "Technology",

    # Semiconductor
    "TSM": "Technology", "INTC": "Technology", "QCOM": "Technology",
    "AVGO": "Technology", "MU": "Technology",

    # Other
    "JPM": "Financial", "BAC": "Financial", "GS": "Financial",
    "XOM": "Energy", "CVX": "Energy",
}

# Default sector for unmapped symbols
DEFAULT_SECTOR = "Other"

# Configuration constants
SHARPE_WEIGHT = 0.40
WIN_RATE_WEIGHT = 0.30
AVG_PNL_WEIGHT = 0.20
FREQ_WEIGHT = 0.10

MAX_SECTOR_PCT = 0.30  # 30% max per sector
MAX_CHURN_PER_WEEK = 3  # Max 3 symbol changes per week
ROTATION_PCT = 0.20  # Bottom 20% eligible for rotation
MIN_TRADES_FOR_SCORING = 5  # Minimum trades needed for valid score


def get_symbol_sector(symbol: str) -> str:
    """
    Get sector for a symbol.

    Args:
        symbol: Trading symbol

    Returns:
        Sector name
    """
    return SECTOR_MAP.get(symbol, DEFAULT_SECTOR)


def calculate_sharpe_ratio(pnls: List[float], risk_free_rate: float = 0.0) -> float:
    """
    Calculate Sharpe ratio from P&L series.

    Sharpe = (mean_return - risk_free_rate) / std_return

    Args:
        pnls: List of profit/loss values
        risk_free_rate: Risk-free rate (annualized, default 0%)

    Returns:
        Sharpe ratio (higher is better)
    """
    if len(pnls) < 2:
        return 0.0

    returns = np.array(pnls)
    mean_return = np.mean(returns)
    std_return = np.std(returns, ddof=1)

    if std_return == 0:
        return 0.0 if mean_return <= risk_free_rate else np.inf

    sharpe = (mean_return - risk_free_rate) / std_return
    return sharpe


def calculate_symbol_score(
    symbol: str,
    lookback_days: int = 30,
    db_path: Optional[Path] = None
) -> Dict:
    """
    Calculate composite performance score for a symbol.

    Score components (weighted):
    - Sharpe ratio: 40%
    - Win rate: 30%
    - Average P&L: 20%
    - Trade frequency: 10%

    Args:
        symbol: Trading symbol to score
        lookback_days: Number of days to look back for performance
        db_path: Path to database (default: DB_PATH)

    Returns:
        Dictionary with score components and composite score:
        {
            "symbol": str,
            "score": float,  # 0-100 composite score
            "sharpe_ratio": float,
            "win_rate": float,  # 0.0-1.0
            "avg_pnl": float,  # Average profit per trade
            "trade_count": int,
            "sector": str,
            "days_tracked": int,
            "has_min_trades": bool  # Whether >= MIN_TRADES_FOR_SCORING
        }
    """
    if db_path is None:
        db_path = DB_PATH

    # Query closed trades for this symbol within lookback period
    start_date = (datetime.now() - timedelta(days=lookback_days)).isoformat()

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT pnl, status, timestamp
        FROM trades
        WHERE symbol = ?
          AND timestamp >= ?
          AND status IN ('FILLED', 'CLOSED')
          AND pnl IS NOT NULL
        ORDER BY timestamp ASC
    """, (symbol, start_date))

    trades = cursor.fetchall()
    conn.close()

    # Default result for symbols with no trades
    if len(trades) == 0:
        return {
            "symbol": symbol,
            "score": 0.0,
            "sharpe_ratio": 0.0,
            "win_rate": 0.0,
            "avg_pnl": 0.0,
            "trade_count": 0,
            "sector": get_symbol_sector(symbol),
            "days_tracked": lookback_days,
            "has_min_trades": False
        }

    # Extract P&L values
    pnls = [trade["pnl"] for trade in trades]
    trade_count = len(pnls)

    # Calculate components
    sharpe = calculate_sharpe_ratio(pnls)
    win_count = sum(1 for pnl in pnls if pnl > 0)
    win_rate = win_count / trade_count if trade_count > 0 else 0.0
    avg_pnl = np.mean(pnls)

    # Normalize components to 0-100 scale
    # Sharpe: -3 to +3 → 0 to 100
    sharpe_normalized = np.clip((sharpe + 3) / 6 * 100, 0, 100)

    # Win rate: 0% to 100% → 0 to 100
    win_rate_normalized = win_rate * 100

    # Avg P&L: -500 to +500 → 0 to 100
    avg_pnl_normalized = np.clip((avg_pnl + 500) / 1000 * 100, 0, 100)

    # Trade frequency: 0 to 20 trades → 0 to 100
    freq_normalized = np.clip(trade_count / 20 * 100, 0, 100)

    # Composite score (weighted average)
    composite_score = (
        sharpe_normalized * SHARPE_WEIGHT +
        win_rate_normalized * WIN_RATE_WEIGHT +
        avg_pnl_normalized * AVG_PNL_WEIGHT +
        freq_normalized * FREQ_WEIGHT
    )

    return {
        "symbol": symbol,
        "score": round(composite_score, 2),
        "sharpe_ratio": round(sharpe, 3),
        "win_rate": round(win_rate, 3),
        "avg_pnl": round(avg_pnl, 2),
        "trade_count": trade_count,
        "sector": get_symbol_sector(symbol),
        "days_tracked": lookback_days,
        "has_min_trades": trade_count >= MIN_TRADES_FOR_SCORING
    }


def get_current_watchlist(db_path: Optional[Path] = None) -> List[str]:
    """
    Get current active watchlist symbols.

    Args:
        db_path: Path to database (default: DB_PATH)

    Returns:
        List of active symbols
    """
    if db_path is None:
        db_path = DB_PATH

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT symbol
        FROM watchlist
        WHERE active = 1
        ORDER BY priority DESC, symbol ASC
    """)

    symbols = [row["symbol"] for row in cursor.fetchall()]
    conn.close()

    return symbols


def get_recent_churn(days: int = 7, db_path: Optional[Path] = None) -> int:
    """
    Count watchlist changes in the last N days.

    Args:
        days: Number of days to look back
        db_path: Path to database (default: DB_PATH)

    Returns:
        Number of symbols added/removed in period
    """
    if db_path is None:
        db_path = DB_PATH

    cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Count additions
    cursor.execute("""
        SELECT COUNT(*) as count
        FROM watchlist
        WHERE added_at >= ?
    """, (cutoff_date,))

    additions = cursor.fetchone()["count"]

    # Count removals (active=0 with last_updated in period)
    cursor.execute("""
        SELECT COUNT(*) as count
        FROM watchlist
        WHERE active = 0
          AND last_updated >= ?
    """, (cutoff_date,))

    removals = cursor.fetchone()["count"]
    conn.close()

    return additions + removals


def update_watchlist(
    candidate_pool: List[str],
    max_watchlist_size: int = 20,
    lookback_days: int = 30,
    enforce_sector_limits: bool = True,
    db_path: Optional[Path] = None
) -> Dict:
    """
    Update watchlist by rotating underperformers.

    Algorithm:
    1. Score all current watchlist symbols
    2. Identify bottom 20% performers (with min trades)
    3. Score candidate pool
    4. Replace underperformers with top candidates
    5. Enforce sector diversification (max 30% per sector)
    6. Enforce churn limit (max 3 changes per week)

    Args:
        candidate_pool: List of candidate symbols to consider
        max_watchlist_size: Maximum watchlist size (default 20)
        lookback_days: Days to look back for performance (default 30)
        enforce_sector_limits: Whether to enforce sector diversification
        db_path: Path to database (default: DB_PATH)

    Returns:
        Dictionary with update results:
        {
            "added": List[str],
            "removed": List[str],
            "scores": Dict[str, Dict],  # symbol -> score details
            "churn_limit_reached": bool,
            "sector_distribution": Dict[str, int]
        }
    """
    if db_path is None:
        db_path = DB_PATH

    # Check churn limit
    recent_churn = get_recent_churn(days=7, db_path=db_path)
    churn_available = MAX_CHURN_PER_WEEK - recent_churn

    if churn_available <= 0:
        warnings.warn(
            f"Churn limit reached ({recent_churn}/{MAX_CHURN_PER_WEEK} changes this week). "
            "No watchlist updates performed."
        )
        return {
            "added": [],
            "removed": [],
            "scores": {},
            "churn_limit_reached": True,
            "sector_distribution": {}
        }

    # Get current watchlist
    current_symbols = get_current_watchlist(db_path)

    # Score current watchlist
    current_scores = {}
    for symbol in current_symbols:
        score_data = calculate_symbol_score(symbol, lookback_days, db_path)
        current_scores[symbol] = score_data

    # Identify underperformers (bottom 20% with min trades)
    scored_symbols = [
        (sym, data) for sym, data in current_scores.items()
        if data["has_min_trades"]
    ]

    if len(scored_symbols) == 0:
        # No symbols with enough trades to score
        return {
            "added": [],
            "removed": [],
            "scores": current_scores,
            "churn_limit_reached": False,
            "sector_distribution": {}
        }

    scored_symbols.sort(key=lambda x: x[1]["score"])
    rotation_count = max(1, int(len(scored_symbols) * ROTATION_PCT))
    rotation_count = min(rotation_count, churn_available)  # Respect churn limit

    underperformers = [sym for sym, _ in scored_symbols[:rotation_count]]

    # Score candidate pool
    candidate_scores = {}
    for symbol in candidate_pool:
        if symbol not in current_symbols:  # Don't re-add current symbols
            score_data = calculate_symbol_score(symbol, lookback_days, db_path)
            candidate_scores[symbol] = score_data

    # Rank candidates by score
    ranked_candidates = sorted(
        candidate_scores.items(),
        key=lambda x: x[1]["score"],
        reverse=True
    )

    # Select replacements (respecting sector limits if enabled)
    added = []
    removed = []

    # Calculate current sector distribution
    remaining_symbols = [s for s in current_symbols if s not in underperformers]
    sector_counts = {}
    for symbol in remaining_symbols:
        sector = get_symbol_sector(symbol)
        sector_counts[sector] = sector_counts.get(sector, 0) + 1

    # Add candidates to fill slots
    max_total_symbols = min(max_watchlist_size, len(current_symbols))

    for candidate, score_data in ranked_candidates:
        if len(added) >= len(underperformers):
            break  # Filled all open slots

        # Check sector limit
        if enforce_sector_limits:
            sector = score_data["sector"]
            current_sector_count = sector_counts.get(sector, 0)
            projected_total = len(remaining_symbols) + len(added)

            if projected_total == 0:
                sector_pct = 0
            else:
                sector_pct = (current_sector_count + 1) / projected_total

            if sector_pct > MAX_SECTOR_PCT:
                continue  # Skip, would violate sector limit

        # Add candidate
        added.append(candidate)
        sector = score_data["sector"]
        sector_counts[sector] = sector_counts.get(sector, 0) + 1

    # Only remove as many underperformers as we can replace
    removed = underperformers[:len(added)]

    # Update database
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    now = datetime.now().isoformat()

    try:
        # Remove underperformers
        for symbol in removed:
            cursor.execute("""
                UPDATE watchlist
                SET active = 0, last_updated = ?
                WHERE symbol = ?
            """, (now, symbol))

        # Add new symbols
        for symbol in added:
            # Check if symbol already exists (was previously removed)
            cursor.execute("SELECT symbol FROM watchlist WHERE symbol = ?", (symbol,))
            exists = cursor.fetchone() is not None

            if exists:
                # Reactivate
                cursor.execute("""
                    UPDATE watchlist
                    SET active = 1, last_updated = ?, priority = 5
                    WHERE symbol = ?
                """, (now, symbol))
            else:
                # Insert new
                cursor.execute("""
                    INSERT INTO watchlist (symbol, added_at, active, priority, notes)
                    VALUES (?, ?, 1, 5, 'Auto-added by watchlist manager')
                """, (symbol, now))

        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

    # Merge scores
    all_scores = {**current_scores, **candidate_scores}

    return {
        "added": added,
        "removed": removed,
        "scores": all_scores,
        "churn_limit_reached": False,
        "sector_distribution": sector_counts
    }


def get_watchlist_performance_report(
    lookback_days: int = 30,
    db_path: Optional[Path] = None
) -> Dict:
    """
    Generate performance report for current watchlist.

    Args:
        lookback_days: Days to look back for performance
        db_path: Path to database (default: DB_PATH)

    Returns:
        Dictionary with performance metrics:
        {
            "symbol_scores": List[Dict],  # Sorted by score (desc)
            "avg_score": float,
            "total_trades": int,
            "sector_distribution": Dict[str, int],
            "underperformers": List[str],  # Bottom 20%
            "top_performers": List[str]  # Top 20%
        }
    """
    if db_path is None:
        db_path = DB_PATH

    current_symbols = get_current_watchlist(db_path)

    # Score all symbols
    scores = []
    total_trades = 0
    sector_dist = {}

    for symbol in current_symbols:
        score_data = calculate_symbol_score(symbol, lookback_days, db_path)
        scores.append(score_data)
        total_trades += score_data["trade_count"]

        sector = score_data["sector"]
        sector_dist[sector] = sector_dist.get(sector, 0) + 1

    # Sort by score
    scores.sort(key=lambda x: x["score"], reverse=True)

    # Calculate average score
    avg_score = np.mean([s["score"] for s in scores]) if scores else 0.0

    # Identify top and bottom performers
    count = len(scores)
    top_20_count = max(1, int(count * 0.2))
    bottom_20_count = max(1, int(count * 0.2))

    top_performers = [s["symbol"] for s in scores[:top_20_count]]
    underperformers = [s["symbol"] for s in scores[-bottom_20_count:]]

    return {
        "symbol_scores": scores,
        "avg_score": round(avg_score, 2),
        "total_trades": total_trades,
        "sector_distribution": sector_dist,
        "underperformers": underperformers,
        "top_performers": top_performers
    }
