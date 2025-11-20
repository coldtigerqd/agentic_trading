"""
Technical Indicators Library for Agentic AlphaHive Runtime.

Provides battle-tested technical analysis functions using NumPy vectorization
for 10x+ performance improvement over naive Python loops.

All functions handle edge cases gracefully (NaN, insufficient data, invalid parameters)
and follow industry-standard calculation methods.

Input Format:
    bars: List[Dict] with keys ['open', 'high', 'low', 'close', 'volume', 'timestamp']

Output Format:
    NumPy arrays or dicts (depending on indicator complexity)
"""

import numpy as np
import warnings
from typing import List, Dict, Optional, Tuple
from datetime import datetime


# ==================== HELPER FUNCTIONS ====================

def _extract_prices(bars: List[Dict], field: str = 'close') -> np.ndarray:
    """
    Extract price array from bars with NaN handling.

    Args:
        bars: List of OHLCV dictionaries
        field: Price field to extract ('open', 'high', 'low', 'close', 'volume')

    Returns:
        NumPy array of prices
    """
    if not bars:
        return np.array([])

    try:
        prices = np.array([float(bar[field]) for bar in bars])
        return prices
    except (KeyError, ValueError, TypeError):
        warnings.warn(f"Invalid data in field '{field}', returning empty array")
        return np.array([])


def _validate_period(bars: List[Dict], period: int, indicator_name: str) -> bool:
    """
    Validate sufficient data for period-based calculations.

    Args:
        bars: List of OHLCV bars
        period: Required period length
        indicator_name: Name of indicator (for warning message)

    Returns:
        True if sufficient data, False otherwise
    """
    if period <= 0:
        warnings.warn(
            f"Invalid period for {indicator_name}: {period} (must be > 0)"
        )
        return False
    if len(bars) < period:
        warnings.warn(
            f"Insufficient data for {indicator_name}({period}): "
            f"need {period} bars, got {len(bars)}"
        )
        return False
    return True


# ==================== MOVING AVERAGES ====================

def calculate_sma(bars: List[Dict], period: int, field: str = 'close') -> np.ndarray:
    """
    Calculate Simple Moving Average (SMA).

    Formula: SMA = sum(prices[-period:]) / period

    Args:
        bars: List of OHLCV bars
        period: Number of periods for averaging
        field: Price field to use (default: 'close')

    Returns:
        Array where first (period-1) values are NaN, rest are SMA values

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

    # Use NumPy convolve for vectorized moving average
    # This is ~10x faster than Python loops
    weights = np.ones(period) / period
    sma = np.convolve(prices, weights, mode='valid')

    # Prepend NaN for first (period-1) values
    result = np.concatenate([np.full(period - 1, np.nan), sma])
    return result


def calculate_ema(bars: List[Dict], period: int, field: str = 'close') -> np.ndarray:
    """
    Calculate Exponential Moving Average (EMA).

    Formula:
        multiplier = 2 / (period + 1)
        EMA[i] = price[i] * multiplier + EMA[i-1] * (1 - multiplier)

    Args:
        bars: List of OHLCV bars
        period: Number of periods for EMA
        field: Price field to use (default: 'close')

    Returns:
        Array of EMA values (first value is SMA, rest are exponential)

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

    # Find first valid window of 'period' non-NaN values
    first_valid = None
    for i in range(period - 1, len(prices)):
        window = prices[i - period + 1:i + 1]
        if not np.any(np.isnan(window)):
            # Initialize with SMA of first valid window
            ema[i] = np.mean(window)
            first_valid = i
            break

    if first_valid is None:
        return ema  # All NaN if no valid window found

    # Calculate EMA from first valid point forward
    for i in range(first_valid + 1, len(prices)):
        if np.isnan(prices[i]):
            ema[i] = ema[i - 1]  # Propagate previous EMA on NaN
        else:
            ema[i] = prices[i] * multiplier + ema[i - 1] * (1 - multiplier)

    return ema


