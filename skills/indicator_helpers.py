"""
技术指标辅助函数 - 提供健壮的错误处理和数据验证。

这个模块提供了安全的技术指标调用包装器，确保：
1. 永远不会返回空数组（而是抛出明确的异常）
2. 自动处理NaN值和无效数据
3. 提供清晰的错误消息

用于替代直接调用technical_indicators模块，避免索引越界错误。
"""

import numpy as np
from typing import List, Dict, Optional, Tuple
from . import technical_indicators as ti


class InsufficientDataError(ValueError):
    """数据不足以计算指标"""
    pass


class InvalidDataError(ValueError):
    """数据无效（全是NaN或空）"""
    pass


def safe_calculate_sma(
    bars: List[Dict],
    period: int,
    field: str = 'close',
    return_latest: bool = True
) -> float:
    """
    安全地计算SMA，保证返回有效值或抛出明确异常。

    Args:
        bars: OHLCV K线数据列表
        period: 平均周期数
        field: 使用的价格字段（默认: 'close'）
        return_latest: 是否只返回最新值（默认True）

    Returns:
        float: 最新的SMA值（如果return_latest=True）

    Raises:
        InsufficientDataError: 数据不足（bars数量 < period）
        InvalidDataError: 数据无效（全是NaN或无法提取）

    Example:
        ```python
        from skills.indicator_helpers import safe_calculate_sma

        try:
            sma_20 = safe_calculate_sma(bars, period=20)
            print(f"SMA(20): ${sma_20:.2f}")
        except InsufficientDataError:
            print("数据不足，需要至少20根K线")
        except InvalidDataError:
            print("数据无效，无法计算SMA")
        ```
    """
    if not bars:
        raise InsufficientDataError(f"bars为空，无法计算SMA({period})")

    if len(bars) < period:
        raise InsufficientDataError(
            f"SMA({period})数据不足: 需要{period}根K线，实际{len(bars)}根"
        )

    # 调用原始函数
    result = ti.calculate_sma(bars, period, field)

    if len(result) == 0:
        raise InvalidDataError(f"无法从字段'{field}'提取有效数据")

    # 检查是否有有效值
    valid_values = result[~np.isnan(result)]
    if len(valid_values) == 0:
        raise InvalidDataError(f"SMA({period})计算结果全为NaN")

    if return_latest:
        # 返回最后一个有效值
        return float(valid_values[-1])
    else:
        # 返回整个数组
        return result


def safe_calculate_rsi(
    bars: List[Dict],
    period: int = 14,
    field: str = 'close',
    return_latest: bool = True
) -> float:
    """
    安全地计算RSI，保证返回有效值或抛出明确异常。

    Args:
        bars: OHLCV K线数据列表
        period: RSI周期（默认14）
        field: 使用的价格字段（默认: 'close'）
        return_latest: 是否只返回最新值（默认True）

    Returns:
        float: 最新的RSI值（0-100）

    Raises:
        InsufficientDataError: 数据不足
        InvalidDataError: 数据无效

    Example:
        ```python
        try:
            rsi_14 = safe_calculate_rsi(bars, period=14)
            print(f"RSI(14): {rsi_14:.2f}")

            if rsi_14 > 70:
                print("超买区域")
            elif rsi_14 < 30:
                print("超卖区域")
        except InsufficientDataError:
            print("数据不足，需要至少14根K线")
        ```
    """
    if not bars:
        raise InsufficientDataError(f"bars为空，无法计算RSI({period})")

    if len(bars) < period + 1:  # RSI需要period+1根K线
        raise InsufficientDataError(
            f"RSI({period})数据不足: 需要{period + 1}根K线，实际{len(bars)}根"
        )

    result = ti.calculate_rsi(bars, period, field)

    if len(result) == 0:
        raise InvalidDataError(f"无法从字段'{field}'提取有效数据")

    valid_values = result[~np.isnan(result)]
    if len(valid_values) == 0:
        raise InvalidDataError(f"RSI({period})计算结果全为NaN")

    if return_latest:
        return float(valid_values[-1])
    else:
        return result


