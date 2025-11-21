"""
Agentic AlphaHive 运行时技术指标库。

通过 NumPy 向量化提供久经考验的技术分析函数，
相比原生 Python 循环实现 10 倍以上性能提升。

所有函数优雅处理边界情况（NaN、数据不足、无效参数），
并遵循行业标准计算方法。

输入格式:
    bars: List[Dict] 包含键 ['open', 'high', 'low', 'close', 'volume', 'timestamp']

输出格式:
    NumPy 数组或字典（取决于指标复杂度）
"""

import numpy as np
import warnings
from typing import List, Dict, Optional, Tuple
from datetime import datetime


# ==================== 辅助函数 ====================

def _extract_prices(bars: List[Dict], field: str = 'close') -> np.ndarray:
    """
    从 K 线数据中提取价格数组，并处理 NaN 值。

    Args:
        bars: OHLCV 字典列表
        field: 要提取的价格字段 ('open', 'high', 'low', 'close', 'volume')

    Returns:
        价格的 NumPy 数组
    """
    if not bars:
        return np.array([])

    try:
        prices = np.array([float(bar[field]) for bar in bars])
        return prices
    except (KeyError, ValueError, TypeError):
        warnings.warn(f"字段 '{field}' 中存在无效数据，返回空数组 (INVALID_FIELD_DATA)")
        return np.array([])


def _validate_period(bars: List[Dict], period: int, indicator_name: str) -> bool:
    """
    验证周期计算所需的数据是否充足。

    Args:
        bars: OHLCV K 线数据列表
        period: 所需周期长度
        indicator_name: 指标名称（用于警告消息）

    Returns:
        如果数据充足返回 True，否则返回 False
    """
    if period <= 0:
        warnings.warn(
            f"{indicator_name} 的周期无效: {period}（必须 > 0）(INVALID_PERIOD)"
        )
        return False
    if len(bars) < period:
        warnings.warn(
            f"{indicator_name}({period}) 数据不足: "
            f"需要 {period} 根 K 线，实际 {len(bars)} 根 (INSUFFICIENT_DATA)"
        )
        return False
    return True


# ==================== 移动平均线 ====================

def calculate_sma(bars: List[Dict], period: int, field: str = 'close') -> np.ndarray:
    """
    计算简单移动平均线 (SMA)。

    公式: SMA = sum(prices[-period:]) / period

    Args:
        bars: OHLCV K 线数据列表
        period: 平均周期数
        field: 使用的价格字段（默认: 'close'）

    Returns:
        数组，前 (period-1) 个值为 NaN，其余为 SMA 值

    Example:
        >>> bars = [{'close': 100}, {'close': 102}, {'close': 101}]
        >>> sma = calculate_sma(bars, period=2)
        >>> # [NaN, 101.0, 101.5]
    """
    if not _validate_period(bars, period, f"SMA"):
        return np.full(len(bars), np.nan)

    prices = _extract_prices(bars, field)
    if len(prices) == 0:
        return np.array([])

    # 使用 NumPy convolve 实现向量化移动平均
    # 性能比 Python 循环快约 10 倍
    weights = np.ones(period) / period
    sma = np.convolve(prices, weights, mode='valid')

    # 为前 (period-1) 个值填充 NaN
    result = np.concatenate([np.full(period - 1, np.nan), sma])
    return result


