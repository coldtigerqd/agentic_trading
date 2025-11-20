# technical-indicators Specification

## Purpose
TBD - created by archiving change enhance-swarm-intelligence. Update Purpose after archive.
## Requirements
### Requirement: Moving Average Calculations

The system MUST provide simple, exponential, and weighted moving average calculations using NumPy vectorization.

**Priority:** MUST
**Impact:** Core functionality for all strategy templates

#### Scenario: Calculate 20-period SMA for daily bars

**Given** 30 days of OHLCV price data
**When** the system calculates `calculate_sma(bars, period=20)`
**Then** it SHALL return an array of 30 values where:
- First 19 values are NaN (insufficient data)
- Values 20-30 are the arithmetic mean of the prior 20 close prices
- Calculation uses NumPy vectorization (no Python loops)
- Result accuracy matches reference implementation (TA-Lib) within 0.01%

---

### Requirement: Momentum Indicator Calculations

The system MUST provide RSI, MACD, and Stochastic oscillator calculations for momentum analysis.

**Priority:** MUST
**Impact:** Required for entry timing in all strategies

#### Scenario: Calculate 14-period RSI for trend detection

**Given** 50 days of OHLCV price data
**When** the system calculates `calculate_rsi(bars, period=14)`
**Then** it SHALL return an array where:
- First 14 values are NaN (insufficient data)
- Remaining values are in range [0, 100]
- RSI > 70 indicates overbought conditions
- RSI < 30 indicates oversold conditions
- Calculation follows Wilder's smoothing method
- Handles constant price (returns 50.0, not NaN)

#### Scenario: Calculate MACD with signal line crossover

**Given** 100 days of OHLCV price data
**When** the system calculates `calculate_macd(bars, fast=12, slow=26, signal=9)`
**Then** it SHALL return a dict containing:
- `macd_line`: MACD values (12 EMA - 26 EMA)
- `signal_line`: 9 EMA of MACD line
- `histogram`: MACD line - signal line
- Bullish crossover detected when histogram crosses above 0
- Bearish crossover detected when histogram crosses below 0

---

### Requirement: Volatility Indicator Calculations

The system MUST provide Bollinger Bands, ATR, and historical volatility calculations for risk assessment.

**Priority:** MUST
**Impact:** Critical for position sizing and stop loss placement

#### Scenario: Calculate Bollinger Bands for mean reversion

**Given** 30 days of OHLCV price data
**When** the system calculates `calculate_bollinger_bands(bars, period=20, std_dev=2)`
**Then** it SHALL return a dict containing:
- `upper_band`: SMA(20) + 2 * std_dev(20)
- `middle_band`: SMA(20)
- `lower_band`: SMA(20) - 2 * std_dev(20)
- `bandwidth`: (upper - lower) / middle (volatility metric)
- Price touching lower band signals potential long entry
- Price touching upper band signals potential short entry

#### Scenario: Calculate ATR for stop loss placement

**Given** 14 days of OHLCV price data with varying volatility
**When** the system calculates `calculate_atr(bars, period=14)`
**Then** it SHALL return an array where:
- First value is simple average of first 14 true ranges
- Subsequent values use Wilder's smoothing: ATR = (Prior ATR * 13 + Current TR) / 14
- True Range = max(high - low, abs(high - prior_close), abs(low - prior_close))
- Values represent average price movement in dollars

---

### Requirement: Trend Detection Functions

The system MUST provide trend detection using moving average relationships and ADX calculations.

**Priority:** MUST
**Impact:** Strategy selection depends on accurate trend identification

#### Scenario: Detect strong uptrend using SMA crossover

**Given** 60 days of OHLCV price data in uptrend
**When** the system calls `detect_trend(bars, sma_short=20, sma_long=50)`
**Then** it SHALL return "STRONG_UPTREND" when:
- Current price > SMA(20) > SMA(50)
- SMA(20) slope is positive (rising)
- At least 10 consecutive days of this configuration

**And** SHALL return "WEAK_UPTREND" when:
- Current price > SMA(20) but SMA(20) ≈ SMA(50) (within 2%)

**And** SHALL return "SIDEWAYS" when:
- SMA(20) and SMA(50) flat (slope < 0.5% over 10 days)

---

### Requirement: Support and Resistance Detection

The system MUST identify swing highs, swing lows, and pivot points for key price levels.

**Priority:** MUST
**Impact:** Enables precise strike selection at technical levels

#### Scenario: Find swing highs for resistance levels

**Given** 30 days of OHLCV price data
**When** the system calls `find_swing_highs(bars, window=5)`
**Then** it SHALL return an array of prices where:
- Each value is a local maximum within ±5 bars window
- Price[i] > all prices in range [i-5, i+5]
- Results sorted in descending order (highest resistance first)
- Minimum 3 touches required to confirm resistance level

#### Scenario: Calculate daily pivot points

**Given** yesterday's OHLC data
**When** the system calls `calculate_pivot_points(bars[-1])`
**Then** it SHALL return a dict containing:
- `pivot`: (High + Low + Close) / 3
- `r1`: 2 * pivot - Low
- `r2`: pivot + (High - Low)
- `s1`: 2 * pivot - High
- `s2`: pivot - (High - Low)
- All values in dollars (price levels)

---

### Requirement: Edge Case Handling

The system MUST handle edge cases gracefully without crashing or producing invalid results.

**Priority:** MUST
**Impact:** System stability under real-world conditions

#### Scenario: Handle insufficient data gracefully

**Given** only 5 days of OHLCV price data
**When** the system attempts to calculate `calculate_sma(bars, period=20)`
**Then** it SHALL:
- Return an array of 5 NaN values
- Log warning: "Insufficient data for SMA(20): need 20 bars, got 5"
- NOT raise an exception
- Allow strategy to handle NaN values (typically return NO_TRADE)

#### Scenario: Handle NaN values in input data

**Given** 30 days of price data with NaN gaps (missing bars)
**When** the system calculates any indicator
**Then** it SHALL:
- Skip NaN values in calculations (use `np.nanmean`, `np.nanstd`)
- Propagate NaN forward if gap exceeds indicator period
- Set quality flag to indicate degraded data
- Never return -inf, +inf, or invalid numeric values

---

### Requirement: Performance Optimization

The system MUST use NumPy vectorization to achieve 10x speedup over naive Python loops.

**Priority:** MUST
**Impact:** Enables real-time analysis of 50+ symbols concurrently

#### Scenario: Benchmark SMA calculation performance

**Given** 1000 days of OHLCV price data
**When** the system calculates `calculate_sma(bars, period=50)` 100 times
**Then** it SHALL complete in <100ms total (1ms per calculation)
**And** SHALL be at least 10x faster than naive Python loop implementation
**And** SHALL use <10MB memory (no array copies)

---