def calculate_wma(bars: List[Dict], period: int, field: str = 'close') -> np.ndarray:
    """
    Calculate Weighted Moving Average (WMA).

    Formula: WMA = sum(price[i] * weight[i]) / sum(weight[i])
    where weight[i] = i + 1 (linear weighting, recent prices weighted more)

    Args:
        bars: List of OHLCV bars
        period: Number of periods
        field: Price field to use

    Returns:
        Array of WMA values
    """
    if not _validate_period(bars, period, "WMA"):
        return np.full(len(bars), np.nan)

    prices = _extract_prices(bars, field)
    if len(prices) == 0:
        return np.array([])

    # Create linear weights (1, 2, 3, ..., period)
    weights = np.arange(1, period + 1)
    weight_sum = weights.sum()

    wma = np.full(len(prices), np.nan)

    # Calculate WMA for each valid window
    for i in range(period - 1, len(prices)):
        window = prices[i - period + 1:i + 1]
        wma[i] = np.dot(window, weights) / weight_sum

    return wma


# ==================== MOMENTUM INDICATORS ====================

def calculate_rsi(bars: List[Dict], period: int = 14, field: str = 'close') -> np.ndarray:
    """
    Calculate Relative Strength Index (RSI) using Wilder's smoothing method.

    Formula:
        RS = Average Gain / Average Loss
        RSI = 100 - (100 / (1 + RS))

    Args:
        bars: List of OHLCV bars
        period: Number of periods (default: 14)
        field: Price field to use

    Returns:
        Array of RSI values in range [0, 100]
        First (period) values are NaN

    Edge Cases:
        - Constant price: Returns 50.0 (neutral)
        - Only gains: Returns 100.0
        - Only losses: Returns 0.0

    Example:
        >>> rsi = calculate_rsi(bars, period=14)
        >>> # RSI > 70 indicates overbought
        >>> # RSI < 30 indicates oversold
    """
    if not _validate_period(bars, period + 1, "RSI"):
        return np.full(len(bars), np.nan)

    prices = _extract_prices(bars, field)
    if len(prices) == 0:
        return np.array([])

    # Calculate price changes
    deltas = np.diff(prices)

    # Separate gains and losses
    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)

    # Calculate initial average gain/loss (simple average)
    avg_gain = np.mean(gains[:period])
    avg_loss = np.mean(losses[:period])

    # Calculate RSI using Wilder's smoothing
    rsi = np.full(len(prices), np.nan)

    for i in range(period, len(prices) - 1):
        # Wilder's smoothing: (previous_avg * (period-1) + current_value) / period
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period

        if avg_loss == 0 and avg_gain == 0:
            rsi[i + 1] = 50.0  # Constant price, neutral RSI
        elif avg_loss == 0:
            rsi[i + 1] = 100.0  # Only gains, maximum RSI
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
    Calculate MACD (Moving Average Convergence Divergence).

    Formula:
        MACD Line = EMA(fast) - EMA(slow)
        Signal Line = EMA(MACD Line, signal)
        Histogram = MACD Line - Signal Line

    Args:
        bars: List of OHLCV bars
        fast: Fast EMA period (default: 12)
        slow: Slow EMA period (default: 26)
        signal: Signal line EMA period (default: 9)
        field: Price field to use

    Returns:
        Dict with keys:
            - 'macd_line': MACD values
            - 'signal_line': Signal line values
            - 'histogram': MACD - Signal (crossover indicator)

    Signals:
        - Histogram > 0: Bullish (MACD above signal)
        - Histogram < 0: Bearish (MACD below signal)
        - Histogram crosses above 0: Buy signal
        - Histogram crosses below 0: Sell signal

    Example:
        >>> macd_data = calculate_macd(bars)
        >>> if macd_data['histogram'][-1] > 0 and macd_data['histogram'][-2] <= 0:
        ...     print("Bullish crossover!")
    """
    if not _validate_period(bars, slow + signal, "MACD"):
        n = len(bars)
        return {
            'macd_line': np.full(n, np.nan),
            'signal_line': np.full(n, np.nan),
            'histogram': np.full(n, np.nan)
        }

    # Calculate fast and slow EMAs
    ema_fast = calculate_ema(bars, fast, field)
    ema_slow = calculate_ema(bars, slow, field)

    # MACD line = fast EMA - slow EMA
    macd_line = ema_fast - ema_slow

    # Signal line = EMA of MACD line
    # Convert MACD line to bars format for EMA calculation
    macd_bars = [{'close': val} for val in macd_line]
    signal_line = calculate_ema(macd_bars, signal, 'close')

    # Histogram = MACD - Signal
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
    Calculate Stochastic Oscillator.

    Formula:
        %K = 100 * (Close - Lowest Low) / (Highest High - Lowest Low)
        %D = SMA(%K, d_period)

    Args:
        bars: List of OHLCV bars
        k_period: Lookback period for %K (default: 14)
        d_period: SMA period for %D (default: 3)

    Returns:
        Dict with keys:
            - 'k': %K values (fast stochastic)
            - 'd': %D values (slow stochastic, smoothed)

    Signals:
        - %K > 80: Overbought
        - %K < 20: Oversold
        - %K crosses above %D: Buy signal
        - %K crosses below %D: Sell signal
    """
    if not _validate_period(bars, k_period, "Stochastic"):
        n = len(bars)
        return {'k_line': np.full(n, np.nan), 'd_line': np.full(n, np.nan)}

    highs = _extract_prices(bars, 'high')
    lows = _extract_prices(bars, 'low')
    closes = _extract_prices(bars, 'close')

    k = np.full(len(bars), np.nan)

    # Calculate %K for each period
    for i in range(k_period - 1, len(bars)):
        window_high = np.max(highs[i - k_period + 1:i + 1])
        window_low = np.min(lows[i - k_period + 1:i + 1])

        if window_high == window_low:
            k[i] = 50.0  # Neutral when no range
        else:
            k[i] = 100.0 * (closes[i] - window_low) / (window_high - window_low)

    # Calculate %D (SMA of %K)
    k_bars = [{'close': val} for val in k]
    d = calculate_sma(k_bars, d_period, 'close')

    return {'k_line': k, 'd_line': d}


