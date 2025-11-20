"""
Data Quality Validation and Pre-Flight Checks

Validates market data quality before analysis and trading operations.
Ensures data is fresh, complete, and meets minimum requirements for
technical indicator calculations and swarm intelligence analysis.
"""

import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import warnings

# Data lake path
DATA_LAKE = Path(__file__).parent.parent / "data_lake"
CACHE_DB = DATA_LAKE / "trades.db"  # Using unified trades.db for all data

# Data quality thresholds
DEFAULT_MAX_AGE_HOURS = 1  # Data older than 1 hour is stale during market hours
DEFAULT_MIN_DAILY_BARS = 30  # Minimum daily bars for technical analysis
DEFAULT_MIN_HOURLY_BARS = 50  # Minimum hourly bars
DEFAULT_MIN_5MIN_BARS = 390  # Minimum 5-min bars (3 trading days)

# Market hours (US Eastern Time)
MARKET_OPEN_HOUR = 9
MARKET_OPEN_MINUTE = 30
MARKET_CLOSE_HOUR = 16
MARKET_CLOSE_MINUTE = 0


def validate_data_quality(
    symbols: List[str],
    min_daily_bars: int = DEFAULT_MIN_DAILY_BARS,
    min_hourly_bars: int = DEFAULT_MIN_HOURLY_BARS,
    min_5min_bars: int = DEFAULT_MIN_5MIN_BARS,
    max_age_hours: Optional[float] = None,
    require_all_intervals: bool = True
) -> Dict:
    """
    Validate data quality for a list of symbols.

    Checks:
    - Data freshness (age)
    - Data completeness (bar counts)
    - Data coverage (which intervals have data)

    Args:
        symbols: List of symbols to validate
        min_daily_bars: Minimum required daily bars
        min_hourly_bars: Minimum required hourly bars
        min_5min_bars: Minimum required 5-minute bars
        max_age_hours: Maximum data age in hours (None = skip age check)
        require_all_intervals: Whether all intervals must have data

    Returns:
        Dictionary with validation results:
        {
            "valid": bool,  # Overall validation pass/fail
            "symbols_checked": int,
            "symbols_passed": List[str],
            "symbols_failed": List[str],
            "issues": List[Dict],  # Detailed issues per symbol
            "summary": str,
            "recommendations": List[str]
        }
    """
    if not CACHE_DB.exists():
        return {
            "valid": False,
            "symbols_checked": len(symbols),
            "symbols_passed": [],
            "symbols_failed": symbols,
            "issues": [{
                "symbol": "ALL",
                "severity": "CRITICAL",
                "issue": "Market data cache database not found",
                "detail": f"Expected at: {CACHE_DB}"
            }],
            "summary": "Cache database missing - no data available",
            "recommendations": ["Initialize market data cache database"]
        }

    conn = sqlite3.connect(str(CACHE_DB))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    symbols_passed = []
    symbols_failed = []
    issues = []
    now = datetime.now()

    for symbol in symbols:
        symbol_issues = []

        # Check each interval
        for interval, min_bars in [
            ("daily", min_daily_bars),
            ("1h", min_hourly_bars),
            ("5min", min_5min_bars)
        ]:
            cursor.execute("""
                SELECT COUNT(*) as bar_count,
                       MAX(timestamp) as latest_timestamp
                FROM market_data_bars
                WHERE symbol = ? AND interval = ?
            """, (symbol, interval))

            result = cursor.fetchone()
            bar_count = result["bar_count"] if result else 0
            latest_timestamp = result["latest_timestamp"] if result else None

            # Check bar count
            if bar_count < min_bars:
                symbol_issues.append({
                    "symbol": symbol,
                    "severity": "CRITICAL" if interval == "daily" else "HIGH",
                    "issue": f"Insufficient {interval} bars",
                    "detail": f"Have {bar_count}, need {min_bars}",
                    "interval": interval
                })

            # Check data freshness
            if max_age_hours is not None and latest_timestamp:
                try:
                    latest_dt = datetime.fromisoformat(latest_timestamp)
                    age_hours = (now - latest_dt).total_seconds() / 3600

                    if age_hours > max_age_hours:
                        symbol_issues.append({
                            "symbol": symbol,
                            "severity": "HIGH",
                            "issue": f"Stale {interval} data",
                            "detail": f"Age: {age_hours:.1f} hours (max: {max_age_hours})",
                            "interval": interval,
                            "age_hours": age_hours
                        })
                except (ValueError, TypeError):
                    symbol_issues.append({
                        "symbol": symbol,
                        "severity": "MEDIUM",
                        "issue": f"Invalid timestamp for {interval}",
                        "detail": f"Cannot parse: {latest_timestamp}",
                        "interval": interval
                    })

            # Check if interval has no data at all
            if bar_count == 0:
                symbol_issues.append({
                    "symbol": symbol,
                    "severity": "CRITICAL",
                    "issue": f"No {interval} data",
                    "detail": "Symbol not in cache",
                    "interval": interval
                })

        # Determine if symbol passed
        critical_issues = [i for i in symbol_issues if i["severity"] == "CRITICAL"]

        if require_all_intervals:
            # All intervals must pass
            if len(critical_issues) == 0:
                symbols_passed.append(symbol)
            else:
                symbols_failed.append(symbol)
                issues.extend(symbol_issues)
        else:
            # At least one interval must pass
            if len(symbol_issues) < 9:  # Less than 3 intervals * 3 issues per interval
                symbols_passed.append(symbol)
            else:
                symbols_failed.append(symbol)
                issues.extend(symbol_issues)

    conn.close()

    # Generate summary and recommendations
    valid = len(symbols_failed) == 0

    if valid:
        summary = f"✓ All {len(symbols)} symbols passed data quality validation"
    else:
        summary = f"✗ {len(symbols_failed)}/{len(symbols)} symbols failed validation"

    recommendations = []
    if len(symbols_failed) > 0:
        recommendations.append(
            f"Backfill data for: {', '.join(symbols_failed)}"
        )

    # Check for stale data issues
    stale_issues = [i for i in issues if "stale" in i["issue"].lower()]
    if len(stale_issues) > 0:
        recommendations.append("Refresh stale data - market may be closed or data feed paused")

    # Check for missing data issues
    missing_issues = [i for i in issues if "no" in i["issue"].lower() or "insufficient" in i["issue"].lower()]
    if len(missing_issues) > 0:
        recommendations.append(
            f"Run backfill for {len(set(i['symbol'] for i in missing_issues))} symbols with missing/insufficient data"
        )

    return {
        "valid": valid,
        "symbols_checked": len(symbols),
        "symbols_passed": symbols_passed,
        "symbols_failed": symbols_failed,
        "issues": issues,
        "summary": summary,
        "recommendations": recommendations
    }