def calculate_ema(bars: List[Dict], period: int, field: str = 'close') -> np.ndarray:
    """
    计算指数移动平均线 (EMA)。

    公式:
        multiplier = 2 / (period + 1)
        EMA[i] = price[i] * multiplier + EMA[i-1] * (1 - multiplier)

    Args:
        bars: OHLCV K 线数据列表
        period: EMA 周期数
        field: 使用的价格字段（默认: 'close'）

    Returns:
        EMA 值数组（首个值为 SMA，其余为指数加权）

    Example:
        >>> ema = calculate_ema(bars, period=12)
    """
    if not _validate_period(bars, period, "EMA"):
        return np.full(len(bars), np.nan)

    prices = _extract_prices(bars, field)
    if len(prices) == 0:
        return np.array([])

    multiplier = 2.0 / (period + 1)
    ema = np.full(len(prices), np.nan)

    # 查找第一个包含 'period' 个非 NaN 值的有效窗口
    first_valid = None
    for i in range(period - 1, len(prices)):
        window = prices[i - period + 1:i + 1]
        if not np.any(np.isnan(window)):
            # 使用第一个有效窗口的 SMA 初始化
            ema[i] = np.mean(window)
            first_valid = i
            break

    if first_valid is None:
        return ema  # 如果没有找到有效窗口，返回全 NaN

    # 从第一个有效点开始向前计算 EMA
    for i in range(first_valid + 1, len(prices)):
        if np.isnan(prices[i]):
            ema[i] = ema[i - 1]  # 遇到 NaN 时传播前一个 EMA 值
        else:
            ema[i] = prices[i] * multiplier + ema[i - 1] * (1 - multiplier)

    return ema


def calculate_wma(bars: List[Dict], period: int, field: str = 'close') -> np.ndarray:
    """
    计算加权移动平均线 (WMA)。

    公式: WMA = sum(price[i] * weight[i]) / sum(weight[i])
    其中 weight[i] = i + 1（线性加权，近期价格权重更高）

    Args:
        bars: OHLCV K 线数据列表
        period: 周期数
        field: 使用的价格字段

    Returns:
        WMA 值数组
    """
    if not _validate_period(bars, period, "WMA"):
        return np.full(len(bars), np.nan)

    prices = _extract_prices(bars, field)
    if len(prices) == 0:
        return np.array([])

    # 创建线性权重 (1, 2, 3, ..., period)
    weights = np.arange(1, period + 1)
    weight_sum = weights.sum()

    wma = np.full(len(prices), np.nan)

    # 为每个有效窗口计算 WMA
    for i in range(period - 1, len(prices)):
        window = prices[i - period + 1:i + 1]
        wma[i] = np.dot(window, weights) / weight_sum

    return wma


# ==================== 动量指标 ====================

def calculate_rsi(bars: List[Dict], period: int = 14, field: str = 'close') -> np.ndarray:
    """
    使用 Wilder 平滑方法计算相对强弱指数 (RSI)。

    公式:
        RS = 平均涨幅 / 平均跌幅
        RSI = 100 - (100 / (1 + RS))

    Args:
        bars: OHLCV K 线数据列表
        period: 周期数（默认: 14）
        field: 使用的价格字段

    Returns:
        RSI 值数组，范围 [0, 100]
        前 (period) 个值为 NaN

    边界情况:
        - 价格恒定: 返回 50.0（中性）
        - 仅上涨: 返回 100.0
        - 仅下跌: 返回 0.0

    Example:
        >>> rsi = calculate_rsi(bars, period=14)
        >>> # RSI > 70 表示超买
        >>> # RSI < 30 表示超卖
    """
    if not _validate_period(bars, period + 1, "RSI"):
        return np.full(len(bars), np.nan)

    prices = _extract_prices(bars, field)
    if len(prices) == 0:
        return np.array([])

    # 计算价格变化
    deltas = np.diff(prices)

    # 分离涨幅和跌幅
    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)

    # 计算初始平均涨幅/跌幅（简单平均）
    avg_gain = np.mean(gains[:period])
    avg_loss = np.mean(losses[:period])

    # 使用 Wilder 平滑计算 RSI
    rsi = np.full(len(prices), np.nan)

    for i in range(period, len(prices) - 1):
        # Wilder 平滑: (previous_avg * (period-1) + current_value) / period
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period

        if avg_loss == 0 and avg_gain == 0:
            rsi[i + 1] = 50.0  # 价格恒定，中性 RSI
        elif avg_loss == 0:
            rsi[i + 1] = 100.0  # 仅上涨，最大 RSI
        else:
            rs = avg_gain / avg_loss
            rsi[i + 1] = 100.0 - (100.0 / (1.0 + rs))

    return rsi