def safe_calculate_macd(
    bars: List[Dict],
    fast_period: int = 12,
    slow_period: int = 26,
    signal_period: int = 9,
    field: str = 'close'
) -> Dict[str, float]:
    """
    安全地计算MACD，返回最新的MACD值、信号线和直方图。

    Args:
        bars: OHLCV K线数据列表
        fast_period: 快速EMA周期（默认12）
        slow_period: 慢速EMA周期（默认26）
        signal_period: 信号线周期（默认9）
        field: 使用的价格字段（默认: 'close'）

    Returns:
        Dict: {
            'macd': float,           # MACD值
            'signal': float,         # 信号线值
            'histogram': float       # MACD柱状图（macd - signal）
        }

    Raises:
        InsufficientDataError: 数据不足
        InvalidDataError: 数据无效

    Example:
        ```python
        try:
            macd_data = safe_calculate_macd(bars)
            print(f"MACD: {macd_data['macd']:.2f}")
            print(f"Signal: {macd_data['signal']:.2f}")
            print(f"Histogram: {macd_data['histogram']:.2f}")

            if macd_data['histogram'] > 0:
                print("MACD金叉")
            else:
                print("MACD死叉")
        except InsufficientDataError:
            print("数据不足，需要至少26根K线")
        ```
    """
    min_required = slow_period + signal_period

    if not bars:
        raise InsufficientDataError(f"bars为空，无法计算MACD")

    if len(bars) < min_required:
        raise InsufficientDataError(
            f"MACD数据不足: 需要{min_required}根K线，实际{len(bars)}根"
        )

    result = ti.calculate_macd(bars, fast_period, slow_period, signal_period, field)

    if not result or 'macd' not in result:
        raise InvalidDataError(f"MACD计算失败")

    # 检查每个值
    for key in ['macd', 'signal', 'histogram']:
        values = result[key]
        if len(values) == 0:
            raise InvalidDataError(f"MACD计算结果为空（{key}）")

        valid_values = values[~np.isnan(values)]
        if len(valid_values) == 0:
            raise InvalidDataError(f"MACD计算结果全为NaN（{key}）")

    # 返回最新值
    return {
        'macd': float(result['macd'][~np.isnan(result['macd'])][-1]),
        'signal': float(result['signal'][~np.isnan(result['signal'])][-1]),
        'histogram': float(result['histogram'][~np.isnan(result['histogram'])][-1])
    }


def safe_calculate_historical_volatility(
    bars: List[Dict],
    window: int = 20,
    field: str = 'close'
) -> float:
    """
    安全地计算历史波动率（年化）。

    Args:
        bars: OHLCV K线数据列表
        window: 回溯窗口（默认20）
        field: 使用的价格字段（默认: 'close'）

    Returns:
        float: 年化历史波动率（例如：0.25 = 25%）

    Raises:
        InsufficientDataError: 数据不足
        InvalidDataError: 数据无效

    Example:
        ```python
        try:
            vol_20 = safe_calculate_historical_volatility(bars, window=20)
            print(f"20日历史波动率: {vol_20:.2%}")

            if vol_20 > 0.30:
                print("高波动环境")
        except InsufficientDataError:
            print("数据不足，需要至少21根K线")
        ```
    """
    # 提取收盘价
    if not bars:
        raise InsufficientDataError("bars为空，无法计算历史波动率")

    if len(bars) < window + 1:
        raise InsufficientDataError(
            f"历史波动率数据不足: 需要{window + 1}根K线，实际{len(bars)}根"
        )

    closes = ti._extract_prices(bars, field)

    if len(closes) == 0:
        raise InvalidDataError(f"无法从字段'{field}'提取有效数据")

    # 使用最后window+1个数据点
    recent_closes = closes[-(window + 1):]

    result = ti.calculate_historical_volatility(recent_closes)

    if np.isnan(result) or np.isinf(result):
        raise InvalidDataError("历史波动率计算结果无效（NaN或Inf）")

    return float(result)


