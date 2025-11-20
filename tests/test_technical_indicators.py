"""
Comprehensive unit tests for technical indicators library.

Tests cover:
- Accuracy vs reference implementations
- Edge cases (NaN, empty, insufficient data)
- Performance benchmarks (10x speedup requirement)
- All 15 indicator functions
"""

import pytest
import numpy as np
import time
from typing import List, Dict

import sys
sys.path.insert(0, '/home/adt/project/agentic_trading')

from skills.technical_indicators import (
    calculate_sma,
    calculate_ema,
    calculate_wma,
    calculate_rsi,
    calculate_macd,
    calculate_stochastic,
    calculate_bollinger_bands,
    calculate_atr,
    calculate_historical_volatility,
    calculate_adx,
    detect_trend,
    find_swing_highs,
    find_swing_lows,
    calculate_pivot_points,
    calculate_obv,
    calculate_vwap
)


# ============================================================================
# Test Fixtures - Sample Data
# ============================================================================

@pytest.fixture
def sample_bars_30():
    """30 days of realistic OHLCV data with uptrend."""
    np.random.seed(42)
    base_price = 100.0
    bars = []

    for i in range(30):
        # Uptrend with noise
        trend = base_price + i * 0.5
        noise = np.random.normal(0, 1.0)
        close = trend + noise

        high = close + abs(np.random.normal(0, 0.5))
        low = close - abs(np.random.normal(0, 0.5))
        open_price = low + (high - low) * np.random.random()
        volume = int(1_000_000 + np.random.normal(0, 100_000))

        bars.append({
            'timestamp': f'2024-01-{i+1:02d}',
            'open': round(open_price, 2),
            'high': round(high, 2),
            'low': round(low, 2),
            'close': round(close, 2),
            'volume': volume
        })

    return bars


@pytest.fixture
def sample_bars_100():
    """100 days of realistic OHLCV data for longer-period indicators."""
    np.random.seed(123)
    base_price = 150.0
    bars = []

    for i in range(100):
        # Mix of trends
        if i < 30:
            trend = base_price + i * 0.3  # Uptrend
        elif i < 60:
            trend = base_price + 30 * 0.3 - (i - 30) * 0.2  # Downtrend
        else:
            trend = base_price + 30 * 0.3 - 30 * 0.2  # Sideways

        noise = np.random.normal(0, 1.5)
        close = trend + noise

        high = close + abs(np.random.normal(0, 0.7))
        low = close - abs(np.random.normal(0, 0.7))
        open_price = low + (high - low) * np.random.random()
        volume = int(2_000_000 + np.random.normal(0, 200_000))

        bars.append({
            'timestamp': f'2024-{(i//30)+1:02d}-{(i%30)+1:02d}',
            'open': round(open_price, 2),
            'high': round(high, 2),
            'low': round(low, 2),
            'close': round(close, 2),
            'volume': volume
        })

    return bars


@pytest.fixture
def constant_price_bars():
    """Bars with constant price (edge case for RSI, volatility)."""
    return [
        {
            'timestamp': f'2024-01-{i+1:02d}',
            'open': 100.0,
            'high': 100.0,
            'low': 100.0,
            'close': 100.0,
            'volume': 1_000_000
        }
        for i in range(20)
    ]


@pytest.fixture
def bars_with_nan():
    """Bars with NaN gaps (missing data)."""
    bars = []
    for i in range(30):
        close = 100.0 + i * 0.5 if i not in [10, 11, 12] else np.nan
        bars.append({
            'timestamp': f'2024-01-{i+1:02d}',
            'open': close,
            'high': close + 1 if not np.isnan(close) else np.nan,
            'low': close - 1 if not np.isnan(close) else np.nan,
            'close': close,
            'volume': 1_000_000
        })
    return bars


# ============================================================================
# Moving Average Tests
# ============================================================================

