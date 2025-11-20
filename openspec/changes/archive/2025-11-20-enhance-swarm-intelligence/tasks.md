# Implementation Tasks: Enhanced Swarm Intelligence

**Change ID:** `enhance-swarm-intelligence`
**Status:** Draft
**Created:** 2025-11-20

## Task Overview

This change enhances the Alpha Swarm with 3 new strategy templates, a technical indicators library, and automated watchlist management.

**Estimated Effort:** 16-20 hours across 4 weeks
**Dependencies:** Requires `refactor-market-data-cache` to be completed

---

## Phase 1: Technical Indicators Foundation (Tasks 1-3)

### Task 1: Implement technical indicators library
**Priority:** P0 (Blocking)
**Estimated Time:** 4 hours

**Description:**
Create `skills/technical_indicators.py` with 15+ battle-tested technical analysis functions using NumPy for performance.

**Implementation Steps:**
1. Create `skills/technical_indicators.py` with module structure
2. Implement moving averages (SMA, EMA, WMA)
3. Implement momentum indicators (RSI, MACD, Stochastic)
4. Implement volatility indicators (Bollinger Bands, ATR, Historical Vol)
5. Implement trend indicators (ADX, trend detection)
6. Implement support/resistance helpers (swing highs/lows, pivots)
7. Implement volume indicators (OBV, VWAP)
8. Add comprehensive docstrings with formula references
9. Handle edge cases (NaN, insufficient data, invalid parameters)

**Acceptance Criteria:**
- [ ] All 15 indicator functions implemented with NumPy vectorization
- [ ] Functions handle edge cases gracefully (NaN, empty arrays, insufficient data)
- [ ] Docstrings include formula, parameters, returns, and example usage
- [ ] Performance: 10x faster than naive Python loops

**Files Created:**
- `skills/technical_indicators.py`

---

### Task 2: Write comprehensive unit tests for indicators
**Priority:** P0 (Blocking)
**Estimated Time:** 3 hours

**Description:**
Create exhaustive test suite for technical indicators covering edge cases, accuracy, and performance.

**Implementation Steps:**
1. Create `tests/test_technical_indicators.py`
2. Test moving averages against known reference values
3. Test RSI with edge cases (constant price, trending price, NaN values)
4. Test MACD signal generation (bullish cross, bearish cross, divergence)
5. Test Bollinger Bands (squeeze, expansion, mean reversion)
6. Test ATR with varying volatility regimes
7. Test support/resistance detection with synthetic data
8. Benchmark performance vs naive Python loops
9. Test error handling (ValueError for invalid params, graceful NaN handling)

**Acceptance Criteria:**
- [ ] 100+ test cases covering all indicators
- [ ] Edge case tests pass (empty arrays, NaN values, insufficient data)
- [ ] Accuracy tests match reference implementations (TA-Lib or known values)
- [ ] Performance benchmarks show ≥10x speedup vs naive Python
- [ ] Test coverage ≥95% for technical_indicators.py

**Files Created:**
- `tests/test_technical_indicators.py`

---

### Task 3: Register technical indicators skill
**Priority:** P0 (Blocking)
**Estimated Time:** 15 minutes

**Description:**
Register technical_indicators module in `skills/__init__.py` for import by strategy templates.

**Implementation Steps:**
1. Read `skills/__init__.py`
2. Import all indicator functions
3. Add to `__all__` export list
4. Verify import from strategy templates works

**Acceptance Criteria:**
- [ ] technical_indicators functions importable from skills module
- [ ] All indicator functions visible to Claude Code

**Files Modified:**
- `skills/__init__.py`

---

## Phase 2: Refactor Existing Templates (Tasks 4-5)

### Task 4: Refactor Vol Sniper to use indicator library
**Priority:** P1
**Estimated Time:** 1.5 hours

**Description:**
Replace inline indicator calculations in Vol Sniper template with shared library calls.