# ==================== VOLATILITY INDICATORS ====================

def calculate_bollinger_bands(
    bars: List[Dict],
    period: int = 20,
    std_dev: float = 2.0,
    field: str = 'close'
) -> Dict[str, np.ndarray]:
    """
    Calculate Bollinger Bands.

    Formula:
        Middle Band = SMA(period)
        Upper Band = Middle Band + (std_dev * standard deviation)
        Lower Band = Middle Band - (std_dev * standard deviation)
        Bandwidth = (Upper - Lower) / Middle

    Args:
        bars: List of OHLCV bars
        period: Period for SMA and std dev (default: 20)
        std_dev: Number of standard deviations (default: 2.0)
        field: Price field to use

    Returns:
        Dict with keys:
            - 'upper_band': Upper Bollinger Band
            - 'middle_band': SMA (middle line)
            - 'lower_band': Lower Bollinger Band
            - 'bandwidth': (upper - lower) / middle (volatility metric)

    Signals:
        - Price at upper band: Potential resistance, consider selling
        - Price at lower band: Potential support, consider buying
        - Bandwidth squeeze: Low volatility, breakout likely
        - Bandwidth expansion: High volatility, trend continuation

    Example:
        >>> bb = calculate_bollinger_bands(bars, period=20, std_dev=2)
        >>> if bars[-1]['close'] <= bb['lower_band'][-1]:
        ...     print("Price at lower band - potential buy")
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

    # Calculate rolling standard deviation
    std = np.full(len(bars), np.nan)
    for i in range(period - 1, len(bars)):
        window = prices[i - period + 1:i + 1]
        std[i] = np.std(window, ddof=1)  # Sample std dev

    # Calculate bands
    upper_band = middle_band + (std_dev * std)
    lower_band = middle_band - (std_dev * std)

    # Calculate bandwidth (volatility metric)
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
    Calculate Average True Range (ATR) using Wilder's smoothing.

    Formula:
        True Range = max(high - low, abs(high - prev_close), abs(low - prev_close))
        ATR = Wilder's smoothed average of True Range

    Args:
        bars: List of OHLCV bars
        period: ATR period (default: 14)

    Returns:
        Array of ATR values in dollars

    Usage:
        ATR represents average price movement and is used for:
        - Stop loss placement (e.g., stop at entry - 2*ATR)
        - Position sizing (risk per unit = ATR)
        - Volatility assessment

    Example:
        >>> atr = calculate_atr(bars, period=14)
        >>> stop_loss = entry_price - (2 * atr[-1])
    """
    if not _validate_period(bars, period + 1, "ATR"):
        return np.full(len(bars), np.nan)

    highs = _extract_prices(bars, 'high')
    lows = _extract_prices(bars, 'low')
    closes = _extract_prices(bars, 'close')

    # Calculate True Range
    tr = np.full(len(bars), np.nan)
    tr[0] = highs[0] - lows[0]  # First bar uses simple range

    for i in range(1, len(bars)):
        hl = highs[i] - lows[i]
        hc = abs(highs[i] - closes[i - 1])
        lc = abs(lows[i] - closes[i - 1])
        tr[i] = max(hl, hc, lc)

    # Calculate ATR using Wilder's smoothing
    atr = np.full(len(bars), np.nan)
    atr[period] = np.mean(tr[1:period + 1])  # Initial ATR is simple average

    for i in range(period + 1, len(bars)):
        # Wilder's smoothing: (previous_atr * (period-1) + current_tr) / period
        atr[i] = (atr[i - 1] * (period - 1) + tr[i]) / period

    return atr


