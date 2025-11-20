# Design Document: Enhanced Swarm Intelligence

**Change ID:** `enhance-swarm-intelligence`
**Date:** 2025-11-20

---

## Architecture Overview

This enhancement builds on the market data cache to enable sophisticated multi-strategy trading across all market regimes.

```
┌─────────────────────────────────────────────────────────────┐
│                      Commander (Claude Code)                 │
│  - Strategy selection based on market regime                │
│  - Watchlist update decisions                               │
│  - Sentiment filter integration                             │
└───────────────────┬─────────────────────────────────────────┘
                    │
         ┌──────────▼──────────┐
         │   Swarm Core Skill   │
         │  - Concurrent agents  │
         │  - Signal aggregation │
         └──┬────────┬────────┬─┘
            │        │        │
    ┌───────▼──┐ ┌──▼───────┐ ┌▼──────────────┐
    │Vol Sniper│ │Trend Scout│ │Mean Reversion │ (NEW)
    └──────────┘ └───────────┘ └───────────────┘
    ┌──────────────┐ ┌────────────────────┐
    │Breakout Scout│ │Correlation Arb     │ (NEW)
    └──────────────┘ └────────────────────┘
            │                │
    ┌───────▼────────────────▼──────────┐
    │  Technical Indicators Library      │ (NEW)
    │  - SMA, EMA, RSI, MACD, BBands    │
    │  - ATR, Stochastic, ADX, etc.     │
    │  - Optimized NumPy calculations   │
    └───────────────────────────────────┘
            │
    ┌───────▼──────────────────┐
    │  Market Data Cache        │
    │  - 3-year OHLCV history   │
    │  - Multi-timeframe query  │
    └───────────────────────────┘

    ┌────────────────────────────────┐
    │  Watchlist Manager (NEW)        │
    │  - Performance tracking         │
    │  - Automatic rotation           │
    │  - Top 20% prioritization      │
    └────────────────────────────────┘

    ┌────────────────────────────────┐
    │  Sentiment Filter (NEW)         │
    │  - News event detection         │
    │  - Earnings blackout            │
    │  - Major announcement avoid     │
    └────────────────────────────────┘
```

---

## Component Design

### 1. Technical Indicators Library

**File:** `skills/technical_indicators.py`

**Design Principles:**
- Pure functions (no side effects)
- NumPy vectorization for performance
- Graceful NaN handling at boundaries
- Clear docstrings with formula references

**Core Functions:**

```python
# Moving Averages
def calculate_sma(bars: List[Dict], period: int) -> List[float]
def calculate_ema(bars: List[Dict], period: int) -> List[float]
def calculate_wma(bars: List[Dict], period: int) -> List[float]

# Momentum Indicators
def calculate_rsi(bars: List[Dict], period: int = 14) -> List[float]
def calculate_macd(bars: List[Dict], fast=12, slow=26, signal=9) -> Dict
def calculate_stochastic(bars: List[Dict], k_period=14, d_period=3) -> Dict

# Volatility Indicators
def calculate_bollinger_bands(bars: List[Dict], period=20, std_dev=2) -> Dict
def calculate_atr(bars: List[Dict], period: int = 14) -> List[float]
def calculate_historical_volatility(bars: List[Dict], period=20) -> float

# Trend Indicators
def calculate_adx(bars: List[Dict], period: int = 14) -> List[float]
def detect_trend(bars: List[Dict], sma_short=20, sma_long=50) -> str

# Support/Resistance
def find_swing_highs(bars: List[Dict], window: int = 5) -> List[float]
def find_swing_lows(bars: List[Dict], window: int = 5) -> List[float]
def calculate_pivot_points(bars: List[Dict]) -> Dict

# Volume Analysis
def calculate_obv(bars: List[Dict]) -> List[float]  # On-Balance Volume
def calculate_vwap(bars: List[Dict]) -> List[float]  # Volume-Weighted Average Price
```

