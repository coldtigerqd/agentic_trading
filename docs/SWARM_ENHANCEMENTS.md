# Swarm Intelligence Enhancements Guide

This document provides comprehensive guidance on using the enhanced Swarm Intelligence system, including new strategy templates, technical indicators library, and automated watchlist management.

## Table of Contents

1. [Overview](#overview)
2. [Technical Indicators Library](#technical-indicators-library)
3. [New Strategy Templates](#new-strategy-templates)
4. [Watchlist Manager](#watchlist-manager)
5. [Integration Examples](#integration-examples)
6. [Sentiment Analysis (Optional)](#sentiment-analysis)

---

## Overview

The Swarm Intelligence system has been enhanced with:

- **15 Technical Indicators**: Vectorized NumPy implementations for 10x+ performance
- **3 New Strategy Templates**: Mean Reversion, Breakout Scout, Correlation Arbitrage
- **Automated Watchlist Manager**: Performance-based symbol rotation with sector diversification
- **Sentiment MCP Integration**: News and Twitter sentiment analysis (optional)

### System Architecture

```
Commander Agent
    ↓
Swarm Intelligence (5 concurrent strategies)
    ├── Vol Sniper (earnings volatility)
    ├── Trend Scout (momentum breakouts)
    ├── Mean Reversion (range-bound markets)
    ├── Breakout Scout (volatility squeezes)
    └── Correlation Arbitrage (pairs trading)
         ↓
Technical Indicators Library (15 functions)
         ↓
Market Data (3-year cache, 5-min bars)
         ↓
Watchlist Manager (auto-rotation)
```

---

## Technical Indicators Library

### Location
`skills/technical_indicators.py`

### Performance
- **18.7x speedup** for SMA (exceeds 10x requirement)
- All functions use NumPy vectorization
- Handles edge cases (NaN, empty arrays, insufficient data)

### Available Functions

#### Moving Averages
```python
from skills import calculate_sma, calculate_ema, calculate_wma

# Simple Moving Average
sma = calculate_sma(bars, period=20, field='close')
# Result: np.ndarray with NaN for first (period-1) values

# Exponential Moving Average (with NaN-aware initialization)
ema = calculate_ema(bars, period=12, field='close')

# Weighted Moving Average
wma = calculate_wma(bars, period=10, field='close')
```

#### Momentum Indicators
```python
from skills import calculate_rsi, calculate_macd, calculate_stochastic

# RSI (Wilder's smoothing)
rsi = calculate_rsi(bars, period=14)
# Returns: np.ndarray (0-100 scale)
# Edge case: Constant price returns 50.0 (neutral)

# MACD
macd = calculate_macd(bars, fast=12, slow=26, signal=9)
# Returns: {'macd_line': ndarray, 'signal_line': ndarray, 'histogram': ndarray}

# Stochastic Oscillator
stoch = calculate_stochastic(bars, k_period=14, d_period=3)
# Returns: {'k_line': ndarray, 'd_line': ndarray}
```

#### Volatility Indicators
```python
from skills import (
    calculate_bollinger_bands,
    calculate_atr,
    calculate_historical_volatility
)

# Bollinger Bands
bb = calculate_bollinger_bands(bars, period=20, std_dev=2.0)
# Returns: {
#     'upper_band': ndarray,
#     'middle_band': ndarray (SMA),
#     'lower_band': ndarray,
#     'bandwidth': ndarray  # Normalized (upper-lower)/middle
# }

# ATR (Wilder's smoothing)
atr = calculate_atr(bars, period=14)
# Returns: np.ndarray

# Historical Volatility (annualized)
hv = calculate_historical_volatility(bars, period=20)
# Returns: np.ndarray (annualized std dev of returns)
```

#### Trend Detection
```python
from skills import calculate_adx, detect_trend

# ADX (Average Directional Index)
adx = calculate_adx(bars, period=14)
# Returns: np.ndarray
# ADX > 25: Strong trend
# ADX < 20: Weak trend / ranging

# Trend Classification
trend = detect_trend(bars, sma_short=20, sma_long=50)
# Returns: str
# Options: "STRONG_UPTREND", "WEAK_UPTREND", "SIDEWAYS",
#          "WEAK_DOWNTREND", "STRONG_DOWNTREND"
```

#### Support/Resistance
```python
from skills import find_swing_highs, find_swing_lows, calculate_pivot_points

# Swing Points
highs = find_swing_highs(bars, window=5, min_bars=10)
# Returns: List[float] (sorted descending)

lows = find_swing_lows(bars, window=5, min_bars=10)
# Returns: List[float] (sorted ascending)

# Pivot Points (for single bar or latest bar)
pivots = calculate_pivot_points(bars)
# Returns: {
#     'pivot': float,
#     'r1': float, 'r2': float, 'r3': float,
#     's1': float, 's2': float, 's3': float
# }
```

#### Volume Indicators
```python
from skills import calculate_obv, calculate_vwap

# On-Balance Volume
obv = calculate_obv(bars)
# Returns: np.ndarray (cumulative volume based on price direction)

# VWAP
vwap = calculate_vwap(bars)
# Returns: np.ndarray (volume-weighted average price)
```

### Input Format

All technical indicator functions expect bars in this format:

```python
bars = [
    {
        'timestamp': '2025-11-20T09:30:00',
        'open': 150.5,
        'high': 151.2,
        'low': 150.1,
        'close': 150.8,
        'volume': 1000000
    },
    # ... more bars
]
```

### Error Handling

- **Empty arrays**: Return empty np.ndarray or default dict
- **Insufficient data**: Return NaN arrays with warnings
- **Invalid periods**: Validate period > 0
- **NaN values**: Use `np.nanmean`, `np.nanstd` where applicable

---

## New Strategy Templates

### 1. Mean Reversion

**Location**: `swarm_intelligence/templates/mean_reversion.md`
**Instance**: `swarm_intelligence/active_instances/mean_reversion_spx.json`

**Target Markets**: Range-bound, low volatility environments (ADX < 25)

**Strategy Logic**:
1. Detect range with ADX < max_adx (typically 20-25)
2. Measure BB position and RSI extremes
3. Validate range stability over min_range_days
4. Recommend Iron Condors (neutral) or credit spreads (extremes)

**Configuration Example**:
```json
{
  "template": "mean_reversion",
  "name": "mean_reversion_spx",
  "priority": 6,
  "enabled": true,
  "parameters": {
    "symbol_pool": ["SPY", "QQQ", "IWM", "DIA", "XLF", "XLE", "XLK", "XLV"],
    "max_adx": 25,
    "bb_period": 20,
    "bb_std_dev": 2.0,
    "rsi_period": 14,
    "rsi_oversold": 30,
    "rsi_overbought": 70,
    "min_range_days": 10
  }
}
```

**Signals**:
- **IRON_CONDOR**: Neutral range (ADX < 20, BB position 0.4-0.6, RSI 40-60)
- **SHORT_CALL_SPREAD**: Overbought extreme (BB > 0.9, RSI > 70)
- **SHORT_PUT_SPREAD**: Oversold extreme (BB < 0.1, RSI < 30)
- **NO_TRADE**: Trending market or insufficient range

---

### 2. Breakout Scout

**Location**: `swarm_intelligence/templates/breakout_scout.md`
**Instance**: `swarm_intelligence/active_instances/breakout_scout_tech.json`

**Target Markets**: Volatility compression followed by explosive moves

**Strategy Logic**:
1. Detect volatility contraction (ATR decline >= atr_contraction_pct, BB squeeze)
2. Identify consolidation pattern (min_consolidation_days)
3. Wait for breakout with volume confirmation (volume_multiplier)
4. Use breakout_confirm_bars for false breakout filtering
5. Confirm with RSI and OBV momentum
6. Calculate targets using ATR and range projection
7. Require Risk:Reward >= 2:1

**Configuration Example**:
```json
{
  "template": "breakout_scout",
  "name": "breakout_scout_tech",
  "priority": 7,
  "enabled": true,
  "parameters": {
    "symbol_pool": ["NVDA", "TSLA", "AMD", "META", "GOOGL", "AMZN", "NFLX", "AAPL"],
    "atr_contraction_pct": 30,
    "bb_squeeze_threshold": 0.10,
    "volume_multiplier": 1.5,
    "min_consolidation_days": 5,
    "breakout_confirm_bars": 2
  }
}
```

**Signals**:
- **LONG_CALL_SPREAD**: Bullish breakout (price > consolidation_high, volume spike, RSI > 50)
- **LONG_PUT_SPREAD**: Bearish breakdown (price < consolidation_low, volume spike, RSI < 50)
- **NO_TRADE**: No squeeze, poor R:R, or insufficient confirmation

---

### 3. Correlation Arbitrage

**Location**: `swarm_intelligence/templates/correlation_arbitrage.md`
**Instance**: `swarm_intelligence/active_instances/correlation_arb_tech_pairs.json`

**Target Markets**: Statistical arbitrage on correlated pairs

**Strategy Logic**:
1. Calculate Pearson correlation (requires >= min_correlation)
2. Determine hedge ratio via linear regression (capped at max_hedge_ratio)
3. Calculate z-score of spread deviation
4. Enter when |z-score| >= zscore_threshold (typically 2.0)
5. Confirm with RSI and Bollinger Band divergence
6. Validate correlation stability (std < 0.15 over min_stability_days)
7. Check for opposing trends (avoid correlation breakdown)
8. Measure historical reversion rate (require > 70%)

**Configuration Example**:
```json
{
  "template": "correlation_arbitrage",
  "name": "correlation_arb_tech_pairs",
  "priority": 8,
  "enabled": true,
  "parameters": {
    "symbol_pairs": [
      ["AAPL", "MSFT"],
      ["NVDA", "AMD"],
      ["GOOGL", "META"],
      ["AMZN", "SHOP"],
      ["TSM", "INTC"]
    ],
    "min_correlation": 0.7,
    "zscore_threshold": 2.0,
    "lookback_days": 90,
    "min_stability_days": 30,
    "max_hedge_ratio": 2.0
  }
}
```

**Signals**:
- **LONG_SHORT_COMBO**: Symbol A overvalued (z-score > 2.0, long B, short A)
- **SHORT_LONG_COMBO**: Symbol A undervalued (z-score < -2.0, long A, short B)
- **NO_TRADE**: Weak correlation, unstable, or poor reversion history

---

## Watchlist Manager

### Location
`skills/watchlist_manager.py`

### Purpose
Automatically rotate watchlist symbols based on trading performance while enforcing sector diversification and stability constraints.

### Core Functions

#### 1. Calculate Symbol Score
```python
from skills import calculate_symbol_score

# Score a symbol based on 30-day performance
score_data = calculate_symbol_score(
    symbol="AAPL",
    lookback_days=30  # Default: 30
)

# Returns:
{
    "symbol": "AAPL",
    "score": 72.5,  # Composite score 0-100
    "sharpe_ratio": 1.8,
    "win_rate": 0.65,  # 65% win rate
    "avg_pnl": 120.50,  # Average P&L per trade
    "trade_count": 15,
    "sector": "Technology",
    "days_tracked": 30,
    "has_min_trades": True  # >= 5 trades
}
```

**Scoring Formula** (0-100 scale):
- Sharpe ratio: 40% weight (normalized: -3 to +3 → 0 to 100)
- Win rate: 30% weight (0% to 100% → 0 to 100)
- Avg P&L: 20% weight (-$500 to +$500 → 0 to 100)
- Trade frequency: 10% weight (0 to 20 trades → 0 to 100)

#### 2. Update Watchlist
```python
from skills import update_watchlist

# Rotate underperformers with top candidates
result = update_watchlist(
    candidate_pool=["SPY", "QQQ", "AAPL", "NVDA", "AMD", "TSLA"],
    max_watchlist_size=20,  # Default: 20
    lookback_days=30,  # Default: 30
    enforce_sector_limits=True  # Default: True
)

# Returns:
{
    "added": ["NVDA", "AMD"],  # New symbols added
    "removed": ["LOSER1", "LOSER2"],  # Underperformers removed
    "scores": {...},  # All symbol scores
    "churn_limit_reached": False,
    "sector_distribution": {
        "Technology": 6,
        "Financial": 3,
        "Energy": 2,
        "Broad Market": 4,
        ...
    }
}
```

**Rotation Logic**:
1. Score all current watchlist symbols
2. Identify bottom 20% performers (with >= 5 trades)
3. Score candidate pool
4. Replace underperformers with top candidates
5. Enforce sector limit (max 30% per sector)
6. Enforce churn limit (max 3 changes per week)

#### 3. Get Performance Report
```python
from skills import get_watchlist_performance_report

report = get_watchlist_performance_report(lookback_days=30)

# Returns:
{
    "symbol_scores": [  # Sorted by score (descending)
        {"symbol": "AAPL", "score": 85.2, ...},
        {"symbol": "NVDA", "score": 78.5, ...},
        ...
    ],
    "avg_score": 68.5,
    "total_trades": 250,
    "sector_distribution": {"Technology": 8, ...},
    "underperformers": ["SYM1", "SYM2"],  # Bottom 20%
    "top_performers": ["AAPL", "NVDA"]  # Top 20%
}
```

### Configuration Constants

Located in `skills/watchlist_manager.py`:

```python
MIN_TRADES_FOR_SCORING = 5  # Minimum trades for valid score
ROTATION_PCT = 0.20  # Bottom 20% eligible for rotation
MAX_CHURN_PER_WEEK = 3  # Max symbol changes per week
MAX_SECTOR_PCT = 0.30  # Max 30% concentration per sector

# Composite score weights
SHARPE_WEIGHT = 0.40  # 40%
WIN_RATE_WEIGHT = 0.30  # 30%
AVG_PNL_WEIGHT = 0.20  # 20%
FREQ_WEIGHT = 0.10  # 10%
```

### Sector Mapping

The watchlist manager includes sector mappings for 40+ symbols:

```python
SECTOR_MAP = {
    # Broad Market
    "SPY": "Broad Market",
    "QQQ": "Technology",
    "IWM": "Broad Market",

    # Sector ETFs
    "XLF": "Financial",
    "XLE": "Energy",
    "XLK": "Technology",
    "XLV": "Healthcare",
    # ... more sectors

    # Tech Stocks
    "AAPL": "Technology",
    "NVDA": "Technology",
    "TSLA": "Consumer Discretionary",
    # ... more stocks
}
```

**Unknown symbols** default to sector "Other".

### Weekly Rotation Workflow

**Recommended schedule**: Every Friday at market close

```python
from skills import update_watchlist, get_watchlist_performance_report

# 1. Get current performance
report = get_watchlist_performance_report(lookback_days=7)

print(f"Average score: {report['avg_score']}")
print(f"Underperformers: {report['underperformers']}")

# 2. Define candidate pool (from Swarm recommendations or predefined list)
candidates = [
    "AAPL", "MSFT", "NVDA", "AMD", "TSLA",
    "GOOGL", "META", "AMZN", "SPY", "QQQ",
    "IWM", "DIA", "XLF", "XLE", "XLK"
]

# 3. Update watchlist
result = update_watchlist(
    candidate_pool=candidates,
    max_watchlist_size=20,
    lookback_days=7,  # Weekly performance
    enforce_sector_limits=True
)

# 4. Log results
print(f"Added: {result['added']}")
print(f"Removed: {result['removed']}")
print(f"Sector distribution: {result['sector_distribution']}")
```

---

## Integration Examples

### Example 1: Using Technical Indicators in Swarm Template

```python
# In swarm_intelligence/templates/custom_strategy.md

from skills import (
    get_historical_bars,
    calculate_sma,
    calculate_rsi,
    calculate_bollinger_bands,
    detect_trend
)

# Fetch data
bars = get_historical_bars(symbol="{{ symbol }}", interval="daily", lookback_days=60)

# Calculate indicators
sma_20 = calculate_sma(bars, period=20)
sma_50 = calculate_sma(bars, period=50)
rsi = calculate_rsi(bars, period=14)
bb = calculate_bollinger_bands(bars, period=20, std_dev=2.0)

# Automated trend detection
trend = detect_trend(bars, sma_short=20, sma_long=50)
# Returns: "STRONG_UPTREND", "WEAK_UPTREND", "SIDEWAYS", etc.

# Generate signal
if trend == "STRONG_UPTREND" and rsi[-1] < 70:
    signal = "LONG_CALL_SPREAD"
elif trend == "STRONG_DOWNTREND" and rsi[-1] > 30:
    signal = "LONG_PUT_SPREAD"
else:
    signal = "NO_TRADE"
```

### Example 2: Commander Workflow with Watchlist Manager

```python
# In prompts/commander_system_prompt.md

from skills import (
    get_watchlist_performance_report,
    update_watchlist,
    consult_swarm
)

# Step 1: Get watchlist performance
report = get_watchlist_performance_report(lookback_days=7)

# Step 2: Check if weekly rotation is needed (Fridays)
if today_is_friday():
    # Get Swarm recommendations for new candidates
    swarm_results = consult_swarm()

    # Extract symbols with high confidence
    high_confidence_symbols = [
        r["target"] for r in swarm_results
        if r["confidence"] > 0.75 and r["signal"] != "NO_TRADE"
    ]

    # Add to candidate pool
    candidates = high_confidence_symbols + [
        "SPY", "QQQ", "IWM", "DIA"  # Core holdings
    ]

    # Rotate watchlist
    rotation_result = update_watchlist(
        candidate_pool=candidates,
        max_watchlist_size=20,
        lookback_days=7,
        enforce_sector_limits=True
    )

    # Log rotation
    if rotation_result["added"]:
        log(f"Watchlist rotation: Added {rotation_result['added']}, "
            f"Removed {rotation_result['removed']}")
```

### Example 3: Sentiment-Enhanced Strategy

```python
# Using news-sentiment MCP (if available)

from skills import get_historical_bars, calculate_rsi

# Get technical analysis
bars = get_historical_bars("AAPL", interval="daily", lookback_days=30)
rsi = calculate_rsi(bars, period=14)

# Get sentiment (via MCP)
# Assume MCP tool: get_news_sentiment(symbol)
sentiment = get_news_sentiment("AAPL")

# Combine technical + sentiment
if rsi[-1] < 30 and sentiment["score"] > 0.5:
    # Oversold + positive sentiment = strong buy signal
    signal = "LONG_CALL_SPREAD"
    confidence = 0.85
elif rsi[-1] > 70 and sentiment["score"] < -0.5:
    # Overbought + negative sentiment = strong sell signal
    signal = "LONG_PUT_SPREAD"
    confidence = 0.85
else:
    # Technical and sentiment conflict
    signal = "NO_TRADE"
    confidence = 0.0
```

---

## Sentiment Analysis (Optional)

### MCP Server Location
`mcp-servers/news-sentiment/`

### Features
1. **News Sentiment**: LLM-powered sentiment scoring (-1 to +1)
2. **Twitter/X Sentiment**: Real-time social sentiment tracking
3. **Event Calendar**: Earnings dates, economic events (FOMC, CPI, GDP)

### Setup

#### 1. Install Dependencies
```bash
cd mcp-servers/news-sentiment
pip install requests anthropic
```

#### 2. Set API Keys
```bash
export SERPER_API_KEY="your-serper-key"  # For news
export ANTHROPIC_API_KEY="your-anthropic-key"  # For sentiment scoring
export TWITTER_BEARER_TOKEN="your-twitter-token"  # Optional
```

#### 3. Configure MCP Client
Add to Claude Code MCP configuration:

```json
{
  "mcpServers": {
    "news-sentiment": {
      "command": "python",
      "args": ["/path/to/mcp-servers/news-sentiment/server.py"],
      "env": {
        "SERPER_API_KEY": "your-key",
        "ANTHROPIC_API_KEY": "your-key"
      }
    }
  }
}
```

### Usage

#### Get News Sentiment
```python
# MCP tool call
result = get_news_sentiment(symbol="AAPL", max_articles=10)

# Returns:
{
    "symbol": "AAPL",
    "overall_sentiment": 0.65,  # -1 to +1 scale
    "sentiment_trend": "improving",  # improving/stable/deteriorating
    "article_count": 10,
    "top_headlines": [
        {
            "title": "Apple announces new iPhone...",
            "source": "TechCrunch",
            "sentiment": 0.8,
            "date": "2025-11-19"
        },
        ...
    ]
}
```

#### Get Twitter Sentiment
```python
result = get_twitter_sentiment(symbol="TSLA")

# Returns:
{
    "symbol": "TSLA",
    "overall_sentiment": -0.3,
    "influencer_sentiment": 0.1,  # Accounts > 10K followers
    "sentiment_spike": False,
    "tweet_count": 5000
}
```

#### Get Event Calendar
```python
result = get_event_calendar(symbol="AAPL")

# Returns:
{
    "symbol": "AAPL",
    "earnings_date": "2025-12-15",
    "days_until_earnings": 25,
    "upcoming_economic_events": [
        {
            "event": "FOMC Meeting",
            "date": "2025-12-01",
            "impact": "high",
            "days_until": 11
        },
        ...
    ]
}
```

---

## Testing

### Run All Tests
```bash
# Technical indicators (40 tests)
python -m pytest tests/test_technical_indicators.py -v

# Watchlist manager (27 tests)
python -m pytest tests/test_watchlist_manager.py -v

# All tests
python -m pytest tests/ -v
```

### Performance Benchmarks

From `tests/test_technical_indicators.py`:

```
SMA Performance: 18.7x speedup (naive: 1.2ms, vectorized: 0.064ms)
Target: 10x minimum ✓ PASSED
```

---

## Troubleshooting

### Issue: "Insufficient data for indicator calculation"

**Solution**: Ensure bars array has enough data points
```python
# For SMA(20), need at least 20 bars
bars = get_historical_bars(symbol, interval="daily", lookback_days=30)
```

### Issue: "Churn limit reached"

**Solution**: Wait until next week or adjust MAX_CHURN_PER_WEEK
```python
# Check recent churn
from skills.watchlist_manager import get_recent_churn

churn = get_recent_churn(days=7)
print(f"Recent changes: {churn}/3")
```

### Issue: "Sector limit exceeded"

**Solution**: Diversify candidate pool across sectors
```python
# Ensure candidates span multiple sectors
candidates = [
    "AAPL",  # Technology
    "XLE",   # Energy
    "JPM",   # Financial
    "SPY"    # Broad Market
]
```

---

## Performance Metrics

### Technical Indicators
- **Vectorization speedup**: 18.7x for SMA (target: 10x)
- **Test coverage**: 40 tests, 100% pass rate
- **Edge case handling**: Empty arrays, NaN values, insufficient data

### Watchlist Manager
- **Composite scoring**: 4-factor weighted average
- **Rotation efficiency**: Bottom 20% identification in O(n log n)
- **Test coverage**: 27 tests, 100% pass rate
- **Sector enforcement**: Max 30% concentration per sector

### Swarm Templates
- **Total strategies**: 5 (Vol Sniper, Trend Scout, Mean Reversion, Breakout Scout, Correlation Arbitrage)
- **Concurrent execution**: All 5 strategies run in parallel
- **Priority scoring**: 6-10 (higher priority evaluated first)

---

## Summary

The enhanced Swarm Intelligence system provides:

1. **Comprehensive Technical Analysis**: 15 vectorized indicators with 10x+ performance
2. **Diverse Strategy Coverage**: 5 concurrent strategies spanning volatility, trends, ranges, breakouts, and statistical arbitrage
3. **Intelligent Portfolio Management**: Automated watchlist rotation with sector diversification
4. **Optional Sentiment Integration**: News and Twitter sentiment via MCP

All enhancements are fully tested, documented, and integrated into the existing Commander workflow.