def calculate_historical_volatility(
    bars: List[Dict],
    period: int = 20,
    field: str = 'close'
) -> float:
    """
    Calculate annualized historical volatility.

    Formula:
        Daily Return = ln(price[i] / price[i-1])
        Volatility = std(returns) * sqrt(252)

    Args:
        bars: List of OHLCV bars
        period: Lookback period (default: 20 days)
        field: Price field to use

    Returns:
        Annualized volatility as decimal (e.g., 0.25 = 25%)

    Usage:
        Compare to implied volatility (IV) to identify mispricing:
        - HV > IV: Volatility underpriced, favor buying options
        - HV < IV: Volatility overpriced, favor selling options

    Example:
        >>> hv = calculate_historical_volatility(bars, period=20)
        >>> print(f"20-day HV: {hv:.1%}")  # e.g., "20-day HV: 24.5%"
    """
    if not _validate_period(bars, period + 1, "Historical Volatility"):
        return np.nan

    prices = _extract_prices(bars, field)
    if len(prices) < period + 1:
        return np.nan

    # Use most recent 'period' bars
    recent_prices = prices[-period - 1:]

    # Calculate log returns
    returns = np.log(recent_prices[1:] / recent_prices[:-1])

    # Calculate standard deviation
    volatility = np.std(returns, ddof=1)  # Sample std dev

    # Annualize (252 trading days per year)
    annualized_vol = volatility * np.sqrt(252)

    return annualized_vol


# ==================== TREND INDICATORS ====================