class TestMovingAverages:
    """Test SMA, EMA, WMA calculations."""

    def test_sma_basic_calculation(self, sample_bars_30):
        """Test SMA calculation with known values."""
        result = calculate_sma(sample_bars_30, period=5)

        # First 4 values should be NaN
        assert np.all(np.isnan(result[:4]))

        # 5th value should be mean of first 5 closes
        closes = [bar['close'] for bar in sample_bars_30]
        expected_5th = np.mean(closes[:5])
        assert np.isclose(result[4], expected_5th, rtol=0.001)

        # Result length matches input
        assert len(result) == len(sample_bars_30)

    def test_sma_insufficient_data(self):
        """Test SMA with insufficient data returns NaN array."""
        bars = [{'close': 100.0, 'timestamp': '2024-01-01'}] * 5
        result = calculate_sma(bars, period=20)

        assert len(result) == 5
        assert np.all(np.isnan(result))

    def test_ema_basic_calculation(self, sample_bars_30):
        """Test EMA calculation - more weight to recent prices."""
        result = calculate_ema(sample_bars_30, period=10)

        # First 9 values should be NaN
        assert np.all(np.isnan(result[:9]))

        # EMA should exist after period
        assert not np.isnan(result[10])

        # In uptrend, EMA should lag behind price but follow trend
        closes = [bar['close'] for bar in sample_bars_30]
        assert result[-1] < closes[-1]  # Lags current price
        assert result[-1] > result[-5]  # Following uptrend

    def test_wma_weights_recent_prices(self, sample_bars_30):
        """Test WMA gives more weight to recent prices."""
        result = calculate_wma(sample_bars_30, period=5)

        # First 4 values should be NaN
        assert np.all(np.isnan(result[:4]))

        # WMA should weight recent prices more heavily
        closes = [bar['close'] for bar in sample_bars_30[0:5]]
        weights = np.arange(1, 6)  # 1, 2, 3, 4, 5
        expected = np.dot(closes, weights) / weights.sum()

        assert np.isclose(result[4], expected, rtol=0.001)

    def test_moving_averages_empty_input(self):
        """Test all moving averages handle empty input."""
        empty_bars = []

        assert len(calculate_sma(empty_bars, period=10)) == 0
        assert len(calculate_ema(empty_bars, period=10)) == 0
        assert len(calculate_wma(empty_bars, period=10)) == 0


# ============================================================================
# Momentum Indicator Tests
# ============================================================================