def get_data_health_report(symbols: List[str]) -> Dict:
    """
    Get detailed data health metrics for symbols.

    Args:
        symbols: List of symbols to check

    Returns:
        Dictionary with health metrics per symbol:
        {
            "symbol": {
                "intervals": {
                    "daily": {"bars": int, "latest": str, "age_hours": float},
                    "1h": {...},
                    "5min": {...}
                },
                "health_score": float,  # 0-100
                "status": str,  # "HEALTHY", "DEGRADED", "CRITICAL"
                "issues": List[str]
            }
        }
    """
    if not CACHE_DB.exists():
        return {
            symbol: {
                "intervals": {},
                "health_score": 0.0,
                "status": "CRITICAL",
                "issues": ["Cache database not found"]
            }
            for symbol in symbols
        }

    conn = sqlite3.connect(str(CACHE_DB))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    report = {}
    now = datetime.now()

    for symbol in symbols:
        intervals_data = {}
        issues = []

        for interval in ["daily", "1h", "5min"]:
            cursor.execute("""
                SELECT COUNT(*) as bar_count,
                       MAX(timestamp) as latest_timestamp
                FROM market_data_bars
                WHERE symbol = ? AND interval = ?
            """, (symbol, interval))

            result = cursor.fetchone()
            bar_count = result["bar_count"] if result else 0
            latest_timestamp = result["latest_timestamp"] if result else None

            age_hours = None
            if latest_timestamp:
                try:
                    latest_dt = datetime.fromisoformat(latest_timestamp)
                    age_hours = (now - latest_dt).total_seconds() / 3600
                except (ValueError, TypeError):
                    issues.append(f"Invalid timestamp for {interval}")

            intervals_data[interval] = {
                "bars": bar_count,
                "latest": latest_timestamp,
                "age_hours": round(age_hours, 2) if age_hours else None
            }

            # Check for issues
            if bar_count == 0:
                issues.append(f"No {interval} data")
            elif bar_count < DEFAULT_MIN_DAILY_BARS and interval == "daily":
                issues.append(f"Insufficient {interval} bars ({bar_count} < {DEFAULT_MIN_DAILY_BARS})")

            if age_hours and age_hours > 24:
                issues.append(f"Stale {interval} data ({age_hours:.1f}h old)")

        # Calculate health score (0-100)
        score = 100.0

        # Deduct for missing intervals
        for interval, data in intervals_data.items():
            if data["bars"] == 0:
                score -= 30
            elif interval == "daily" and data["bars"] < DEFAULT_MIN_DAILY_BARS:
                score -= 15

            # Deduct for stale data
            if data["age_hours"]:
                if data["age_hours"] > 24:
                    score -= 20
                elif data["age_hours"] > 8:
                    score -= 10

        score = max(0.0, score)

        # Determine status
        if score >= 80:
            status = "HEALTHY"
        elif score >= 50:
            status = "DEGRADED"
        else:
            status = "CRITICAL"

        report[symbol] = {
            "intervals": intervals_data,
            "health_score": round(score, 1),
            "status": status,
            "issues": issues
        }

    conn.close()
    return report


def auto_trigger_backfill(
    symbols: List[str],
    missing_intervals: Optional[List[str]] = None,
    days: int = 60
) -> Dict:
    """
    Automatically trigger backfill for symbols with missing/stale data.

    This is a placeholder that prepares backfill tasks.
    Actual backfill execution happens in background_tasks.py.

    Args:
        symbols: Symbols needing backfill
        missing_intervals: Specific intervals to backfill (None = all)
        days: Days of history to backfill

    Returns:
        Dictionary with backfill task information:
        {
            "tasks_created": int,
            "symbols": List[str],
            "intervals": List[str],
            "estimated_api_calls": int,
            "status": str
        }
    """
    if missing_intervals is None:
        missing_intervals = ["5min", "1h", "daily"]

    # Estimate API calls needed
    # Assuming: daily=1 call, 1h=3 calls, 5min=12 calls per 60 days
    calls_per_interval = {"daily": 1, "1h": 3, "5min": 12}
    estimated_calls = sum(
        calls_per_interval.get(interval, 1)
        for interval in missing_intervals
    ) * len(symbols)

    return {
        "tasks_created": len(symbols) * len(missing_intervals),
        "symbols": symbols,
        "intervals": missing_intervals,
        "days": days,
        "estimated_api_calls": estimated_calls,
        "status": "QUEUED",
        "note": "Backfill tasks queued for background processing"
    }


# Export functions for use in other modules
__all__ = [
    "validate_data_quality",
    "get_data_health_report",
    "auto_trigger_backfill"
]