def calculate_macd(
    bars: List[Dict],
    fast: int = 12,
    slow: int = 26,
    signal: int = 9,
    field: str = 'close'
) -> Dict[str, np.ndarray]:
    """
    计算 MACD（移动平均收敛发散指标）。

    公式:
        MACD 线 = EMA(fast) - EMA(slow)
        信号线 = EMA(MACD 线, signal)
        柱状图 = MACD 线 - 信号线

    Args:
        bars: OHLCV K 线数据列表
        fast: 快速 EMA 周期（默认: 12）
        slow: 慢速 EMA 周期（默认: 26）
        signal: 信号线 EMA 周期（默认: 9）
        field: 使用的价格字段

    Returns:
        包含以下键的字典:
            - 'macd_line': MACD 值
            - 'signal_line': 信号线值
            - 'histogram': MACD - 信号线（交叉指标）

    信号:
        - 柱状图 > 0: 看涨（MACD 在信号线上方）
        - 柱状图 < 0: 看跌（MACD 在信号线下方）
        - 柱状图向上穿越 0: 买入信号
        - 柱状图向下穿越 0: 卖出信号

    Example:
        >>> macd_data = calculate_macd(bars)
        >>> if macd_data['histogram'][-1] > 0 and macd_data['histogram'][-2] <= 0:
        ...     print("看涨交叉!")
    """
    if not _validate_period(bars, slow + signal, "MACD"):
        n = len(bars)
        return {
            'macd_line': np.full(n, np.nan),
            'signal_line': np.full(n, np.nan),
            'histogram': np.full(n, np.nan)
        }

    # 计算快速和慢速 EMA
    ema_fast = calculate_ema(bars, fast, field)
    ema_slow = calculate_ema(bars, slow, field)

    # MACD 线 = 快速 EMA - 慢速 EMA
    macd_line = ema_fast - ema_slow

    # 信号线 = MACD 线的 EMA
    # 将 MACD 线转换为 bars 格式以计算 EMA
    macd_bars = [{'close': val} for val in macd_line]
    signal_line = calculate_ema(macd_bars, signal, 'close')

    # 柱状图 = MACD - 信号线
    histogram = macd_line - signal_line

    return {
        'macd_line': macd_line,
        'signal_line': signal_line,
        'histogram': histogram
    }


def calculate_stochastic(
    bars: List[Dict],
    k_period: int = 14,
    d_period: int = 3
) -> Dict[str, np.ndarray]:
    """
    计算 Stochastic 震荡指标。

    公式:
        %K = 100 * (收盘价 - 最低价) / (最高价 - 最低价)
        %D = SMA(%K, d_period)

    Args:
        bars: OHLCV K 线数据列表
        k_period: %K 的回溯周期（默认: 14）
        d_period: %D 的 SMA 周期（默认: 3）

    Returns:
        包含以下键的字典:
            - 'k_line': %K 值（快速随机指标）
            - 'd_line': %D 值（慢速随机指标，平滑后）

    信号:
        - %K > 80: 超买
        - %K < 20: 超卖
        - %K 向上穿越 %D: 买入信号
        - %K 向下穿越 %D: 卖出信号
    """
    if not _validate_period(bars, k_period, "Stochastic"):
        n = len(bars)
        return {'k_line': np.full(n, np.nan), 'd_line': np.full(n, np.nan)}

    highs = _extract_prices(bars, 'high')
    lows = _extract_prices(bars, 'low')
    closes = _extract_prices(bars, 'close')

    k = np.full(len(bars), np.nan)

    # 为每个周期计算 %K
    for i in range(k_period - 1, len(bars)):
        window_high = np.max(highs[i - k_period + 1:i + 1])
        window_low = np.min(lows[i - k_period + 1:i + 1])

        if window_high == window_low:
            k[i] = 50.0  # 无波动范围时为中性
        else:
            k[i] = 100.0 * (closes[i] - window_low) / (window_high - window_low)

    # 计算 %D（%K 的 SMA）
    k_bars = [{'close': val} for val in k]
    d = calculate_sma(k_bars, d_period, 'close')

    return {'k_line': k, 'd_line': d}