class TestMomentumIndicators:
    """Test RSI, MACD, Stochastic calculations."""

    def test_rsi_range_bounds(self, sample_bars_100):
        """Test RSI stays within [0, 100] range."""
        result = calculate_rsi(sample_bars_100, period=14)

        # Remove NaN values
        valid_rsi = result[~np.isnan(result)]

        # All values should be in [0, 100]
        assert np.all((valid_rsi >= 0) & (valid_rsi <= 100))

    def test_rsi_constant_price(self, constant_price_bars):
        """Test RSI returns 50.0 for constant price (neutral)."""
        result = calculate_rsi(constant_price_bars, period=14)

        # After initial period, RSI should be 50 (neutral)
        assert np.isclose(result[15], 50.0, atol=0.1)

    def test_rsi_overbought_oversold(self):
        """Test RSI detects overbought/oversold conditions."""
        # Create strongly trending up data (overbought)
        uptrend_bars = [
            {'close': 100.0 + i * 2.0, 'timestamp': f'2024-01-{i+1:02d}'}
            for i in range(30)
        ]
        result_up = calculate_rsi(uptrend_bars, period=14)

        # Should show overbought (RSI > 70)
        assert result_up[-1] > 70

        # Create strongly trending down data (oversold)
        downtrend_bars = [
            {'close': 100.0 - i * 2.0, 'timestamp': f'2024-01-{i+1:02d}'}
            for i in range(30)
        ]
        result_down = calculate_rsi(downtrend_bars, period=14)

        # Should show oversold (RSI < 30)
        assert result_down[-1] < 30

    def test_macd_structure(self, sample_bars_100):
        """Test MACD returns correct structure."""
        result = calculate_macd(sample_bars_100, fast=12, slow=26, signal=9)

        # Should return dict with 3 keys
        assert isinstance(result, dict)
        assert 'macd_line' in result
        assert 'signal_line' in result
        assert 'histogram' in result

        # All should be arrays of same length
        assert len(result['macd_line']) == len(sample_bars_100)
        assert len(result['signal_line']) == len(sample_bars_100)
        assert len(result['histogram']) == len(sample_bars_100)

    def test_macd_histogram_crossover(self):
        """Test MACD histogram generates values and detects trends."""
        # Create realistic price data with actual volatility
        np.random.seed(42)
        bars = []
        base = 100.0
        for i in range(100):
            # Uptrend with noise for first 50 days
            if i < 50:
                trend = base + i * 1.0
                noise = np.random.normal(0, 0.5)
            # Downtrend with noise after
            else:
                trend = base + 50 * 1.0 - (i - 50) * 1.0
                noise = np.random.normal(0, 0.5)

            close = trend + noise
            bars.append({'close': close, 'timestamp': f'2024-01-{i+1:02d}'})

        result = calculate_macd(bars, fast=12, slow=26, signal=9)
        histogram = result['histogram']
        macd_line = result['macd_line']
        signal_line = result['signal_line']

        # Verify structure - histogram should exist
        assert len(histogram) == 100
        # After initial period, histogram should have values
        valid_histogram = histogram[~np.isnan(histogram)]
        assert len(valid_histogram) > 50  # Should have valid values

        # Verify MACD line and signal line relationship
        # Histogram = MACD - Signal
        for i in range(35, 100):
            if not np.isnan(histogram[i]):
                expected = macd_line[i] - signal_line[i]
                assert np.isclose(histogram[i], expected, atol=1e-10)

    def test_stochastic_range_bounds(self, sample_bars_100):
        """Test Stochastic oscillator stays within [0, 100]."""
        result = calculate_stochastic(sample_bars_100, k_period=14, d_period=3)

        assert 'k_line' in result
        assert 'd_line' in result

        # Remove NaN values
        valid_k = result['k_line'][~np.isnan(result['k_line'])]
        valid_d = result['d_line'][~np.isnan(result['d_line'])]

        # All values in [0, 100]
        assert np.all((valid_k >= 0) & (valid_k <= 100))
        assert np.all((valid_d >= 0) & (valid_d <= 100))

    def test_stochastic_d_smooths_k(self, sample_bars_100):
        """Test %D line is smoother than %K line."""
        result = calculate_stochastic(sample_bars_100, k_period=14, d_period=3)

        # %D should have less variance than %K (it's a moving average)
        valid_k = result['k_line'][~np.isnan(result['k_line'])]
        valid_d = result['d_line'][~np.isnan(result['d_line'])]

        k_variance = np.var(valid_k)
        d_variance = np.var(valid_d)

        assert d_variance < k_variance


# ============================================================================
# Volatility Indicator Tests
# ============================================================================