**Implementation Steps:**
1. Read current `swarm_intelligence/templates/vol_sniper.md`
2. Identify inline calculations (SMA, historical volatility, S/R levels)
3. Replace with library function calls:
   ```python
   from skills import calculate_sma, calculate_historical_volatility, find_swing_highs, find_swing_lows
   ```
4. Test template rendering with sample parameters
5. Verify signals identical to pre-refactor version (regression test)

**Acceptance Criteria:**
- [ ] Vol Sniper uses indicator library instead of inline calculations
- [ ] Template renders correctly with Jinja2
- [ ] Signals remain identical to pre-refactor version (backward compatibility)
- [ ] Code reduction: ~30-40 lines removed

**Files Modified:**
- `swarm_intelligence/templates/vol_sniper.md`

---

### Task 5: Refactor Trend Scout to use indicator library
**Priority:** P1
**Estimated Time:** 1.5 hours

**Description:**
Replace inline indicator calculations in Trend Scout template with shared library calls.

**Implementation Steps:**
1. Read current `swarm_intelligence/templates/trend_scout.md`
2. Identify inline calculations (SMA, RSI, volume analysis, S/R levels)
3. Replace with library function calls
4. Test template rendering
5. Verify signals identical to pre-refactor version

**Acceptance Criteria:**
- [ ] Trend Scout uses indicator library
- [ ] Template renders correctly
- [ ] Signals remain identical (backward compatibility)
- [ ] Code reduction: ~40-50 lines removed

**Files Modified:**
- `swarm_intelligence/templates/trend_scout.md`

---

## Phase 3: New Strategy Templates (Tasks 6-11)

### Task 6: Implement Mean Reversion strategy template
**Priority:** P1
**Estimated Time:** 3 hours

**Description:**
Create Mean Reversion strategy template for range-bound markets using technical indicator library.

**Implementation Steps:**
1. Create `swarm_intelligence/templates/mean_reversion.md`
2. Implement strategy logic:
   - Trading range identification (30-day high/low)
   - Range rejection criteria (ADX < 25, min width >5%)
   - Entry signals (price at range extremes + RSI confirmation)
   - Position structure (call spreads at support, put spreads at resistance)
3. Add parameter placeholders for Jinja2 templating
4. Include example usage with market_data structure
5. Add comprehensive docstring explaining strategy theory

**Acceptance Criteria:**
- [ ] Template generates valid JSON signals
- [ ] Uses indicator library (no inline calculations)
- [ ] Handles all market conditions (trending, ranging, volatile)
- [ ] Returns NO_TRADE for non-range-bound markets

**Files Created:**
- `swarm_intelligence/templates/mean_reversion.md`

---

### Task 7: Create Mean Reversion instance config
**Priority:** P1
**Estimated Time:** 30 minutes

**Description:**
Create instance configuration for SPY mean reversion trading.

**Implementation Steps:**
1. Create `swarm_intelligence/active_instances/spy_mean_reversion.json`
2. Configure parameters:
   - symbol_pool: ["SPY"]
   - range_lookback_days: 30
   - range_min_width_pct: 5.0
   - entry_threshold_pct: 2.0
   - rsi_oversold: 30, rsi_overbought: 70
   - max_adx: 25
3. Add evolution_history metadata
4. Validate JSON format

**Acceptance Criteria:**
- [ ] JSON file valid and parseable
- [ ] Parameters appropriate for SPY (liquid, range-bound ETF)

**Files Created:**
- `swarm_intelligence/active_instances/spy_mean_reversion.json`

---

### Task 8: Implement Breakout Scout strategy template
**Priority:** P1
**Estimated Time:** 3 hours

**Description:**
Create Breakout Scout strategy template for volatility expansion using consolidation and breakout detection.

**Implementation Steps:**
1. Create `swarm_intelligence/templates/breakout_scout.md`
2. Implement strategy logic:
   - Consolidation detection (declining ATR, narrow Bollinger Bands)
   - Breakout confirmation (volume spike, ATR expansion)
   - False breakout filter (2-hour confirmation, multi-timeframe alignment)
   - Position structure (call/put spreads at breakout level)
