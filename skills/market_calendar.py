"""
Market Calendar and Trading Hours Detection

Detect US stock market hours, holidays, and trading sessions.
Helps optimize analysis timing and avoid wasted API calls during off-hours.
"""

from datetime import datetime, time, timedelta
from typing import Dict, Optional, Tuple
import warnings

# US Stock Market Hours (Eastern Time)
MARKET_OPEN_TIME = time(9, 30)  # 9:30 AM ET
MARKET_CLOSE_TIME = time(16, 0)  # 4:00 PM ET
PREMARKET_OPEN_TIME = time(4, 0)  # 4:00 AM ET
AFTERHOURS_CLOSE_TIME = time(20, 0)  # 8:00 PM ET

# Trading days (Monday=0 ... Sunday=6)
TRADING_DAYS = [0, 1, 2, 3, 4]  # Monday through Friday

# 2025 US Stock Market Holidays (NYSE/NASDAQ)
# Source: https://www.nyse.com/markets/hours-calendars
MARKET_HOLIDAYS_2025 = [
    "2025-01-01",  # New Year's Day
    "2025-01-20",  # Martin Luther King Jr. Day
    "2025-02-17",  # Presidents Day
    "2025-04-18",  # Good Friday
    "2025-05-26",  # Memorial Day
    "2025-07-04",  # Independence Day
    "2025-09-01",  # Labor Day
    "2025-11-27",  # Thanksgiving Day
    "2025-12-25",  # Christmas Day
]

# Early close days (1:00 PM ET close)
EARLY_CLOSE_DAYS_2025 = [
    "2025-07-03",  # Day before Independence Day
    "2025-11-28",  # Day after Thanksgiving
    "2025-12-24",  # Christmas Eve
]

EARLY_CLOSE_TIME = time(13, 0)  # 1:00 PM ET


def is_market_holiday(date: Optional[datetime] = None) -> bool:
    """
    Check if a given date is a market holiday.

    Args:
        date: Date to check (default: today)

    Returns:
        True if market is closed for holiday
    """
    if date is None:
        date = datetime.now()

    date_str = date.strftime("%Y-%m-%d")
    return date_str in MARKET_HOLIDAYS_2025


def is_trading_day(date: Optional[datetime] = None) -> bool:
    """
    Check if a given date is a trading day (not weekend or holiday).

    Args:
        date: Date to check (default: today)

    Returns:
        True if market is open for trading
    """
    if date is None:
        date = datetime.now()

    # Check if weekend
    if date.weekday() not in TRADING_DAYS:
        return False

    # Check if holiday
    if is_market_holiday(date):
        return False

    return True


def is_early_close_day(date: Optional[datetime] = None) -> bool:
    """
    Check if a given date has early market close (1:00 PM ET).

    Args:
        date: Date to check (default: today)

    Returns:
        True if market closes early
    """
    if date is None:
        date = datetime.now()

    date_str = date.strftime("%Y-%m-%d")
    return date_str in EARLY_CLOSE_DAYS_2025


def get_market_hours(date: Optional[datetime] = None) -> Dict:
    """
    Get market hours for a specific date.

    Args:
        date: Date to check (default: today)

    Returns:
        Dictionary with market hours:
        {
            "date": str,
            "is_trading_day": bool,
            "is_holiday": bool,
            "is_early_close": bool,
            "premarket_open": str,  # "04:00:00"
            "market_open": str,  # "09:30:00"
            "market_close": str,  # "16:00:00" or "13:00:00"
            "afterhours_close": str  # "20:00:00"
        }
    """
    if date is None:
        date = datetime.now()

    is_trading = is_trading_day(date)
    is_holiday = is_market_holiday(date)
    is_early = is_early_close_day(date)

    close_time = EARLY_CLOSE_TIME if is_early else MARKET_CLOSE_TIME

    return {
        "date": date.strftime("%Y-%m-%d"),
        "is_trading_day": is_trading,
        "is_holiday": is_holiday,
        "is_early_close": is_early,
        "premarket_open": PREMARKET_OPEN_TIME.strftime("%H:%M:%S"),
        "market_open": MARKET_OPEN_TIME.strftime("%H:%M:%S"),
        "market_close": close_time.strftime("%H:%M:%S"),
        "afterhours_close": AFTERHOURS_CLOSE_TIME.strftime("%H:%M:%S")
    }


def is_market_open(dt: Optional[datetime] = None) -> bool:
    """
    Check if US stock market is currently open for regular trading.

    Args:
        dt: Datetime to check (default: now in local time)

    Returns:
        True if market is open for regular trading session

    Note:
        This function assumes the input datetime is in Eastern Time (ET).
        For accurate results, convert your local time to ET first.
    """
    if dt is None:
        dt = datetime.now()

    # Check if trading day
    if not is_trading_day(dt):
        return False

    # Check market hours
    current_time = dt.time()
    close_time = EARLY_CLOSE_TIME if is_early_close_day(dt) else MARKET_CLOSE_TIME

    return MARKET_OPEN_TIME <= current_time < close_time