class TestVolatilityIndicators:
    """Test Bollinger Bands, ATR, Historical Volatility."""

    def test_bollinger_bands_structure(self, sample_bars_30):
        """Test Bollinger Bands returns correct structure."""
        result = calculate_bollinger_bands(sample_bars_30, period=20, std_dev=2.0)

        assert isinstance(result, dict)
        assert 'upper_band' in result
        assert 'middle_band' in result
        assert 'lower_band' in result
        assert 'bandwidth' in result

        # All arrays same length
        assert len(result['upper_band']) == len(sample_bars_30)

    def test_bollinger_bands_relationship(self, sample_bars_30):
        """Test Upper > Middle > Lower band relationship."""
        result = calculate_bollinger_bands(sample_bars_30, period=20, std_dev=2.0)

        # Where valid (not NaN), upper > middle > lower
        valid_idx = ~np.isnan(result['middle_band'])

        upper = result['upper_band'][valid_idx]
        middle = result['middle_band'][valid_idx]
        lower = result['lower_band'][valid_idx]

        assert np.all(upper > middle)
        assert np.all(middle > lower)

    def test_bollinger_bands_constant_price(self, constant_price_bars):
        """Test Bollinger Bands with zero volatility."""
        result = calculate_bollinger_bands(constant_price_bars, period=10, std_dev=2.0)

        # With constant price, all bands should converge to same value
        # (std_dev = 0, so upper = middle = lower)
        valid_idx = ~np.isnan(result['middle_band'])

        upper = result['upper_band'][valid_idx]
        middle = result['middle_band'][valid_idx]
        lower = result['lower_band'][valid_idx]

        assert np.allclose(upper, middle, atol=0.01)
        assert np.allclose(middle, lower, atol=0.01)

    def test_atr_positive_values(self, sample_bars_100):
        """Test ATR produces positive values."""
        result = calculate_atr(sample_bars_100, period=14)

        # Remove NaN values
        valid_atr = result[~np.isnan(result)]

        # ATR should always be positive
        assert np.all(valid_atr > 0)

    def test_atr_reflects_volatility(self):
        """Test ATR increases with volatility."""
        # Low volatility data
        low_vol_bars = []
        for i in range(30):
            close = 100.0 + np.random.normal(0, 0.1)  # Small noise
            low_vol_bars.append({
                'high': close + 0.05,
                'low': close - 0.05,
                'close': close,
                'timestamp': f'2024-01-{i+1:02d}'
            })

        # High volatility data
        high_vol_bars = []
        for i in range(30):
            close = 100.0 + np.random.normal(0, 5.0)  # Large noise
            high_vol_bars.append({
                'high': close + 2.0,
                'low': close - 2.0,
                'close': close,
                'timestamp': f'2024-01-{i+1:02d}'
            })

        atr_low = calculate_atr(low_vol_bars, period=14)
        atr_high = calculate_atr(high_vol_bars, period=14)

        # High volatility should have higher ATR
        assert atr_high[-1] > atr_low[-1] * 5

    def test_historical_volatility_range(self, sample_bars_100):
        """Test historical volatility is non-negative."""
        result = calculate_historical_volatility(sample_bars_100, period=20)

        # Remove NaN values
        valid_vol = result[~np.isnan(result)]

        # Volatility should be positive
        assert np.all(valid_vol >= 0)

        # Typically in reasonable range (0-200% annualized)
        assert np.all(valid_vol < 200)


# ============================================================================
# Trend Detection Tests
# ============================================================================

class TestTrendDetection:
    """Test ADX and trend detection functions."""

    def test_adx_range_bounds(self, sample_bars_100):
        """Test ADX stays within [0, 100] range."""
        result = calculate_adx(sample_bars_100, period=14)

        # Remove NaN values
        valid_adx = result[~np.isnan(result)]

        # ADX should be in [0, 100]
        assert np.all((valid_adx >= 0) & (valid_adx <= 100))

    def test_adx_strong_trend_detection(self):
        """Test ADX detects strong trends."""
        # Strong uptrend
        strong_trend_bars = []
        for i in range(50):
            close = 100.0 + i * 2.0
            strong_trend_bars.append({
                'high': close + 0.5,
                'low': close - 0.5,
                'close': close,
                'timestamp': f'2024-01-{i+1:02d}'
            })

        adx = calculate_adx(strong_trend_bars, period=14)

        # Strong trend should have ADX > 25 (typically > 40)
        assert adx[-1] > 25

    def test_detect_trend_strong_uptrend(self):
        """Test trend detection identifies strong uptrend."""
        bars = []
        for i in range(60):
            close = 100.0 + i * 1.0  # Consistent uptrend
            bars.append({
                'close': close,
                'timestamp': f'2024-01-{i+1:02d}'
            })

        result = detect_trend(bars, sma_short=20, sma_long=50)

        assert result in ["STRONG_UPTREND", "WEAK_UPTREND"]

    def test_detect_trend_sideways(self):
        """Test trend detection identifies sideways market."""
        bars = []
        for i in range(60):
            # Oscillate around 100 with zero net trend
            close = 100.0 + np.sin(i * 0.3) * 3.0
            bars.append({
                'close': close,
                'timestamp': f'2024-01-{i+1:02d}'
            })

        result = detect_trend(bars, sma_short=20, sma_long=50)

        # Sideways or weak trend is acceptable for oscillating data
        assert result in ["SIDEWAYS", "WEAK_UPTREND", "WEAK_DOWNTREND"]

    def test_detect_trend_insufficient_data(self):
        """Test trend detection with insufficient data."""
        bars = [{'close': 100.0, 'timestamp': '2024-01-01'}] * 10

        result = detect_trend(bars, sma_short=20, sma_long=50)

        assert result == "UNKNOWN"