**Performance Optimization:**
- Use NumPy arrays internally (convert from List[Dict] at entry)
- Vectorized operations (no Python loops for calculations)
- Lazy evaluation where possible (don't calculate unused indicators)
- Pre-allocate arrays to avoid memory fragmentation

**Error Handling:**
- Insufficient data: Return NaN array with warning
- Invalid parameters: Raise ValueError with clear message
- Edge cases: Return partial results with quality flag

---

### 2. Mean Reversion Strategy

**Template:** `swarm_intelligence/templates/mean_reversion.md`

**Market Regime:** Range-bound, low volatility, sideways consolidation

**Core Logic:**
1. **Identify Trading Range**:
   - 30-day high/low defines range boundaries
   - Require minimum range width (>5% price range)
   - Reject trending markets (ADX < 25)

2. **Entry Signals**:
   - Price touches lower 2% of range → Buy signal
   - Price touches upper 2% of range → Sell signal
   - RSI confirmation (oversold <30 for buy, overbought >70 for sell)
   - Bollinger Band squeeze (volatility contraction precedes mean reversion)

3. **Position Structure**:
   - **Long at Support**: Buy ATM call spread, sell below support
   - **Short at Resistance**: Sell ATM put spread, buy above resistance
   - Target: Return to 50% range (mean)
   - Exit: Opposite range extreme or 50% profit

4. **Risk Management**:
   - Max risk: 2% account per trade
   - Stop loss: Range breakout (close beyond boundary)
   - Time decay: Exit 7 DTE if not profitable

**Parameters:**
```json
{
  "range_lookback_days": 30,
  "range_min_width_pct": 5.0,
  "entry_threshold_pct": 2.0,
  "rsi_oversold": 30,
  "rsi_overbought": 70,
  "max_adx": 25,
  "target_dte": 30-45
}
```

---

### 3. Breakout Scout Strategy

**Template:** `swarm_intelligence/templates/breakout_scout.md`

**Market Regime:** Consolidation followed by volatility expansion

**Core Logic:**
1. **Consolidation Detection**:
   - 20-day ATR declining (volatility contraction)
   - Price range narrowing (Bollinger Band squeeze)
   - Volume declining below 20-day average

2. **Breakout Confirmation**:
   - Price closes above/below 20-day high/low
   - Volume spike >1.5x average
   - ATR expansion (volatility breakout)
   - Strong directional close (>80% of candle range)

3. **Position Structure**:
   - **Upside Breakout**: Long call spread at breakout level
   - **Downside Breakout**: Long put spread at breakdown level
   - Target: ATR projection (2x recent ATR from breakout)
   - Tight stop: Re-entry into consolidation range

4. **False Breakout Filter**:
   - Wait for 2-hour confirmation (avoid head fakes)
   - Require volume confirmation (not just price)
   - Check multi-timeframe alignment (hourly + daily)

**Parameters:**
```json
{
  "consolidation_days": 10,
  "atr_contraction_threshold": 0.8,
  "volume_breakout_multiplier": 1.5,
  "confirmation_hours": 2,
  "target_atr_multiple": 2.0,
  "target_dte": 21-30
}
```

---

### 4. Correlation Arbitrage Strategy

**Template:** `swarm_intelligence/templates/correlation_arbitrage.md`

**Market Regime:** Temporary divergence in historically correlated pairs

**Core Logic:**
1. **Pair Selection**:
   - Historical correlation >0.7 (60-day rolling)
   - Same sector (XLF components, Tech stocks, etc.)
   - Similar market cap and liquidity

2. **Divergence Detection**:
   - Z-score of price spread >2.0 (2 standard deviations)
   - Correlation remains strong (temporary divergence, not structural break)
   - No major news explaining divergence (sentiment filter)

3. **Position Structure**:
   - **Long underperformer**: Call spread on lagging symbol
   - **Short outperformer**: Put spread on leading symbol
   - Market-neutral: Equal dollar exposure
   - Target: Spread mean reversion (z-score → 0)

4. **Risk Management**:
   - Stop loss: Z-score >3.0 (extreme divergence, may be structural)
   - Time limit: 30 days max holding period
   - Correlation breakdown: Exit if correlation <0.5

**Parameters:**
```json
{
  "correlation_window": 60,
  "min_correlation": 0.7,
  "entry_zscore": 2.0,
  "exit_zscore": 0.5,
  "stop_zscore": 3.0,
  "max_holding_days": 30,
  "target_dte": 45-60
}
```

---

### 5. Automated Watchlist Manager

**File:** `skills/watchlist_manager.py`

**Design Principles:**
- Performance-based rotation (meritocracy)
- Gradual changes (avoid thrashing)
- Diversification enforcement (max 30% per sector)

**Performance Metrics:**
```python
def calculate_symbol_score(symbol: str, lookback_days: int = 90) -> float:
    """Composite score combining multiple factors"""

    # Factor 1: Sharpe Ratio (risk-adjusted return)
    sharpe = calculate_sharpe_ratio(symbol, lookback_days)

    # Factor 2: Win Rate (consistency)
    win_rate = get_win_rate(symbol, lookback_days)

    # Factor 3: Average P&L per trade
    avg_pnl = get_avg_pnl(symbol, lookback_days)

    # Factor 4: Trade frequency (opportunity)
    trade_count = get_trade_count(symbol, lookback_days)

    # Weighted composite score
    score = (
        sharpe * 0.4 +
        win_rate * 0.3 +
        avg_pnl * 0.2 +
        min(trade_count / 10, 1.0) * 0.1
    )

    return score
```

**Rotation Logic:**
```python
def update_watchlist(current_watchlist: List[str], candidates: List[str]) -> Dict:
    """Weekly watchlist update"""

    # Calculate scores for all symbols
    scores = {sym: calculate_symbol_score(sym) for sym in current_watchlist + candidates}

    # Identify underperformers (bottom 20%)
    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    threshold = len(current_watchlist) * 0.2
    underperformers = [sym for sym, score in ranked[-int(threshold):]]

    # Find better candidates
    replacements = []
    for candidate in candidates:
        if candidate not in current_watchlist and scores[candidate] > min(scores[u] for u in underperformers):
            replacements.append(candidate)

    # Limit churn (max 3 changes per week)
    changes = min(3, len(underperformers), len(replacements))

    # Return update recommendation
    return {
        "remove": underperformers[:changes],
        "add": replacements[:changes],
        "reason": "Performance-based rotation (bottom 20% replaced)"
    }
```

**Diversification Constraints:**
```python
def check_sector_balance(watchlist: List[str]) -> bool:
    """Ensure no sector exceeds 30% of watchlist"""
    sector_counts = get_sector_distribution(watchlist)
    max_allowed = len(watchlist) * 0.3

    for sector, count in sector_counts.items():
        if count > max_allowed:
            return False

    return True
```

---

### 6. Sentiment Integration

**Integration Point:** Template-level sentiment filter

**Design:** Graceful degradation if MCP unavailable

```python
# In each strategy template
from skills import get_news_sentiment  # May return None if MCP unavailable

# Before generating signal
sentiment_score = get_news_sentiment(symbol, lookback_hours=24)

if sentiment_score is not None:
    # Apply sentiment filter
    if sentiment_score < -0.5:  # Highly negative news
        return {"signal": "NO_TRADE", "reason": "Negative sentiment filter"}

    # Adjust confidence based on sentiment
    confidence *= (1.0 + sentiment_score * 0.2)  # ±20% adjustment
```

**News Sentiment Skill:**
```python
# skills/sentiment_filter.py
def get_news_sentiment(symbol: str, lookback_hours: int = 24) -> Optional[float]:
    """
    Get aggregated news sentiment score for symbol.

    Returns:
        float in [-1.0, 1.0]: Negative to positive sentiment
        None: If sentiment MCP unavailable (graceful degradation)
    """
    try:
        # Check if sentiment MCP available
        from mcp import news_sentiment

        articles = news_sentiment.get_recent_news(symbol, hours=lookback_hours)
        if not articles:
            return 0.0  # Neutral if no news

        # Aggregate sentiment scores
        scores = [article['sentiment'] for article in articles]
        return sum(scores) / len(scores)

    except ImportError:
        # MCP not available - graceful degradation
        return None
```

---

## Data Flow

### Strategy Execution Flow

```
1. Commander SENSE Phase
   ├─ Get watchlist (updated by watchlist manager)
   ├─ Get market snapshot
   ├─ Get SPY context
   └─ Check news sentiment (if available)

2. Commander THINK Phase
   ├─ Invoke Swarm with market_data + sentiment
   ├─ Each strategy template:
   │   ├─ Get multi-timeframe data from cache
   │   ├─ Calculate indicators (via shared library)
   │   ├─ Apply strategy logic
   │   ├─ Apply sentiment filter (if available)
   │   └─ Return signal + confidence
   └─ Aggregate signals (deduplicate, rank by confidence)

3. Commander DECIDE Phase
   ├─ Evaluate aggregated signals
   ├─ Check watchlist update recommendations
   └─ Select best signal considering:
       ├─ Signal confidence
       ├─ Current portfolio exposure
       ├─ Risk limits
       └─ Market regime alignment

4. Commander ACT Phase
   ├─ Execute selected signal (if any)
   └─ Process watchlist updates (if recommended)

5. Post-Trade
   ├─ Log trade to database
   ├─ Update performance metrics
   └─ Trigger watchlist evaluation (weekly)
```

---

## Testing Strategy

### Unit Tests

**Technical Indicators:**
- Edge cases: Empty arrays, insufficient data, NaN values
- Accuracy: Compare against known reference implementations (TA-Lib)
- Performance: Benchmark against naive Python loops (expect 10x speedup)

**Watchlist Manager:**
- Rotation logic: Verify top/bottom 20% identification
- Diversification: Ensure sector constraints enforced
- Churn limits: Max 3 changes per week respected

**Sentiment Filter:**
- Graceful degradation: Handle missing MCP gracefully
- Score aggregation: Verify weighted average calculation
- Threshold logic: Confirm trade blocking at <-0.5

### Integration Tests

**Strategy Templates:**
- Template rendering: Jinja2 substitution with sample parameters
- Signal generation: Valid JSON output for all market conditions
- Indicator usage: Correct library function calls

**End-to-End Workflow:**
- Full Commander cycle with 5 strategies
- Watchlist update after 90 days of simulated trading
- Sentiment filter blocking trade during earnings

---

## Migration Plan

### Phase 1: Indicator Library (Week 1)
1. Implement `skills/technical_indicators.py`
2. Write comprehensive unit tests (100+ test cases)
3. Benchmark performance (NumPy vs pure Python)

### Phase 2: Template Refactor (Week 1-2)
1. Refactor Vol Sniper to use indicator library
2. Refactor Trend Scout to use indicator library
3. Verify backward compatibility (identical signals)

### Phase 3: New Strategies (Week 2-3)
1. Implement Mean Reversion template + instance config
2. Implement Breakout Scout template + instance config
3. Implement Correlation Arbitrage template + instance config
4. Test each strategy independently

### Phase 4: Watchlist Manager (Week 3-4)
1. Implement `skills/watchlist_manager.py`
2. Add performance tracking to trade database
3. Integrate with Commander workflow
4. Test rotation logic with historical data

### Phase 5: Sentiment Integration (Week 4, if available)
1. Check for news sentiment MCP availability
2. Implement `skills/sentiment_filter.py`
3. Add sentiment checks to all 5 templates
4. Test graceful degradation without MCP

---

## Open Design Decisions

### 1. Indicator Calculation Engine

**Options:**
- Pure Python: Easier debugging, simpler dependencies
- NumPy: 10-100x faster, industry standard
- TA-Lib: Fastest, but external C dependency

**Recommendation:** NumPy
- Good balance of speed and maintainability
- Already used in data pipeline
- No external compilation needed

### 2. Watchlist Rotation Frequency

**Options:**
- Daily: Responsive but may cause overtrading
- Weekly: Balanced approach
- Monthly: Stable but slow to adapt

**Recommendation:** Weekly
- Sufficient time to establish performance patterns
- Avoids excessive churn
- Aligns with typical options expiration cycles

### 3. Performance Metric Weighting

**Current Proposal:**
- Sharpe Ratio: 40% (risk-adjusted return)
- Win Rate: 30% (consistency)
- Avg P&L: 20% (absolute return)
- Trade Frequency: 10% (opportunity)

**Alternative:**
Equal weighting (25% each) - simpler but may not capture risk properly

**Recommendation:** Keep weighted
- Sharpe ratio most important (risk-adjusted)
- Win rate captures consistency
- Open to tuning after backtesting

### 4. Correlation Arbitrage Pairs

**Options:**
- Manual pairs: User-defined (SPY/IWM, XLF/JPM, etc.)
- Automatic discovery: Scan for high correlation
- Sector-based: Within-sector pairs only

**Recommendation:** Start with manual pairs
- Easier to understand and debug
- Avoid spurious correlations
- Can add auto-discovery in future phase

### 5. Sentiment Score Threshold

**Current Proposal:** Block trades at sentiment <-0.5

**Considerations:**
- Too strict: Miss valid trades during routine negative news
- Too lenient: Fail to avoid major sell-offs

**Recommendation:** -0.5 threshold, adjustable per strategy
- Mean reversion: More tolerant (often trades bad news)
- Breakouts: Stricter filter (news can invalidate setup)
- Allow per-strategy tuning in JSON config