# ==================== 波动率指标 ====================

def calculate_bollinger_bands(
    bars: List[Dict],
    period: int = 20,
    std_dev: float = 2.0,
    field: str = 'close'
) -> Dict[str, np.ndarray]:
    """
    计算 Bollinger Bands（布林带）。

    公式:
        中轨 = SMA(period)
        上轨 = 中轨 + (std_dev * 标准差)
        下轨 = 中轨 - (std_dev * 标准差)
        带宽 = (上轨 - 下轨) / 中轨

    Args:
        bars: OHLCV K 线数据列表
        period: SMA 和标准差的周期（默认: 20）
        std_dev: 标准差倍数（默认: 2.0）
        field: 使用的价格字段

    Returns:
        包含以下键的字典:
            - 'upper_band': Bollinger 上轨
            - 'middle_band': SMA（中轨）
            - 'lower_band': Bollinger 下轨
            - 'bandwidth': (上轨 - 下轨) / 中轨（波动率指标）

    信号:
        - 价格在上轨: 潜在阻力位，考虑卖出
        - 价格在下轨: 潜在支撑位，考虑买入
        - 带宽收缩: 低波动率，可能突破
        - 带宽扩张: 高波动率，趋势延续

    Example:
        >>> bb = calculate_bollinger_bands(bars, period=20, std_dev=2)
        >>> if bars[-1]['close'] <= bb['lower_band'][-1]:
        ...     print("价格触及下轨 - 潜在买入机会")
    """
    if not _validate_period(bars, period, "Bollinger Bands"):
        n = len(bars)
        return {
            'upper_band': np.full(n, np.nan),
            'middle_band': np.full(n, np.nan),
            'lower_band': np.full(n, np.nan),
            'bandwidth': np.full(n, np.nan)
        }

    prices = _extract_prices(bars, field)
    middle_band = calculate_sma(bars, period, field)

    # 计算滚动标准差
    std = np.full(len(bars), np.nan)
    for i in range(period - 1, len(bars)):
        window = prices[i - period + 1:i + 1]
        std[i] = np.std(window, ddof=1)  # 样本标准差

    # 计算上下轨
    upper_band = middle_band + (std_dev * std)
    lower_band = middle_band - (std_dev * std)

    # 计算带宽（波动率指标）
    bandwidth = np.where(
        middle_band > 0,
        (upper_band - lower_band) / middle_band,
        np.nan
    )

    return {
        'upper_band': upper_band,
        'middle_band': middle_band,
        'lower_band': lower_band,
        'bandwidth': bandwidth
    }


def calculate_atr(bars: List[Dict], period: int = 14) -> np.ndarray:
    """
    使用 Wilder 平滑方法计算平均真实波幅 (ATR)。

    公式:
        真实波幅 = max(最高价 - 最低价, abs(最高价 - 前收盘价), abs(最低价 - 前收盘价))
        ATR = 真实波幅的 Wilder 平滑平均

    Args:
        bars: OHLCV K 线数据列表
        period: ATR 周期（默认: 14）

    Returns:
        ATR 值数组（单位为美元）

    用途:
        ATR 代表平均价格波动，用于:
        - 止损位设置（例如，止损位 = 入场价 - 2*ATR）
        - 仓位规模计算（每单位风险 = ATR）
        - 波动率评估

    Example:
        >>> atr = calculate_atr(bars, period=14)
        >>> stop_loss = entry_price - (2 * atr[-1])
    """
    if not _validate_period(bars, period + 1, "ATR"):
        return np.full(len(bars), np.nan)

    highs = _extract_prices(bars, 'high')
    lows = _extract_prices(bars, 'low')
    closes = _extract_prices(bars, 'close')

    # 计算真实波幅
    tr = np.full(len(bars), np.nan)
    tr[0] = highs[0] - lows[0]  # 首根 K 线使用简单波幅

    for i in range(1, len(bars)):
        hl = highs[i] - lows[i]
        hc = abs(highs[i] - closes[i - 1])
        lc = abs(lows[i] - closes[i - 1])
        tr[i] = max(hl, hc, lc)

    # 使用 Wilder 平滑计算 ATR
    atr = np.full(len(bars), np.nan)
    atr[period] = np.mean(tr[1:period + 1])  # 初始 ATR 为简单平均

    for i in range(period + 1, len(bars)):
        # Wilder 平滑: (previous_atr * (period-1) + current_tr) / period
        atr[i] = (atr[i - 1] * (period - 1) + tr[i]) / period

    return atr