def is_premarket(dt: Optional[datetime] = None) -> bool:
    """
    Check if we're in pre-market hours (4:00 AM - 9:30 AM ET).

    Args:
        dt: Datetime to check (default: now)

    Returns:
        True if in pre-market session
    """
    if dt is None:
        dt = datetime.now()

    if not is_trading_day(dt):
        return False

    current_time = dt.time()
    return PREMARKET_OPEN_TIME <= current_time < MARKET_OPEN_TIME


def is_afterhours(dt: Optional[datetime] = None) -> bool:
    """
    Check if we're in after-hours trading (4:00 PM - 8:00 PM ET).

    Args:
        dt: Datetime to check (default: now)

    Returns:
        True if in after-hours session
    """
    if dt is None:
        dt = datetime.now()

    if not is_trading_day(dt):
        return False

    current_time = dt.time()
    close_time = EARLY_CLOSE_TIME if is_early_close_day(dt) else MARKET_CLOSE_TIME

    return close_time <= current_time < AFTERHOURS_CLOSE_TIME


def get_market_session_info(dt: Optional[datetime] = None) -> Dict:
    """
    Get comprehensive market session information.

    Args:
        dt: Datetime to check (default: now)

    Returns:
        Dictionary with session info:
        {
            "timestamp": str,
            "is_trading_day": bool,
            "session": str,  # "CLOSED", "PREMARKET", "REGULAR", "AFTERHOURS"
            "market_open": bool,  # True if regular session
            "is_holiday": bool,
            "is_early_close": bool,
            "next_market_open": str,  # ISO timestamp
            "time_to_open_minutes": int  # Minutes until next open
        }
    """
    if dt is None:
        dt = datetime.now()

    trading_day = is_trading_day(dt)
    holiday = is_market_holiday(dt)
    early_close = is_early_close_day(dt)

    # Determine session
    if not trading_day:
        session = "CLOSED"
    elif is_premarket(dt):
        session = "PREMARKET"
    elif is_market_open(dt):
        session = "REGULAR"
    elif is_afterhours(dt):
        session = "AFTERHOURS"
    else:
        session = "CLOSED"

    # Calculate next market open
    next_open, time_to_open = get_next_market_open(dt)

    return {
        "timestamp": dt.isoformat(),
        "is_trading_day": trading_day,
        "session": session,
        "market_open": is_market_open(dt),
        "is_holiday": holiday,
        "is_early_close": early_close,
        "next_market_open": next_open.isoformat() if next_open else None,
        "time_to_open_minutes": time_to_open
    }


def get_next_market_open(dt: Optional[datetime] = None) -> Tuple[Optional[datetime], int]:
    """
    Get the next market open time.

    Args:
        dt: Current datetime (default: now)

    Returns:
        Tuple of (next_open_datetime, minutes_until_open)
    """
    if dt is None:
        dt = datetime.now()

    # If market is currently open, return now
    if is_market_open(dt):
        return dt, 0

    # Start checking from current day
    check_date = dt
    max_days_ahead = 10  # Don't search more than 10 days ahead

    for _ in range(max_days_ahead):
        # If current time is before market open on a trading day
        if is_trading_day(check_date):
            market_open_dt = datetime.combine(check_date.date(), MARKET_OPEN_TIME)

            # If we're on a trading day but before open time
            if check_date.time() < MARKET_OPEN_TIME:
                time_to_open = int((market_open_dt - check_date).total_seconds() / 60)
                return market_open_dt, time_to_open

        # Move to next day at market open time
        check_date = datetime.combine(
            check_date.date() + timedelta(days=1),
            MARKET_OPEN_TIME
        )

    # No market open found in next 10 days
    warnings.warn("Could not find next market open within 10 days")
    return None, -1


def get_recommended_analysis_frequency(session: str) -> str:
    """
    Get recommended analysis frequency based on market session.

    Args:
        session: Market session ("CLOSED", "PREMARKET", "REGULAR", "AFTERHOURS")

    Returns:
        Recommended frequency as human-readable string
    """
    recommendations = {
        "CLOSED": "Hourly or less frequent (market closed)",
        "PREMARKET": "Every 5-15 minutes (low volume)",
        "REGULAR": "Every 1-5 minutes (active trading)",
        "AFTERHOURS": "Every 10-30 minutes (lower volume)"
    }

    return recommendations.get(session, "Every 5 minutes")


# Export key functions
__all__ = [
    "is_market_open",
    "is_trading_day",
    "is_market_holiday",
    "is_premarket",
    "is_afterhours",
    "get_market_session_info",
    "get_next_market_open",
    "get_market_hours",
    "get_recommended_analysis_frequency"
]
