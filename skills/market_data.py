"""
市场数据技能 - Claude Code 可调用的市场数据函数。

提供历史 OHLCV 数据访问、监控列表管理和数据质量指标。
"""

import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from data_lake.market_data_manager import (
    get_bars,
    get_latest_bar,
    get_freshness_info,
    OHLCVBar
)
from .watchlist_manager import (
    get_current_watchlist,
    add_to_watchlist as _add_to_watchlist,
    remove_from_watchlist as _remove_from_watchlist
)


def get_historical_bars(
    symbol: str,
    interval: str = "5min",
    lookback_days: int = 30
) -> Dict:
    """
    查询标的的历史 OHLCV K线数据。

    支持从5分钟基础数据即时聚合的多个时间周期。
    如果数据缺失，返回 cache_hit=false 以表示需要延迟回填。

    参数:
        symbol: 股票代码（例如 "AAPL"）
        interval: K线周期 - "5min", "15min", "1h", 或 "daily"
        lookback_days: 回溯天数

    返回:
        包含 K线数据和元数据的字典

    示例:
        ```python
        # 获取 30 天的 5 分钟K线
        result = get_historical_bars("AAPL", interval="5min", lookback_days=30)

        if result["cache_hit"]:
            print(f"获取到 {result['bar_count']} 根K线")
            for bar in result["bars"][:5]:  # 前5根K线
                print(f"{bar['timestamp']}: ${bar['close']}")
        else:
            print(f"缓存未命中 - 需要回填 {symbol} 的数据")
        ```
    """
    start_time = time.time()

    # 计算日期范围
    end = datetime.now()
    start = end - timedelta(days=lookback_days)

    # 查询K线
    try:
        bars = get_bars(symbol.upper(), start, end, interval)

        # 转换为字典格式
        bars_dict = [bar.to_dict() for bar in bars]

        # 预期K线数量（近似值）
        trading_days = lookback_days * (5/7)  # 每周约5个交易日
        if interval == "5min":
            expected_bars = int(trading_days * 78)  # 每天78根K线
        elif interval == "15min":
            expected_bars = int(trading_days * 26)  # 每天26根K线
        elif interval == "1h":
            expected_bars = int(trading_days * 6.5)  # 每天6.5小时
        else:  # daily
            expected_bars = int(trading_days)

        # 检查缓存命中率
        cache_hit = len(bars) >= (expected_bars * 0.8)  # 80% 阈值

        # 获取数据质量信息
        freshness = get_freshness_info(symbol.upper())

        query_time_ms = int((time.time() - start_time) * 1000)

        return {
            "symbol": symbol.upper(),
            "interval": interval,
            "lookback_days": lookback_days,
            "bars": bars_dict,
            "bar_count": len(bars),
            "expected_bars": expected_bars,
            "cache_hit": cache_hit,
            "query_time_ms": query_time_ms,
            "data_quality": {
                "freshness_seconds": _calculate_freshness_seconds(freshness) if freshness else None,
                "coverage_start": freshness["oldest_bar"] if freshness else None,
                "coverage_end": freshness["newest_bar"] if freshness else None,
                "total_bars_cached": freshness["bar_count"] if freshness else 0,
                "gaps_detected": len(freshness["gaps_detected"]["gaps"]) if freshness else 0
            }
        }

    except Exception as e:
        return {
            "symbol": symbol.upper(),
            "interval": interval,
            "lookback_days": lookback_days,
            "bars": [],
            "bar_count": 0,
            "cache_hit": False,
            "error": str(e),
            "message": "查询历史K线失败 - 可能需要回填数据 (QUERY_FAILED)"
        }


def get_latest_price(symbol: str) -> Dict:
    """
    获取标的的最新缓存价格。

    参数:
        symbol: 股票代码（例如 "NVDA"）

    返回:
        包含最新K线和数据新鲜度信息的字典

    示例:
        ```python
        result = get_latest_price("NVDA")

        if result["success"]:
            print(f"NVDA: ${result['price']}")
            print(f"数据年龄: {result['age_seconds']}秒")

            if result["age_seconds"] > 600:  # 10 分钟
                print("⚠️ 数据已过时 - 建议更新")
        ```
    """
    try:
        latest = get_latest_bar(symbol.upper())

        if not latest:
            return {
                "success": False,
                "symbol": symbol.upper(),
                "error": "无可用数据 (NO_DATA)",
                "message": "标的不在缓存中 - 添加到监控列表并回填数据"
            }

        # 计算数据年龄
        bar_time = datetime.fromisoformat(latest.timestamp)
        age_seconds = int((datetime.now() - bar_time).total_seconds())

        return {
            "success": True,
            "symbol": latest.symbol,
            "timestamp": latest.timestamp,
            "price": latest.close,
            "open": latest.open,
            "high": latest.high,
            "low": latest.low,
            "close": latest.close,
            "volume": latest.volume,
            "vwap": latest.vwap,
            "age_seconds": age_seconds,
            "is_stale": age_seconds > 600  # 10 分钟阈值
        }

    except Exception as e:
        return {
            "success": False,
            "symbol": symbol.upper(),
            "error": str(e)
        }