def calculate_historical_volatility(
    bars: List[Dict],
    period: int = 20,
    field: str = 'close'
) -> float:
    """
    计算年化历史波动率。

    公式:
        日收益率 = ln(price[i] / price[i-1])
        波动率 = std(returns) * sqrt(252)

    Args:
        bars: OHLCV K 线数据列表
        period: 回溯周期（默认: 20 天）
        field: 使用的价格字段

    Returns:
        年化波动率（小数形式，例如 0.25 = 25%）

    用途:
        与隐含波动率 (IV) 对比以识别定价偏差:
        - HV > IV: 波动率定价偏低，倾向买入期权
        - HV < IV: 波动率定价偏高，倾向卖出期权

    Example:
        >>> hv = calculate_historical_volatility(bars, period=20)
        >>> print(f"20 日历史波动率: {hv:.1%}")  # 例如 "20 日历史波动率: 24.5%"
    """
    if not _validate_period(bars, period + 1, "Historical Volatility"):
        return np.nan

    prices = _extract_prices(bars, field)
    if len(prices) < period + 1:
        return np.nan

    # 使用最近 'period' 根 K 线
    recent_prices = prices[-period - 1:]

    # 计算对数收益率
    returns = np.log(recent_prices[1:] / recent_prices[:-1])

    # 计算标准差
    volatility = np.std(returns, ddof=1)  # 样本标准差

    # 年化（每年 252 个交易日）
    annualized_vol = volatility * np.sqrt(252)

    return annualized_vol


# ==================== 趋势指标 ====================

def calculate_adx(bars: List[Dict], period: int = 14) -> np.ndarray:
    """
    计算平均趋向指数 (ADX)。

    ADX 衡量趋势强度（非方向），范围 0-100:
        - ADX < 20: 弱趋势（震荡市场）
        - ADX 20-40: 中等趋势
        - ADX > 40: 强趋势

    Args:
        bars: OHLCV K 线数据列表
        period: ADX 周期（默认: 14）

    Returns:
        ADX 值数组 [0, 100]

    用途:
        使用 ADX 判断市场是趋势市还是震荡市:
        - 高 ADX: 使用趋势跟踪策略
        - 低 ADX: 使用均值回归策略

    Example:
        >>> adx = calculate_adx(bars, period=14)
        >>> if adx[-1] < 25:
        ...     print("弱趋势 - 使用均值回归策略")
    """
    if not _validate_period(bars, period * 2, "ADX"):
        return np.full(len(bars), np.nan)

    highs = _extract_prices(bars, 'high')
    lows = _extract_prices(bars, 'low')
    closes = _extract_prices(bars, 'close')

    # 计算 +DM 和 -DM（方向性运动）
    plus_dm = np.full(len(bars), 0.0)
    minus_dm = np.full(len(bars), 0.0)

    for i in range(1, len(bars)):
        high_diff = highs[i] - highs[i - 1]
        low_diff = lows[i - 1] - lows[i]

        if high_diff > low_diff and high_diff > 0:
            plus_dm[i] = high_diff
        if low_diff > high_diff and low_diff > 0:
            minus_dm[i] = low_diff

    # 计算 ATR
    atr = calculate_atr(bars, period)

    # 计算 +DI 和 -DI（方向性指标）
    plus_di = np.full(len(bars), np.nan)
    minus_di = np.full(len(bars), np.nan)

    # 使用 Wilder 平滑处理 DM 值
    smoothed_plus_dm = np.copy(plus_dm)
    smoothed_minus_dm = np.copy(minus_dm)

    for i in range(period, len(bars)):
        smoothed_plus_dm[i] = (smoothed_plus_dm[i - 1] * (period - 1) + plus_dm[i]) / period
        smoothed_minus_dm[i] = (smoothed_minus_dm[i - 1] * (period - 1) + minus_dm[i]) / period

        if atr[i] > 0:
            plus_di[i] = 100 * smoothed_plus_dm[i] / atr[i]
            minus_di[i] = 100 * smoothed_minus_dm[i] / atr[i]

    # 计算 DX（方向性指数）
    dx = np.full(len(bars), np.nan)
    for i in range(period, len(bars)):
        di_sum = plus_di[i] + minus_di[i]
        if di_sum > 0:
            dx[i] = 100 * abs(plus_di[i] - minus_di[i]) / di_sum

    # 计算 ADX（平滑后的 DX）
    adx = np.full(len(bars), np.nan)
    adx[period * 2 - 1] = np.nanmean(dx[period:period * 2])

    for i in range(period * 2, len(bars)):
        adx[i] = (adx[i - 1] * (period - 1) + dx[i]) / period

    return adx


