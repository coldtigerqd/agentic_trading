"""
市场日历和交易时段检测

检测美国股市交易时间、假期和交易时段。
帮助优化分析时机并避免在非交易时段浪费 API 调用。
"""

from datetime import datetime, time, timedelta
from typing import Dict, Optional, Tuple
from zoneinfo import ZoneInfo
import warnings

# 东部时区
ET = ZoneInfo("America/New_York")

# 美国股市交易时间（东部时间）
MARKET_OPEN_TIME = time(9, 30)  # 上午 9:30 ET
MARKET_CLOSE_TIME = time(16, 0)  # 下午 4:00 PM ET
PREMARKET_OPEN_TIME = time(4, 0)  # 凌晨 4:00 AM ET
AFTERHOURS_CLOSE_TIME = time(20, 0)  # 晚上 8:00 PM ET

# 交易日（周一=0 ... 周日=6）
TRADING_DAYS = [0, 1, 2, 3, 4]  # 周一至周五

# 2025 年美国股市假期（NYSE/NASDAQ）
# 来源: https://www.nyse.com/markets/hours-calendars
MARKET_HOLIDAYS_2025 = [
    "2025-01-01",  # 元旦
    "2025-01-20",  # 马丁·路德·金纪念日
    "2025-02-17",  # 总统日
    "2025-04-18",  # 耶稣受难日
    "2025-05-26",  # 阵亡将士纪念日
    "2025-07-04",  # 独立日
    "2025-09-01",  # 劳动节
    "2025-11-27",  # 感恩节
    "2025-12-25",  # 圣诞节
]

# 提前收盘日（下午 1:00 PM ET 收盘）
EARLY_CLOSE_DAYS_2025 = [
    "2025-07-03",  # 独立日前一天
    "2025-11-28",  # 感恩节后一天
    "2025-12-24",  # 平安夜
]

EARLY_CLOSE_TIME = time(13, 0)  # 下午 1:00 PM ET


def is_market_holiday(date: Optional[datetime] = None) -> bool:
    """
    检查给定日期是否为市场假期。

    参数:
        date: 要检查的日期（默认：今天）

    返回:
        如果市场因假期休市则返回 True
    """
    if date is None:
        date = datetime.now(ET)

    date_str = date.strftime("%Y-%m-%d")
    return date_str in MARKET_HOLIDAYS_2025


def is_trading_day(date: Optional[datetime] = None) -> bool:
    """
    检查给定日期是否为交易日（非周末或假期）。

    参数:
        date: 要检查的日期（默认：今天）

    返回:
        如果市场开放交易则返回 True
    """
    if date is None:
        date = datetime.now(ET)

    # 检查是否为周末
    if date.weekday() not in TRADING_DAYS:
        return False

    # 检查是否为假期
    if is_market_holiday(date):
        return False

    return True


def is_early_close_day(date: Optional[datetime] = None) -> bool:
    """
    检查给定日期是否为提前收盘日（下午 1:00 PM ET）。

    参数:
        date: 要检查的日期（默认：今天）

    返回:
        如果市场提前收盘则返回 True
    """
    if date is None:
        date = datetime.now(ET)

    date_str = date.strftime("%Y-%m-%d")
    return date_str in EARLY_CLOSE_DAYS_2025