3. Add parameter placeholders
4. Include comprehensive docstring

**Acceptance Criteria:**
- [ ] Template generates valid JSON signals
- [ ] Uses indicator library
- [ ] Filters false breakouts effectively
- [ ] Returns NO_TRADE during consolidation phase

**Files Created:**
- `swarm_intelligence/templates/breakout_scout.md`

---

### Task 9: Create Breakout Scout instance config
**Priority:** P1
**Estimated Time:** 30 minutes

**Description:**
Create instance configuration for tech stock breakout hunting.

**Implementation Steps:**
1. Create `swarm_intelligence/active_instances/tech_breakout_hunter.json`
2. Configure parameters:
   - symbol_pool: ["AAPL", "NVDA", "MSFT", "GOOGL", "TSLA"]
   - consolidation_days: 10
   - atr_contraction_threshold: 0.8
   - volume_breakout_multiplier: 1.5
   - confirmation_hours: 2
   - target_atr_multiple: 2.0
3. Validate JSON

**Acceptance Criteria:**
- [ ] JSON valid
- [ ] Parameters tuned for tech stocks (high volatility)

**Files Created:**
- `swarm_intelligence/active_instances/tech_breakout_hunter.json`

---

### Task 10: Implement Correlation Arbitrage strategy template
**Priority:** P2
**Estimated Time:** 3.5 hours

**Description:**
Create Correlation Arbitrage template for relative value trading using correlation analysis.

**Implementation Steps:**
1. Create `swarm_intelligence/templates/correlation_arbitrage.md`
2. Implement strategy logic:
   - Pair correlation calculation (60-day rolling)
   - Spread z-score computation
   - Divergence detection (z-score >2.0)
   - Correlation breakdown check (stop if <0.5)
   - Market-neutral position structure
3. Add parameter placeholders
4. Include pair trading theory docstring

**Acceptance Criteria:**
- [ ] Template generates valid JSON signals
- [ ] Calculates rolling correlation correctly
- [ ] Detects divergences (z-score based)
- [ ] Returns NO_TRADE if correlation breaks down

**Files Created:**
- `swarm_intelligence/templates/correlation_arbitrage.md`

---

### Task 11: Create Correlation Arbitrage instance config
**Priority:** P2
**Estimated Time:** 30 minutes

**Description:**
Create instance configuration for sector pairs trading.

**Implementation Steps:**
1. Create `swarm_intelligence/active_instances/sector_pairs_trader.json`
2. Configure parameters:
   - symbol_pairs: [["XLF", "JPM"], ["XLE", "XOM"], ["XLK", "AAPL"]]
   - correlation_window: 60
   - min_correlation: 0.7
   - entry_zscore: 2.0
   - stop_zscore: 3.0
   - max_holding_days: 30
3. Validate JSON

**Acceptance Criteria:**
- [ ] JSON valid
- [ ] Pairs selected from same sectors (correlation stability)

**Files Created:**
- `swarm_intelligence/active_instances/sector_pairs_trader.json`

---

## Phase 4: Automated Watchlist Manager (Tasks 12-14)

### Task 12: Implement watchlist manager skill
**Priority:** P1
**Estimated Time:** 3 hours

**Description:**
Create automated watchlist rotation based on performance metrics.

**Implementation Steps:**
1. Create `skills/watchlist_manager.py`
2. Implement performance scoring:
   ```python
   def calculate_symbol_score(symbol, lookback_days=90) -> float
   ```
   - Sharpe ratio (40% weight)
   - Win rate (30% weight)
   - Avg P&L (20% weight)
   - Trade frequency (10% weight)
3. Implement rotation logic:
   ```python
   def update_watchlist(current, candidates) -> Dict
   ```
   - Identify bottom 20% performers
   - Find better candidates
   - Limit churn (max 3 changes per week)
4. Implement sector balance check (max 30% per sector)
5. Add logging for rotation decisions