def safe_detect_trend(
    bars: List[Dict],
    lookback_days: int = 30
) -> str:
    """
    安全地检测趋势。

    Args:
        bars: OHLCV K线数据列表
        lookback_days: 回溯天数（默认30）

    Returns:
        str: "UPTREND", "DOWNTREND", 或 "SIDEWAYS"

    Raises:
        InsufficientDataError: 数据不足
        InvalidDataError: 数据无效

    Example:
        ```python
        try:
            trend = safe_detect_trend(bars, lookback_days=30)
            print(f"市场趋势: {trend}")

            if trend == "UPTREND":
                print("上升趋势，考虑看涨策略")
            elif trend == "DOWNTREND":
                print("下降趋势，考虑看跌策略")
        except InsufficientDataError:
            print("数据不足，需要至少30根K线")
        ```
    """
    if not bars:
        raise InsufficientDataError("bars为空，无法检测趋势")

    if len(bars) < lookback_days:
        raise InsufficientDataError(
            f"趋势检测数据不足: 需要{lookback_days}根K线，实际{len(bars)}根"
        )

    # 使用最后lookback_days个K线
    recent_bars = bars[-lookback_days:]

    result = ti.detect_trend(recent_bars)

    if not result or result not in ["UPTREND", "DOWNTREND", "SIDEWAYS"]:
        raise InvalidDataError(f"趋势检测结果无效: {result}")

    return result


# ==================== 批量安全计算 ====================

def calculate_all_indicators_safe(
    bars: List[Dict],
    field: str = 'close'
) -> Dict[str, any]:
    """
    安全地计算所有常用技术指标。

    对每个指标进行try-except包装，失败的指标返回None，
    而不是导致整个计算失败。

    Args:
        bars: OHLCV K线数据列表
        field: 使用的价格字段（默认: 'close'）

    Returns:
        Dict: {
            'sma_20': float or None,
            'sma_50': float or None,
            'rsi_14': float or None,
            'macd': Dict or None,
            'volatility_20': float or None,
            'trend': str or None,
            'errors': List[str]  # 错误消息列表
        }

    Example:
        ```python
        from skills.indicator_helpers import calculate_all_indicators_safe

        indicators = calculate_all_indicators_safe(bars)

        if indicators['sma_20'] is not None:
            print(f"SMA(20): ${indicators['sma_20']:.2f}")

        if indicators['rsi_14'] is not None:
            print(f"RSI(14): {indicators['rsi_14']:.2f}")

        if indicators['errors']:
            print(f"计算失败的指标: {len(indicators['errors'])}")
            for error in indicators['errors']:
                print(f"  • {error}")
        ```
    """
    result = {
        'sma_20': None,
        'sma_50': None,
        'rsi_14': None,
        'macd': None,
        'volatility_20': None,
        'trend': None,
        'errors': []
    }

    # SMA(20)
    try:
        result['sma_20'] = safe_calculate_sma(bars, period=20, field=field)
    except (InsufficientDataError, InvalidDataError) as e:
        result['errors'].append(f"SMA(20): {str(e)}")

    # SMA(50)
    try:
        result['sma_50'] = safe_calculate_sma(bars, period=50, field=field)
    except (InsufficientDataError, InvalidDataError) as e:
        result['errors'].append(f"SMA(50): {str(e)}")

    # RSI(14)
    try:
        result['rsi_14'] = safe_calculate_rsi(bars, period=14, field=field)
    except (InsufficientDataError, InvalidDataError) as e:
        result['errors'].append(f"RSI(14): {str(e)}")

    # MACD
    try:
        result['macd'] = safe_calculate_macd(bars, field=field)
    except (InsufficientDataError, InvalidDataError) as e:
        result['errors'].append(f"MACD: {str(e)}")

    # 历史波动率(20)
    try:
        result['volatility_20'] = safe_calculate_historical_volatility(bars, window=20, field=field)
    except (InsufficientDataError, InvalidDataError) as e:
        result['errors'].append(f"Volatility(20): {str(e)}")

    # 趋势检测
    try:
        result['trend'] = safe_detect_trend(bars, lookback_days=30)
    except (InsufficientDataError, InvalidDataError) as e:
        result['errors'].append(f"Trend: {str(e)}")

    return result