def add_to_watchlist(
    symbol: str,
    priority: int = 0,
    notes: str = ""
) -> Dict:
    """
    将标的添加到活跃监控列表。

    添加后，后台更新程序将为该标的维护最新数据。

    参数:
        symbol: 股票代码（大写）
        priority: 优先级（0-10，数值越高越优先更新）
        notes: 可选的备注/标签，用于组织标的

    返回:
        包含状态和后续步骤的字典

    示例:
        ```python
        # 以高优先级添加 TSLA 到监控列表
        result = add_to_watchlist("TSLA", priority=8, notes="高动量股票")

        if result["success"]:
            print(f"✓ 已将 {result['symbol']} 添加到监控列表")
            print(f"  下一步: 触发历史数据回填")
        ```
    """
    result = _add_to_watchlist(symbol.upper(), priority, notes)

    if result["success"]:
        result["next_steps"] = [
            "1. 标的已添加到监控列表",
            "2. 后台更新程序将每5分钟获取新K线",
            "3. 建议调用 backfill_symbol() 获取历史数据"
        ]

    return result


def remove_from_watchlist(symbol: str) -> Dict:
    """
    从监控列表中移除标的（软删除）。

    停止后台更新但保留缓存数据。

    参数:
        symbol: 股票代码

    返回:
        包含状态的字典

    示例:
        ```python
        result = remove_from_watchlist("GME")

        if result["success"]:
            print(f"✓ 已从活跃监控列表移除 {symbol}")
            print(f"  缓存数据已保留用于查询")
        ```
    """
    return _remove_from_watchlist(symbol.upper())


def get_watchlist() -> Dict:
    """
    获取监控列表中的所有活跃标的及其状态信息。

    返回:
        包含监控列表标的和元数据的字典

    示例:
        ```python
        result = get_watchlist()

        print(f"活跃标的数: {result['total_count']}")
        for symbol_info in result["symbols"]:
            print(f"  {symbol_info['symbol']:6s} (优先级={symbol_info['priority']})")
        ```
    """
    try:
        symbols = get_current_watchlist()

        # 为每个标的添加新鲜度信息
        for symbol_info in symbols:
            freshness = get_freshness_info(symbol_info["symbol"])
            if freshness:
                symbol_info["data_status"] = {
                    "bars_cached": freshness["bar_count"],
                    "newest_bar": freshness["newest_bar"],
                    "freshness_seconds": _calculate_freshness_seconds(freshness)
                }
            else:
                symbol_info["data_status"] = {
                    "bars_cached": 0,
                    "newest_bar": None,
                    "freshness_seconds": None
                }

        return {
            "success": True,
            "symbols": symbols,
            "total_count": len(symbols)
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "symbols": [],
            "total_count": 0
        }


def get_multi_timeframe_data(
    symbol: str,
    intervals: List[str],
    lookback_days: int = 30
) -> Dict:
    """
    在单次调用中获取多个时间周期的历史数据。

    比多次调用 get_historical_bars() 更高效。

    参数:
        symbol: 股票代码
        intervals: 时间周期列表（例如 ["5min", "1h", "daily"]）
        lookback_days: 回溯天数

    返回:
        包含每个时间周期数据的字典

    示例:
        ```python
        # 获取用于技术分析的多时间周期数据
        result = get_multi_timeframe_data(
            symbol="AAPL",
            intervals=["5min", "1h", "daily"],
            lookback_days=30
        )

        if result["success"]:
            print(f"5分钟K线: {result['timeframes']['5min']['bar_count']} 根")
            print(f"1小时K线: {result['timeframes']['1h']['bar_count']} 根")
            print(f"日线K线: {result['timeframes']['daily']['bar_count']} 根")
        ```
    """
    start_time = time.time()

    try:
        timeframes = {}

        for interval in intervals:
            data = get_historical_bars(symbol, interval, lookback_days)
            timeframes[interval] = {
                "bars": data["bars"],
                "bar_count": data["bar_count"],
                "cache_hit": data["cache_hit"]
            }

        query_time_ms = int((time.time() - start_time) * 1000)

        return {
            "success": True,
            "symbol": symbol.upper(),
            "lookback_days": lookback_days,
            "timeframes": timeframes,
            "query_time_ms": query_time_ms
        }

    except Exception as e:
        return {
            "success": False,
            "symbol": symbol.upper(),
            "error": str(e),
            "timeframes": {}
        }


def _calculate_freshness_seconds(freshness_info: Dict) -> Optional[int]:
    """计算最新K线的数据年龄（秒）"""
    if not freshness_info or not freshness_info.get("newest_bar"):
        return None

    newest = datetime.fromisoformat(freshness_info["newest_bar"])
    age = datetime.now() - newest
    return int(age.total_seconds())


# === 技能注册信息 ===
"""
这些函数设计为供 Claude Code 调用：

**历史分析：**
- get_historical_bars(symbol, interval, lookback_days)
- get_multi_timeframe_data(symbol, intervals, lookback_days)

**实时查询：**
- get_latest_price(symbol)
- get_watchlist()

**监控列表管理：**
- add_to_watchlist(symbol, priority, notes)
- remove_from_watchlist(symbol)

**Commander 工作流示例：**

```python
# 检查监控列表状态
watchlist = get_watchlist()
print(f"正在跟踪 {watchlist['total_count']} 个标的")

# 添加新标的用于分析
add_result = add_to_watchlist("MSFT", priority=7, notes="大型科技股")

# 获取用于策略分析的多时间周期数据
mtf_data = get_multi_timeframe_data(
    symbol="AAPL",
    intervals=["5min", "1h", "daily"],
    lookback_days=30
)

# 传递给蜂群进行分析
from skills import consult_swarm
signals = consult_swarm(
    sector="TECH",
    market_data={
        "multi_timeframe": mtf_data,
        "watchlist": watchlist
    }
)
```
"""