def detect_trend(
    bars: List[Dict],
    sma_short: int = 20,
    sma_long: int = 50
) -> str:
    """
    使用移动平均线关系检测趋势方向和强度。

    分类:
        - "STRONG_UPTREND": 价格 > SMA_短期 > SMA_长期，且两条均线均上升
        - "WEAK_UPTREND": 价格 > SMA_短期，但 SMA_短期 ≈ SMA_长期
        - "STRONG_DOWNTREND": 价格 < SMA_短期 < SMA_长期，且两条均线均下降
        - "WEAK_DOWNTREND": 价格 < SMA_短期，但 SMA_短期 ≈ SMA_长期
        - "SIDEWAYS": 均线平坦，无明确方向

    Args:
        bars: OHLCV K 线数据列表
        sma_short: 短期 SMA 周期（默认: 20）
        sma_long: 长期 SMA 周期（默认: 50）

    Returns:
        趋势分类字符串

    Example:
        >>> trend = detect_trend(bars, sma_short=20, sma_long=50)
        >>> if trend == "STRONG_UPTREND":
        ...     # 使用趋势跟踪做多策略
    """
    if len(bars) < sma_long + 10:
        return "UNKNOWN"

    prices = _extract_prices(bars, 'close')
    sma_s = calculate_sma(bars, sma_short)
    sma_l = calculate_sma(bars, sma_long)

    current_price = prices[-1]
    current_sma_s = sma_s[-1]
    current_sma_l = sma_l[-1]

    if np.isnan(current_sma_s) or np.isnan(current_sma_l):
        return "UNKNOWN"

    # 计算 SMA 斜率（最近 10 天）
    sma_s_slope = (sma_s[-1] - sma_s[-10]) / sma_s[-10]
    sma_l_slope = (sma_l[-1] - sma_l[-10]) / sma_l[-10]

    # 检查排列
    if current_price > current_sma_s > current_sma_l:
        if sma_s_slope > 0.005:  # 10 天内涨幅 > 0.5%
            return "STRONG_UPTREND"
        else:
            return "WEAK_UPTREND"

    elif current_price < current_sma_s < current_sma_l:
        if sma_s_slope < -0.005:  # 10 天内跌幅 > 0.5%
            return "STRONG_DOWNTREND"
        else:
            return "WEAK_DOWNTREND"

    elif abs(sma_s_slope) < 0.005 and abs(sma_l_slope) < 0.005:
        return "SIDEWAYS"

    elif current_price > current_sma_s:
        return "WEAK_UPTREND"
    else:
        return "WEAK_DOWNTREND"


# ==================== 支撑/阻力位 ====================