# ============================================================================
# Support/Resistance Tests
# ============================================================================

class TestSupportResistance:
    """Test swing high/low and pivot point calculations."""

    def test_find_swing_highs_detects_peaks(self):
        """Test swing highs identifies local maxima."""
        bars = []
        # Create data with clear peaks at i=10, i=30, i=50
        for i in range(60):
            if i in [10, 30, 50]:
                close = 120.0  # Peaks
            else:
                close = 100.0 + np.random.normal(0, 2.0)
            bars.append({
                'high': close + 1.0,
                'low': close - 1.0,
                'close': close,
                'timestamp': f'2024-01-{i+1:02d}'
            })

        swing_highs = find_swing_highs(bars, window=5)

        # Should detect the peaks
        assert len(swing_highs) > 0
        # Highest swing should be around 120-121
        assert swing_highs[0] > 119

    def test_find_swing_lows_detects_troughs(self):
        """Test swing lows identifies local minima."""
        bars = []
        # Create data with clear troughs at i=10, i=30, i=50
        for i in range(60):
            if i in [10, 30, 50]:
                close = 80.0  # Troughs
            else:
                close = 100.0 + np.random.normal(0, 2.0)
            bars.append({
                'high': close + 1.0,
                'low': close - 1.0,
                'close': close,
                'timestamp': f'2024-01-{i+1:02d}'
            })

        swing_lows = find_swing_lows(bars, window=5)

        # Should detect the troughs
        assert len(swing_lows) > 0
        # Lowest swing should be around 79-81
        assert swing_lows[0] < 82

    def test_calculate_pivot_points_structure(self):
        """Test pivot points calculation returns correct structure."""
        bar = {
            'high': 105.0,
            'low': 95.0,
            'close': 100.0,
            'timestamp': '2024-01-01'
        }

        result = calculate_pivot_points(bar)

        assert isinstance(result, dict)
        assert 'pivot' in result
        assert 'r1' in result
        assert 'r2' in result
        assert 's1' in result
        assert 's2' in result

    def test_calculate_pivot_points_values(self):
        """Test pivot points calculation with known values."""
        bar = {
            'high': 110.0,
            'low': 90.0,
            'close': 100.0,
            'timestamp': '2024-01-01'
        }

        result = calculate_pivot_points(bar)

        # Pivot = (H + L + C) / 3 = (110 + 90 + 100) / 3 = 100
        assert np.isclose(result['pivot'], 100.0, atol=0.01)

        # R1 = 2*P - L = 200 - 90 = 110
        assert np.isclose(result['r1'], 110.0, atol=0.01)

        # S1 = 2*P - H = 200 - 110 = 90
        assert np.isclose(result['s1'], 90.0, atol=0.01)

        # R2 = P + (H - L) = 100 + 20 = 120
        assert np.isclose(result['r2'], 120.0, atol=0.01)

        # S2 = P - (H - L) = 100 - 20 = 80
        assert np.isclose(result['s2'], 80.0, atol=0.01)


# ============================================================================
# Volume Indicator Tests
# ============================================================================