def calculate_adx(bars: List[Dict], period: int = 14) -> np.ndarray:
    """
    Calculate Average Directional Index (ADX).

    ADX measures trend strength (not direction) on scale 0-100:
        - ADX < 20: Weak trend (ranging market)
        - ADX 20-40: Moderate trend
        - ADX > 40: Strong trend

    Args:
        bars: List of OHLCV bars
        period: ADX period (default: 14)

    Returns:
        Array of ADX values [0, 100]

    Usage:
        Use ADX to determine if market is trending or ranging:
        - High ADX: Use trend-following strategies
        - Low ADX: Use mean-reversion strategies

    Example:
        >>> adx = calculate_adx(bars, period=14)
        >>> if adx[-1] < 25:
        ...     print("Weak trend - use mean reversion strategy")
    """
    if not _validate_period(bars, period * 2, "ADX"):
        return np.full(len(bars), np.nan)

    highs = _extract_prices(bars, 'high')
    lows = _extract_prices(bars, 'low')
    closes = _extract_prices(bars, 'close')

    # Calculate +DM and -DM (directional movement)
    plus_dm = np.full(len(bars), 0.0)
    minus_dm = np.full(len(bars), 0.0)

    for i in range(1, len(bars)):
        high_diff = highs[i] - highs[i - 1]
        low_diff = lows[i - 1] - lows[i]

        if high_diff > low_diff and high_diff > 0:
            plus_dm[i] = high_diff
        if low_diff > high_diff and low_diff > 0:
            minus_dm[i] = low_diff

    # Calculate ATR
    atr = calculate_atr(bars, period)

    # Calculate +DI and -DI (directional indicators)
    plus_di = np.full(len(bars), np.nan)
    minus_di = np.full(len(bars), np.nan)

    # Smooth DM values using Wilder's smoothing
    smoothed_plus_dm = np.copy(plus_dm)
    smoothed_minus_dm = np.copy(minus_dm)

    for i in range(period, len(bars)):
        smoothed_plus_dm[i] = (smoothed_plus_dm[i - 1] * (period - 1) + plus_dm[i]) / period
        smoothed_minus_dm[i] = (smoothed_minus_dm[i - 1] * (period - 1) + minus_dm[i]) / period

        if atr[i] > 0:
            plus_di[i] = 100 * smoothed_plus_dm[i] / atr[i]
            minus_di[i] = 100 * smoothed_minus_dm[i] / atr[i]

    # Calculate DX (directional index)
    dx = np.full(len(bars), np.nan)
    for i in range(period, len(bars)):
        di_sum = plus_di[i] + minus_di[i]
        if di_sum > 0:
            dx[i] = 100 * abs(plus_di[i] - minus_di[i]) / di_sum

    # Calculate ADX (smoothed DX)
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
    Detect trend direction and strength using moving average relationships.

    Classification:
        - "STRONG_UPTREND": Price > SMA_short > SMA_long, both SMAs rising
        - "WEAK_UPTREND": Price > SMA_short, but SMA_short ≈ SMA_long
        - "STRONG_DOWNTREND": Price < SMA_short < SMA_long, both SMAs falling
        - "WEAK_DOWNTREND": Price < SMA_short, but SMA_short ≈ SMA_long
        - "SIDEWAYS": SMAs flat, no clear direction

    Args:
        bars: List of OHLCV bars
        sma_short: Short SMA period (default: 20)
        sma_long: Long SMA period (default: 50)

    Returns:
        Trend classification string

    Example:
        >>> trend = detect_trend(bars, sma_short=20, sma_long=50)
        >>> if trend == "STRONG_UPTREND":
        ...     # Use trend-following long strategies
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

    # Calculate SMA slopes (last 10 days)
    sma_s_slope = (sma_s[-1] - sma_s[-10]) / sma_s[-10]
    sma_l_slope = (sma_l[-1] - sma_l[-10]) / sma_l[-10]

    # Check alignment
    if current_price > current_sma_s > current_sma_l:
        if sma_s_slope > 0.005:  # >0.5% rise over 10 days
            return "STRONG_UPTREND"
        else:
            return "WEAK_UPTREND"

    elif current_price < current_sma_s < current_sma_l:
        if sma_s_slope < -0.005:  # >0.5% decline over 10 days
            return "STRONG_DOWNTREND"
        else:
            return "WEAK_DOWNTREND"

    elif abs(sma_s_slope) < 0.005 and abs(sma_l_slope) < 0.005:
        return "SIDEWAYS"

    elif current_price > current_sma_s:
        return "WEAK_UPTREND"
    else:
        return "WEAK_DOWNTREND"


# ==================== SUPPORT/RESISTANCE ====================

def find_swing_highs(bars: List[Dict], window: int = 5) -> List[float]:
    """
    Find swing highs (local maxima) for resistance levels.

    A swing high is a price that is higher than all prices within
    ±window bars on either side.

    Args:
        bars: List of OHLCV bars
        window: Lookback/lookahead window (default: 5)

    Returns:
        List of swing high prices, sorted in descending order

    Usage:
        Use swing highs as resistance levels for:
        - Take profit targets
        - Short entry levels
        - Strike selection (sell strikes at resistance)

    Example:
        >>> resistance_levels = find_swing_highs(bars, window=5)
        >>> nearest_resistance = min([r for r in resistance_levels if r > current_price])
    """
    if len(bars) < window * 2 + 1:
        return []

    highs = _extract_prices(bars, 'high')
    swing_highs = []

    # Check each potential swing high
    for i in range(window, len(highs) - window):
        is_swing_high = True

        # Check if current high is greater than all surrounding highs
        for j in range(i - window, i + window + 1):
            if j != i and highs[j] >= highs[i]:
                is_swing_high = False
                break

        if is_swing_high:
            swing_highs.append(highs[i])

    # Sort in descending order (highest resistance first)
    return sorted(swing_highs, reverse=True)