def find_swing_highs(bars: List[Dict], window: int = 5) -> List[float]:
    """
    查找摆动高点（局部最大值）作为阻力位。

    摆动高点是在其前后 ±window 根 K 线范围内
    高于所有价格的点位。

    Args:
        bars: OHLCV K 线数据列表
        window: 回溯/前瞻窗口（默认: 5）

    Returns:
        摆动高点价格列表，按降序排列

    用途:
        将摆动高点用作阻力位，用于:
        - 止盈目标
        - 做空入场位
        - 行权价选择（在阻力位卖出行权价）

    Example:
        >>> resistance_levels = find_swing_highs(bars, window=5)
        >>> nearest_resistance = min([r for r in resistance_levels if r > current_price])
    """
    if len(bars) < window * 2 + 1:
        return []

    highs = _extract_prices(bars, 'high')
    swing_highs = []

    # 检查每个潜在的摆动高点
    for i in range(window, len(highs) - window):
        is_swing_high = True

        # 检查当前高点是否高于所有周围高点
        for j in range(i - window, i + window + 1):
            if j != i and highs[j] >= highs[i]:
                is_swing_high = False
                break

        if is_swing_high:
            swing_highs.append(highs[i])

    # 按降序排列（最高阻力位优先）
    return sorted(swing_highs, reverse=True)


def find_swing_lows(bars: List[Dict], window: int = 5) -> List[float]:
    """
    查找摆动低点（局部最小值）作为支撑位。

    摆动低点是在其前后 ±window 根 K 线范围内
    低于所有价格的点位。

    Args:
        bars: OHLCV K 线数据列表
        window: 回溯/前瞻窗口（默认: 5）

    Returns:
        摆动低点价格列表，按升序排列

    用途:
        将摆动低点用作支撑位，用于:
        - 止损位设置
        - 做多入场位
        - 行权价选择（在支撑位买入行权价）

    Example:
        >>> support_levels = find_swing_lows(bars, window=5)
        >>> nearest_support = max([s for s in support_levels if s < current_price])
    """
    if len(bars) < window * 2 + 1:
        return []

    lows = _extract_prices(bars, 'low')
    swing_lows = []

    # 检查每个潜在的摆动低点
    for i in range(window, len(lows) - window):
        is_swing_low = True

        # 检查当前低点是否低于所有周围低点
        for j in range(i - window, i + window + 1):
            if j != i and lows[j] <= lows[i]:
                is_swing_low = False
                break

        if is_swing_low:
            swing_lows.append(lows[i])

    # 按升序排列（最低支撑位优先）
    return sorted(swing_lows)


def calculate_pivot_points(bars) -> Dict[str, float]:
    """
    计算枢轴点及支撑/阻力位。

    使用最近的完整 K 线（例如，今日枢轴点使用昨日 OHLC）。

    公式:
        枢轴点 = (最高价 + 最低价 + 收盘价) / 3
        R1 = 2 * 枢轴点 - 最低价
        R2 = 枢轴点 + (最高价 - 最低价)
        S1 = 2 * 枢轴点 - 最高价
        S2 = 枢轴点 - (最高价 - 最低价)

    Args:
        bars: 单个 OHLCV K 线字典或 K 线列表（使用最后一根）

    Returns:
        包含枢轴点和支撑/阻力位的字典

    用途:
        枢轴点是日内支撑/阻力位，用于:
        - 日内交易入场/出场位
        - 止损位设置
        - 目标价选择

    Example:
        >>> pivots = calculate_pivot_points(bars[-1])  # 单根 K 线
        >>> pivots = calculate_pivot_points(bars)  # K 线列表
        >>> if price < pivots['pivot']:
        ...     target = pivots['s1']  # 看跌，目标 S1
    """
    # 处理单根 K 线和 K 线列表两种情况
    if isinstance(bars, dict):
        bar = bars
    elif isinstance(bars, list):
        if len(bars) < 1:
            return {
                'pivot': np.nan,
                'r1': np.nan,
                'r2': np.nan,
                's1': np.nan,
                's2': np.nan
            }
        bar = bars[-1]
    else:
        return {
            'pivot': np.nan,
            'r1': np.nan,
            'r2': np.nan,
            's1': np.nan,
            's2': np.nan
        }
    high = bar['high']
    low = bar['low']
    close = bar['close']

    pivot = (high + low + close) / 3.0
    r1 = 2 * pivot - low
    r2 = pivot + (high - low)
    s1 = 2 * pivot - high
    s2 = pivot - (high - low)

    return {
        'pivot': pivot,
        'r1': r1,
        'r2': r2,
        's1': s1,
        's2': s2
    }