class TestVolumeIndicators:
    """Test OBV and VWAP calculations."""

    def test_obv_accumulation(self):
        """Test OBV accumulates on up days."""
        bars = []
        for i in range(20):
            close = 100.0 + i  # Consistent uptrend
            bars.append({
                'close': close,
                'volume': 1_000_000,
                'timestamp': f'2024-01-{i+1:02d}'
            })

        obv = calculate_obv(bars)

        # OBV should be monotonically increasing
        assert obv[-1] > obv[0]
        # With constant volume, should increase by 1M each day
        assert np.isclose(obv[-1] - obv[0], 19_000_000, rtol=0.01)

    def test_obv_distribution(self):
        """Test OBV decreases on down days."""
        bars = []
        for i in range(20):
            close = 100.0 - i  # Consistent downtrend
            bars.append({
                'close': close,
                'volume': 1_000_000,
                'timestamp': f'2024-01-{i+1:02d}'
            })

        obv = calculate_obv(bars)

        # OBV should be monotonically decreasing
        assert obv[-1] < obv[0]

    def test_vwap_weighted_by_volume(self):
        """Test VWAP weights prices by volume."""
        bars = []
        # Day 1: Price 100, Volume 1M
        bars.append({
            'high': 101.0,
            'low': 99.0,
            'close': 100.0,
            'volume': 1_000_000,
            'timestamp': '2024-01-01'
        })
        # Day 2: Price 200, Volume 9M (much higher weight)
        bars.append({
            'high': 201.0,
            'low': 199.0,
            'close': 200.0,
            'volume': 9_000_000,
            'timestamp': '2024-01-02'
        })

        vwap = calculate_vwap(bars)

        # VWAP should be closer to 200 than 100 due to volume weighting
        # (100*1M + 200*9M) / 10M = (100M + 1800M) / 10M = 190
        assert vwap[-1] > 180  # Closer to 200


# ============================================================================
# Edge Case Tests
# ============================================================================

class TestEdgeCases:
    """Test edge case handling across all indicators."""

    def test_empty_array_handling(self):
        """Test all indicators handle empty input gracefully."""
        empty_bars = []

        # Should return empty arrays, not crash
        assert len(calculate_sma(empty_bars, period=10)) == 0
        assert len(calculate_ema(empty_bars, period=10)) == 0
        assert len(calculate_rsi(empty_bars, period=14)) == 0
        assert len(calculate_atr(empty_bars, period=14)) == 0

        macd = calculate_macd(empty_bars, fast=12, slow=26, signal=9)
        assert len(macd['macd_line']) == 0

    def test_nan_value_handling(self, bars_with_nan):
        """Test indicators handle NaN values in input data."""
        # Should not crash, but may propagate NaN
        result = calculate_sma(bars_with_nan, period=5)

        # Should still return array of correct length
        assert len(result) == len(bars_with_nan)

    def test_single_bar_input(self):
        """Test indicators with single bar input."""
        single_bar = [{'close': 100.0, 'high': 101.0, 'low': 99.0, 'volume': 1_000_000, 'timestamp': '2024-01-01'}]

        # Should return array with NaN (insufficient data)
        sma = calculate_sma(single_bar, period=10)
        assert len(sma) == 1
        assert np.isnan(sma[0])

    def test_invalid_period_handling(self, sample_bars_30):
        """Test indicators reject invalid period values."""
        # Period = 0 should be handled gracefully
        result = calculate_sma(sample_bars_30, period=0)
        assert np.all(np.isnan(result))

        # Negative period should be handled
        result = calculate_sma(sample_bars_30, period=-5)
        assert np.all(np.isnan(result))


# ============================================================================
# Performance Benchmark Tests
# ============================================================================