**Acceptance Criteria:**
- [ ] Performance scoring combines 4 metrics correctly
- [ ] Rotation identifies bottom 20% and replaces with better candidates
- [ ] Churn limited to 3 changes per week
- [ ] Sector diversification enforced (max 30% per sector)
- [ ] Returns structured recommendation dict

**Files Created:**
- `skills/watchlist_manager.py`

---

### Task 13: Write watchlist manager tests
**Priority:** P1
**Estimated Time:** 2 hours

**Description:**
Test watchlist rotation logic with simulated performance data.

**Implementation Steps:**
1. Create `tests/test_watchlist_manager.py`
2. Test performance scoring with synthetic data
3. Test rotation logic (verify bottom 20% identified)
4. Test churn limits (max 3 changes enforced)
5. Test sector balance constraints
6. Test edge cases (all symbols performing well, no candidates)

**Acceptance Criteria:**
- [ ] All rotation scenarios tested
- [ ] Edge cases handled gracefully
- [ ] Sector diversification verified

**Files Created:**
- `tests/test_watchlist_manager.py`

---

### Task 14: Integrate watchlist manager into Commander workflow
**Priority:** P1
**Estimated Time:** 1.5 hours

**Description:**
Add watchlist update handling to Commander system prompt.

**Implementation Steps:**
1. Read `prompts/commander_system.md`
2. Add watchlist evaluation to THINK phase:
   ```python
   from skills import update_watchlist

   # Weekly watchlist check
   if today.weekday() == 0:  # Monday
       recommendations = update_watchlist(current_watchlist, candidate_symbols)
   ```
3. Add watchlist update execution to ACT phase
4. Log watchlist changes to database
5. Test Commander cycle with watchlist updates

**Acceptance Criteria:**
- [ ] Commander evaluates watchlist weekly (Mondays)
- [ ] Watchlist updates applied if recommended
- [ ] Changes logged to database with reasoning

**Files Modified:**
- `prompts/commander_system.md`

---

## Phase 5: Sentiment Integration (Tasks 15-16) [OPTIONAL]

### Task 15: Investigate news sentiment MCP availability
**Priority:** P2
**Estimated Time:** 30 minutes

**Description:**
Check if news sentiment MCP server is available and document API.

**Implementation Steps:**
1. Check `~/.claude.json` for sentiment MCP configuration
2. Test sentiment MCP connection
3. Document API endpoints and response format
4. Determine if integration feasible

**Acceptance Criteria:**
- [ ] Sentiment MCP availability confirmed or ruled out
- [ ] API documented if available
- [ ] Integration plan decided (implement or defer)

**Files Created:**
- `docs/sentiment_mcp_api.md` (if available)

---

### Task 16: Implement sentiment filter skill (if MCP available)
**Priority:** P2
**Estimated Time:** 2 hours

**Description:**
Create sentiment filtering skill with graceful degradation if MCP unavailable.

**Implementation Steps:**
1. Create `skills/sentiment_filter.py`
2. Implement `get_news_sentiment(symbol, lookback_hours)`:
   - Try to import sentiment MCP
   - Return score [-1.0, 1.0] if available
   - Return None if unavailable (graceful degradation)
3. Add sentiment check to all 5 strategy templates:
   ```python
   sentiment_score = get_news_sentiment(symbol, 24)
   if sentiment_score and sentiment_score < -0.5:
       return NO_TRADE
   ```
4. Test with and without MCP available

**Acceptance Criteria:**
- [ ] Sentiment skill returns score if MCP available
- [ ] Returns None gracefully if MCP unavailable
- [ ] All 5 templates include sentiment filter
- [ ] Templates work without sentiment (optional feature)

**Files Created:**
- `skills/sentiment_filter.py`

**Files Modified:**
- All 5 strategy templates (vol_sniper, trend_scout, mean_reversion, breakout_scout, correlation_arbitrage)

---

## Phase 6: Testing & Documentation (Tasks 17-18)