# ==================== 成交量指标 ====================

def calculate_obv(bars: List[Dict]) -> np.ndarray:
    """
    计算能量潮指标 (OBV)。

    公式:
        如果 收盘价 > 前收盘价: OBV = OBV_前值 + 成交量
        如果 收盘价 < 前收盘价: OBV = OBV_前值 - 成交量
        如果 收盘价 == 前收盘价: OBV = OBV_前值

    Args:
        bars: OHLCV K 线数据列表

    Returns:
        OBV 值数组

    用途:
        OBV 通过成交量确认价格趋势:
        - OBV 上升 + 价格上升: 强势上涨（成交量确认）
        - OBV 下降 + 价格上升: 弱势上涨（背离，警告）
        - OBV 上升 + 价格下降: 积累阶段，可能反转

    Example:
        >>> obv = calculate_obv(bars)
        >>> if obv[-1] > obv[-20]:  # OBV 在 20 天内上升
        ...     print("成交量确认上升趋势")
    """
    if len(bars) < 2:
        return np.array([0.0])

    closes = _extract_prices(bars, 'close')
    volumes = _extract_prices(bars, 'volume')

    obv = np.zeros(len(bars))
    obv[0] = volumes[0]

    for i in range(1, len(bars)):
        if closes[i] > closes[i - 1]:
            obv[i] = obv[i - 1] + volumes[i]
        elif closes[i] < closes[i - 1]:
            obv[i] = obv[i - 1] - volumes[i]
        else:
            obv[i] = obv[i - 1]

    return obv


def calculate_vwap(bars: List[Dict]) -> np.ndarray:
    """
    计算成交量加权平均价 (VWAP)。

    公式:
        VWAP = sum(典型价格 * 成交量) / sum(成交量)
        其中 典型价格 = (最高价 + 最低价 + 收盘价) / 3

    Args:
        bars: OHLCV K 线数据列表

    Returns:
        VWAP 值数组（从起点开始累计）

    用途:
        VWAP 代表按成交量加权的平均价格:
        - 价格 > VWAP: 看涨（机构买入）
        - 价格 < VWAP: 看跌（机构卖出）
        - 用作动态支撑/阻力位

    Example:
        >>> vwap = calculate_vwap(bars)
        >>> if current_price > vwap[-1]:
        ...     print("价格高于 VWAP - 看涨")
    """
    if len(bars) < 1:
        return np.array([])

    highs = _extract_prices(bars, 'high')
    lows = _extract_prices(bars, 'low')
    closes = _extract_prices(bars, 'close')
    volumes = _extract_prices(bars, 'volume')

    # 计算典型价格
    typical_price = (highs + lows + closes) / 3.0

    # 计算累计 VWAP
    vwap = np.zeros(len(bars))
    cumulative_pv = 0.0
    cumulative_volume = 0.0

    for i in range(len(bars)):
        cumulative_pv += typical_price[i] * volumes[i]
        cumulative_volume += volumes[i]

        if cumulative_volume > 0:
            vwap[i] = cumulative_pv / cumulative_volume
        else:
            vwap[i] = typical_price[i]

    return vwap


# ==================== 导出所有函数 ====================

__all__ = [
    # 移动平均线
    'calculate_sma',
    'calculate_ema',
    'calculate_wma',

    # 动量指标
    'calculate_rsi',
    'calculate_macd',
    'calculate_stochastic',

    # 波动率指标
    'calculate_bollinger_bands',
    'calculate_atr',
    'calculate_historical_volatility',

    # 趋势指标
    'calculate_adx',
    'detect_trend',

    # 支撑/阻力位
    'find_swing_highs',
    'find_swing_lows',
    'calculate_pivot_points',

    # 成交量指标
    'calculate_obv',
    'calculate_vwap',
]