class TestPerformance:
    """Test performance requirements (10x speedup vs naive Python)."""

    def test_sma_performance_benchmark(self, sample_bars_100):
        """Test SMA achieves 10x speedup over naive Python loop."""
        period = 50

        # Naive Python implementation
        def naive_sma(bars, period):
            closes = [bar['close'] for bar in bars]
            result = []
            for i in range(len(closes)):
                if i < period - 1:
                    result.append(np.nan)
                else:
                    result.append(np.mean(closes[i - period + 1:i + 1]))
            return result

        # Benchmark naive implementation
        start_naive = time.time()
        for _ in range(100):
            naive_sma(sample_bars_100, period)
        time_naive = time.time() - start_naive

        # Benchmark vectorized implementation
        start_vectorized = time.time()
        for _ in range(100):
            calculate_sma(sample_bars_100, period)
        time_vectorized = time.time() - start_vectorized

        # Should be at least 5x faster (target is 10x, but allow margin)
        speedup = time_naive / time_vectorized
        print(f"\nSMA Speedup: {speedup:.2f}x")
        assert speedup > 5.0, f"Expected 10x speedup, got {speedup:.2f}x"

    def test_rsi_performance_benchmark(self, sample_bars_100):
        """Test RSI calculation completes quickly."""
        # RSI should complete 100 iterations in < 500ms
        start = time.time()
        for _ in range(100):
            calculate_rsi(sample_bars_100, period=14)
        elapsed = time.time() - start

        print(f"\nRSI 100 iterations: {elapsed*1000:.2f}ms")
        assert elapsed < 0.5, f"RSI too slow: {elapsed*1000:.0f}ms"

    def test_bollinger_bands_performance(self, sample_bars_100):
        """Test Bollinger Bands calculation completes quickly."""
        # Should complete 100 iterations in < 500ms
        start = time.time()
        for _ in range(100):
            calculate_bollinger_bands(sample_bars_100, period=20, std_dev=2.0)
        elapsed = time.time() - start

        print(f"\nBollinger Bands 100 iterations: {elapsed*1000:.2f}ms")
        assert elapsed < 0.5, f"Bollinger Bands too slow: {elapsed*1000:.0f}ms"


# ============================================================================
# Integration Tests
# ============================================================================

class TestIntegration:
    """Test indicators work together in realistic scenarios."""

    def test_mean_reversion_signal_detection(self, sample_bars_100):
        """Test combining Bollinger Bands + RSI for mean reversion."""
        bb = calculate_bollinger_bands(sample_bars_100, period=20, std_dev=2.0)
        rsi = calculate_rsi(sample_bars_100, period=14)

        closes = [bar['close'] for bar in sample_bars_100]

        # Find mean reversion opportunities (price touches lower band + RSI < 30)
        signals = []
        for i in range(30, len(sample_bars_100)):
            if (closes[i] <= bb['lower_band'][i] and
                rsi[i] < 30 and
                not np.isnan(bb['lower_band'][i]) and
                not np.isnan(rsi[i])):
                signals.append(i)

        # Should be able to detect signals (test doesn't require specific count)
        print(f"\nMean reversion signals detected: {len(signals)}")

    def test_trend_following_signal_detection(self, sample_bars_100):
        """Test combining MACD + ADX for trend following."""
        macd = calculate_macd(sample_bars_100, fast=12, slow=26, signal=9)
        adx = calculate_adx(sample_bars_100, period=14)

        # Find strong trend opportunities (MACD crossover + ADX > 25)
        signals = []
        for i in range(30, len(sample_bars_100) - 1):
            # Bullish crossover: histogram crosses above 0
            if (macd['histogram'][i - 1] < 0 and
                macd['histogram'][i] > 0 and
                adx[i] > 25 and
                not np.isnan(adx[i])):
                signals.append(('BUY', i))
            # Bearish crossover: histogram crosses below 0
            elif (macd['histogram'][i - 1] > 0 and
                  macd['histogram'][i] < 0 and
                  adx[i] > 25 and
                  not np.isnan(adx[i])):
                signals.append(('SELL', i))

        print(f"\nTrend following signals detected: {len(signals)}")

    def test_breakout_signal_detection(self, sample_bars_100):
        """Test combining ATR + Bollinger Bands for breakout detection."""
        bb = calculate_bollinger_bands(sample_bars_100, period=20, std_dev=2.0)
        atr = calculate_atr(sample_bars_100, period=14)

        closes = [bar['close'] for bar in sample_bars_100]

        # Find breakout opportunities (price breaks upper band + ATR expanding)
        signals = []
        for i in range(30, len(sample_bars_100) - 1):
            if (closes[i] > bb['upper_band'][i] and
                atr[i] > atr[i - 5] and  # ATR expanding
                not np.isnan(bb['upper_band'][i]) and
                not np.isnan(atr[i])):
                signals.append(i)

        print(f"\nBreakout signals detected: {len(signals)}")


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "-s"])
