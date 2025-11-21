"""
数据质量验证与飞行前检查

在分析和交易操作之前验证市场数据质量。
确保数据新鲜、完整，并满足技术指标计算和
群体智能分析的最低要求。
"""

import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import warnings

# 数据湖路径
DATA_LAKE = Path(__file__).parent.parent / "data_lake"
CACHE_DB = DATA_LAKE / "trades.db"  # 使用统一的 trades.db 存储所有数据

# 数据质量阈值
DEFAULT_MAX_AGE_HOURS = 1  # 市场开盘期间，超过 1 小时的数据被视为过时
DEFAULT_MIN_DAILY_BARS = 30  # 技术分析所需的最少日线柱数
DEFAULT_MIN_HOURLY_BARS = 50  # 最少小时线柱数
DEFAULT_MIN_5MIN_BARS = 390  # 最少 5 分钟线柱数（3 个交易日）

# 市场时间（美东时间）
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
    验证标的列表的数据质量。

    检查：
    - 数据新鲜度（时效性）
    - 数据完整性（柱数）
    - 数据覆盖范围（哪些时间间隔有数据）

    Args:
        symbols: 要验证的标的列表
        min_daily_bars: 所需的最少日线柱数
        min_hourly_bars: 所需的最少小时线柱数
        min_5min_bars: 所需的最少 5 分钟线柱数
        max_age_hours: 最大数据时效（小时）（None = 跳过时效检查）
        require_all_intervals: 是否所有时间间隔都必须有数据

    Returns:
        包含验证结果的字典：
        {
            "valid": bool,  # 整体验证是否通过
            "symbols_checked": int,
            "symbols_passed": List[str],
            "symbols_failed": List[str],
            "issues": List[Dict],  # 每个标的的详细问题
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
                "issue": "未找到市场数据缓存数据库 (CACHE_DB_NOT_FOUND)",
                "detail": f"预期位置：{CACHE_DB}"
            }],
            "summary": "缺少缓存数据库 - 无可用数据",
            "recommendations": ["初始化市场数据缓存数据库"]
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

        # 检查每个时间间隔
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

            # 检查柱数
            if bar_count < min_bars:
                symbol_issues.append({
                    "symbol": symbol,
                    "severity": "CRITICAL" if interval == "daily" else "HIGH",
                    "issue": f"{interval} 柱数不足 (INSUFFICIENT_BARS)",
                    "detail": f"拥有 {bar_count} 柱，需要 {min_bars} 柱",
                    "interval": interval
                })

            # 检查数据新鲜度
            if max_age_hours is not None and latest_timestamp:
                try:
                    latest_dt = datetime.fromisoformat(latest_timestamp)
                    age_hours = (now - latest_dt).total_seconds() / 3600

                    if age_hours > max_age_hours:
                        symbol_issues.append({
                            "symbol": symbol,
                            "severity": "HIGH",
                            "issue": f"{interval} 数据过时 (STALE_DATA)",
                            "detail": f"时效：{age_hours:.1f} 小时（最大：{max_age_hours}）",
                            "interval": interval,
                            "age_hours": age_hours
                        })
                except (ValueError, TypeError):
                    symbol_issues.append({
                        "symbol": symbol,
                        "severity": "MEDIUM",
                        "issue": f"{interval} 的时间戳无效 (INVALID_TIMESTAMP)",
                        "detail": f"无法解析：{latest_timestamp}",
                        "interval": interval
                    })

            # 检查时间间隔是否完全没有数据
            if bar_count == 0:
                symbol_issues.append({
                    "symbol": symbol,
                    "severity": "CRITICAL",
                    "issue": f"无 {interval} 数据 (NO_DATA)",
                    "detail": "标的不在缓存中",
                    "interval": interval
                })

        # 判断标的是否通过
        critical_issues = [i for i in symbol_issues if i["severity"] == "CRITICAL"]

        if require_all_intervals:
            # 所有时间间隔都必须通过
            if len(critical_issues) == 0:
                symbols_passed.append(symbol)
            else:
                symbols_failed.append(symbol)
                issues.extend(symbol_issues)
        else:
            # 至少一个时间间隔必须通过
            if len(symbol_issues) < 9:  # 少于 3 个时间间隔 * 每个时间间隔 3 个问题
                symbols_passed.append(symbol)
            else:
                symbols_failed.append(symbol)
                issues.extend(symbol_issues)

    conn.close()

    # 生成总结和建议
    valid = len(symbols_failed) == 0

    if valid:
        summary = f"✓ 所有 {len(symbols)} 个标的都通过了数据质量验证"
    else:
        summary = f"✗ {len(symbols_failed)}/{len(symbols)} 个标的验证失败"

    recommendations = []
    if len(symbols_failed) > 0:
        recommendations.append(
            f"回填以下标的的数据：{', '.join(symbols_failed)}"
        )

    # 检查过时数据问题
    stale_issues = [i for i in issues if "过时" in i["issue"]]
    if len(stale_issues) > 0:
        recommendations.append("刷新过时数据 - 市场可能已关闭或数据源已暂停")

    # 检查缺失数据问题
    missing_issues = [i for i in issues if "无" in i["issue"] or "不足" in i["issue"]]
    if len(missing_issues) > 0:
        recommendations.append(
            f"对 {len(set(i['symbol'] for i in missing_issues))} 个缺失/数据不足的标的运行回填"
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
    获取标的的详细数据健康度指标。

    Args:
        symbols: 要检查的标的列表

    Returns:
        包含每个标的健康度指标的字典：
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
                "issues": ["未找到缓存数据库 (CACHE_DB_NOT_FOUND)"]
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
                    issues.append(f"{interval} 的时间戳无效 (INVALID_TIMESTAMP)")

            intervals_data[interval] = {
                "bars": bar_count,
                "latest": latest_timestamp,
                "age_hours": round(age_hours, 2) if age_hours else None
            }

            # 检查问题
            if bar_count == 0:
                issues.append(f"无 {interval} 数据 (NO_DATA)")
            elif bar_count < DEFAULT_MIN_DAILY_BARS and interval == "daily":
                issues.append(f"{interval} 柱数不足（{bar_count} < {DEFAULT_MIN_DAILY_BARS}）(INSUFFICIENT_BARS)")

            if age_hours and age_hours > 24:
                issues.append(f"{interval} 数据过时（{age_hours:.1f} 小时）(STALE_DATA)")

        # 计算健康度评分（0-100）
        score = 100.0

        # 扣除缺失时间间隔的分数
        for interval, data in intervals_data.items():
            if data["bars"] == 0:
                score -= 30
            elif interval == "daily" and data["bars"] < DEFAULT_MIN_DAILY_BARS:
                score -= 15

            # 扣除过时数据的分数
            if data["age_hours"]:
                if data["age_hours"] > 24:
                    score -= 20
                elif data["age_hours"] > 8:
                    score -= 10

        score = max(0.0, score)

        # 确定状态
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
    自动为缺失/过时数据的标的触发回填。

    这是一个准备回填任务的占位符。
    实际的回填执行在 background_tasks.py 中进行。

    Args:
        symbols: 需要回填的标的
        missing_intervals: 要回填的特定时间间隔（None = 全部）
        days: 要回填的历史天数

    Returns:
        包含回填任务信息的字典：
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

    # 估算所需的 API 调用次数
    # 假设：daily=1 次调用，1h=3 次调用，5min=12 次调用（60 天）
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
        "note": "回填任务已排队，等待后台处理"
    }


# 导出函数供其他模块使用
__all__ = [
    "validate_data_quality",
    "get_data_health_report",
    "auto_trigger_backfill"
]