### Task 17: Integration testing
**Priority:** P1
**Estimated Time:** 2 hours

**Description:**
End-to-end testing of enhanced swarm intelligence system.

**Implementation Steps:**
1. Test full Commander cycle with 5 strategies
2. Test strategy selection across different market regimes
3. Test watchlist rotation after 90 days simulation
4. Test sentiment filtering (if available)
5. Test indicator library performance under load
6. Validate signal deduplication and ranking

**Acceptance Criteria:**
- [ ] All 5 strategies generate valid signals
- [ ] Commander selects appropriate strategy for market regime
- [ ] Watchlist rotates correctly after 90 days
- [ ] No performance degradation with 5 concurrent strategies
- [ ] Signal quality improved vs 2-strategy baseline

**Files Created:**
- `tests/test_swarm_integration.py`

---

### Task 18: Update documentation
**Priority:** P2
**Estimated Time:** 2 hours

**Description:**
Document new strategies, indicator library, and watchlist management.

**Implementation Steps:**
1. Update README.md with:
   - Section 3.6: Technical Indicators Library
   - Section 3.7: Strategy Templates (all 5)
   - Section 3.8: Automated Watchlist Manager
   - Section 3.9: Sentiment Integration (if available)
2. Document indicator API reference
3. Document strategy selection logic
4. Add usage examples for each strategy
5. Document watchlist rotation process

**Acceptance Criteria:**
- [ ] README.md includes all new capabilities
- [ ] Indicator API fully documented
- [ ] Each strategy has usage example
- [ ] Watchlist rotation explained clearly

**Files Modified:**
- `README.md`

---

## Task Dependencies

```
Task 1 (Indicators) → Task 2 (Tests) → Task 3 (Register)
                                         ↓
Task 4 (Vol Sniper Refactor) ←──────────┤
Task 5 (Trend Scout Refactor) ←─────────┤
                                         ↓
Task 6 (Mean Reversion) → Task 7 (Instance) ────┐
Task 8 (Breakout Scout) → Task 9 (Instance) ────┤
Task 10 (Correlation Arb) → Task 11 (Instance) ─┤
                                                  ↓
Task 12 (Watchlist Manager) → Task 13 (Tests) → Task 14 (Integration)
                                                  ↓
Task 15 (Sentiment Check) → Task 16 (Sentiment Skill) (OPTIONAL)
                                                  ↓
Task 17 (Integration Tests) → Task 18 (Documentation)
```

**Parallelizable:**
- Tasks 6-11 (all strategy templates can be developed concurrently)
- Tasks 4-5 (both refactors independent)

**Blocking:**
- Tasks 1-3 block everything (indicator library required by all)
- Task 12 blocks Task 14 (watchlist manager integration)
- Task 15 determines Task 16 (sentiment availability check)

---

## Validation Checklist

Before marking this change as complete, verify:

- [ ] All 18 tasks completed (or 16 if sentiment unavailable)
- [ ] Technical indicators library has 15+ functions
- [ ] 5 total strategy templates operational (Vol Sniper, Trend Scout, Mean Reversion, Breakout, Correlation)
- [ ] Watchlist manager rotates underperformers automatically
- [ ] All templates use shared indicator library (no code duplication)
- [ ] 100+ unit tests pass for indicators
- [ ] Integration tests pass for full swarm workflow
- [ ] Documentation updated (README.md)
- [ ] `openspec validate enhance-swarm-intelligence --strict` passes

---

## Performance Metrics

**Code Efficiency:**
- Indicator code reuse: 50% reduction in LOC across templates
- Calculation speedup: 10x faster with NumPy vs naive Python

**Trading Performance (Expected):**
- Strategy coverage: 5 templates cover all major market regimes
- Watchlist optimization: Focus on top 80% performers
- Signal quality: 15-20% improvement with sentiment filtering

**System Performance:**
- Strategy execution time: <2 seconds for 5 concurrent agents
- Watchlist update time: <1 second weekly evaluation
- Memory usage: <100MB for indicator calculations