def find_swing_lows(bars: List[Dict], window: int = 5) -> List[float]:
    """
    Find swing lows (local minima) for support levels.

    A swing low is a price that is lower than all prices within
    ±window bars on either side.

    Args:
        bars: List of OHLCV bars
        window: Lookback/lookahead window (default: 5)

    Returns:
        List of swing low prices, sorted in ascending order

    Usage:
        Use swing lows as support levels for:
        - Stop loss placement
        - Long entry levels
        - Strike selection (buy strikes at support)

    Example:
        >>> support_levels = find_swing_lows(bars, window=5)
        >>> nearest_support = max([s for s in support_levels if s < current_price])
    """
    if len(bars) < window * 2 + 1:
        return []

    lows = _extract_prices(bars, 'low')
    swing_lows = []

    # Check each potential swing low
    for i in range(window, len(lows) - window):
        is_swing_low = True

        # Check if current low is less than all surrounding lows
        for j in range(i - window, i + window + 1):
            if j != i and lows[j] <= lows[i]:
                is_swing_low = False
                break

        if is_swing_low:
            swing_lows.append(lows[i])

    # Sort in ascending order (lowest support first)
    return sorted(swing_lows)


def calculate_pivot_points(bars) -> Dict[str, float]:
    """
    Calculate pivot points and support/resistance levels.

    Uses the most recent complete bar (e.g., yesterday's OHLC for today's pivots).

    Formula:
        Pivot = (High + Low + Close) / 3
        R1 = 2 * Pivot - Low
        R2 = Pivot + (High - Low)
        S1 = 2 * Pivot - High
        S2 = Pivot - (High - Low)

    Args:
        bars: Either a single OHLCV bar dict or a list of bars (uses last bar)

    Returns:
        Dict with pivot point and support/resistance levels

    Usage:
        Pivot points are intraday support/resistance levels used for:
        - Day trading entry/exit levels
        - Stop loss placement
        - Target price selection

    Example:
        >>> pivots = calculate_pivot_points(bars[-1])  # Single bar
        >>> pivots = calculate_pivot_points(bars)  # List of bars
        >>> if price < pivots['pivot']:
        ...     target = pivots['s1']  # Bearish, target S1
    """
    # Handle both single bar and list of bars
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


# ==================== VOLUME INDICATORS ====================

def calculate_obv(bars: List[Dict]) -> np.ndarray:
    """
    Calculate On-Balance Volume (OBV).

    Formula:
        If close > prev_close: OBV = OBV_prev + volume
        If close < prev_close: OBV = OBV_prev - volume
        If close == prev_close: OBV = OBV_prev

    Args:
        bars: List of OHLCV bars

    Returns:
        Array of OBV values

    Usage:
        OBV confirms price trends with volume:
        - Rising OBV + rising price: Strong uptrend (volume confirms)
        - Falling OBV + rising price: Weak uptrend (divergence, warning)
        - Rising OBV + falling price: Accumulation, potential reversal

    Example:
        >>> obv = calculate_obv(bars)
        >>> if obv[-1] > obv[-20]:  # OBV rising over 20 days
        ...     print("Volume confirms uptrend")
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
    Calculate Volume-Weighted Average Price (VWAP).

    Formula:
        VWAP = sum(typical_price * volume) / sum(volume)
        where typical_price = (high + low + close) / 3

    Args:
        bars: List of OHLCV bars

    Returns:
        Array of VWAP values (cumulative from start)

    Usage:
        VWAP represents average price weighted by volume:
        - Price > VWAP: Bullish (institutional buying)
        - Price < VWAP: Bearish (institutional selling)
        - Used as dynamic support/resistance

    Example:
        >>> vwap = calculate_vwap(bars)
        >>> if current_price > vwap[-1]:
        ...     print("Trading above VWAP - bullish")
    """
    if len(bars) < 1:
        return np.array([])

    highs = _extract_prices(bars, 'high')
    lows = _extract_prices(bars, 'low')
    closes = _extract_prices(bars, 'close')
    volumes = _extract_prices(bars, 'volume')

    # Calculate typical price
    typical_price = (highs + lows + closes) / 3.0

    # Calculate cumulative VWAP
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


# ==================== EXPORT ALL FUNCTIONS ====================

__all__ = [
    # Moving Averages
    'calculate_sma',
    'calculate_ema',
    'calculate_wma',

    # Momentum Indicators
    'calculate_rsi',
    'calculate_macd',
    'calculate_stochastic',

    # Volatility Indicators
    'calculate_bollinger_bands',
    'calculate_atr',
    'calculate_historical_volatility',

    # Trend Indicators
    'calculate_adx',
    'detect_trend',

    # Support/Resistance
    'find_swing_highs',
    'find_swing_lows',
    'calculate_pivot_points',

    # Volume Indicators
    'calculate_obv',
    'calculate_vwap',
]