def get_market_hours(date: Optional[datetime] = None) -> Dict:
    """
    获取特定日期的市场交易时间。

    参数:
        date: 要检查的日期（默认：今天）

    返回:
        包含市场交易时间的字典:
        {
            "date": str,
            "is_trading_day": bool,
            "is_holiday": bool,
            "is_early_close": bool,
            "premarket_open": str,  # "04:00:00"
            "market_open": str,  # "09:30:00"
            "market_close": str,  # "16:00:00" 或 "13:00:00"
            "afterhours_close": str  # "20:00:00"
        }
    """
    if date is None:
        date = datetime.now(ET)

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
    检查美国股市当前是否开放常规交易。

    参数:
        dt: 要检查的日期时间（默认：东部时间当前时间）

    返回:
        如果市场开放常规交易时段则返回 True

    注意:
        此函数自动转换为东部时间（ET）。
    """
    if dt is None:
        dt = datetime.now(ET)
    elif dt.tzinfo is None:
        # 如果提供的是简单日期时间，假定为 ET
        dt = dt.replace(tzinfo=ET)
    else:
        # 如果是不同时区，转换为 ET
        dt = dt.astimezone(ET)

    # 检查是否为交易日
    if not is_trading_day(dt):
        return False

    # 检查市场交易时间
    current_time = dt.time()
    close_time = EARLY_CLOSE_TIME if is_early_close_day(dt) else MARKET_CLOSE_TIME

    return MARKET_OPEN_TIME <= current_time < close_time


def is_premarket(dt: Optional[datetime] = None) -> bool:
    """
    检查当前是否处于盘前时段（上午 4:00 - 9:30 AM ET）。

    参数:
        dt: 要检查的日期时间（默认：东部时间当前时间）

    返回:
        如果处于盘前时段则返回 True
    """
    if dt is None:
        dt = datetime.now(ET)

    if not is_trading_day(dt):
        return False

    current_time = dt.time()
    return PREMARKET_OPEN_TIME <= current_time < MARKET_OPEN_TIME


def is_afterhours(dt: Optional[datetime] = None) -> bool:
    """
    检查当前是否处于盘后交易时段（下午 4:00 PM - 8:00 PM ET）。

    参数:
        dt: 要检查的日期时间（默认：当前时间）

    返回:
        如果处于盘后时段则返回 True
    """
    if dt is None:
        dt = datetime.now(ET)

    if not is_trading_day(dt):
        return False

    current_time = dt.time()
    close_time = EARLY_CLOSE_TIME if is_early_close_day(dt) else MARKET_CLOSE_TIME

    return close_time <= current_time < AFTERHOURS_CLOSE_TIME


def get_market_session_info(dt: Optional[datetime] = None) -> Dict:
    """
    获取全面的市场交易时段信息。

    参数:
        dt: 要检查的日期时间（默认：当前时间）

    返回:
        包含交易时段信息的字典:
        {
            "timestamp": str,
            "is_trading_day": bool,
            "session": str,  # "CLOSED", "PREMARKET", "REGULAR", "AFTERHOURS"
            "market_open": bool,  # 如果为常规时段则为 True
            "is_holiday": bool,
            "is_early_close": bool,
            "next_market_open": str,  # ISO 时间戳
            "time_to_open_minutes": int  # 距下次开盘的分钟数
        }
    """
    if dt is None:
        dt = datetime.now(ET)

    trading_day = is_trading_day(dt)
    holiday = is_market_holiday(dt)
    early_close = is_early_close_day(dt)

    # 确定交易时段
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

    # 计算下次开盘时间
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
    获取下次市场开盘时间。

    参数:
        dt: 当前日期时间（默认：当前时间）

    返回:
        包含 (下次开盘日期时间, 距开盘分钟数) 的元组
    """
    if dt is None:
        dt = datetime.now(ET)

    # 如果市场当前开放，返回当前时间
    if is_market_open(dt):
        return dt, 0

    # 从当天开始检查
    check_date = dt
    max_days_ahead = 10  # 不搜索超过 10 天

    for _ in range(max_days_ahead):
        # 如果是交易日
        if is_trading_day(check_date):
            market_open_dt = datetime.combine(check_date.date(), MARKET_OPEN_TIME, tzinfo=ET)

            # 如果这个开盘时间在未来（即使是当天也可能已经过了开盘时间）
            if market_open_dt > dt:
                time_to_open = int((market_open_dt - dt).total_seconds() / 60)
                return market_open_dt, time_to_open

        # 移至下一天的午夜（00:00），而不是开盘时间
        # 这样下一次循环时 market_open_dt > dt 的比较才能正确工作
        check_date = datetime.combine(
            check_date.date() + timedelta(days=1),
            time(0, 0),  # 使用午夜而不是开盘时间
            tzinfo=ET
        )

    # 未来 10 天内未找到市场开盘时间
    warnings.warn("未能在 10 天内找到下次市场开盘时间 (NO_MARKET_OPEN_FOUND)")
    return None, -1


def get_recommended_analysis_frequency(session: str) -> str:
    """
    根据市场交易时段获取推荐的分析频率。

    参数:
        session: 市场时段（"CLOSED", "PREMARKET", "REGULAR", "AFTERHOURS"）

    返回:
        可读的推荐频率字符串
    """
    recommendations = {
        "CLOSED": "每小时或更低频率（市场休市）",
        "PREMARKET": "每 5-15 分钟（成交量低）",
        "REGULAR": "每 1-5 分钟（活跃交易）",
        "AFTERHOURS": "每 10-30 分钟（成交量较低）"
    }

    return recommendations.get(session, "每 5 分钟")


# 导出关键函数
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
