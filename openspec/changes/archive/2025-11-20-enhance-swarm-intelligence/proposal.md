# Proposal: Enhance Swarm Intelligence with Advanced Strategies and Technical Analysis

**Change ID:** `enhance-swarm-intelligence`
**Status:** Draft
**Created:** 2025-11-20
**Author:** AI Assistant

## Summary

Enhance the Alpha Swarm trading intelligence with three new strategy templates (Mean Reversion, Breakout Scout, Correlation Arbitrage), a comprehensive technical indicators library, and automated watchlist management. This builds on the market data cache foundation to enable sophisticated multi-strategy trading with intelligent symbol selection.

## Why

The trading system currently has only two strategy templates (Vol Sniper and Trend Scout), limiting its ability to capitalize on different market conditions. Key gaps:

1. **Limited Strategy Diversity**: Only volatility-selling and trend-following covered; missing mean reversion and breakout strategies
2. **Code Duplication**: Each template recalculates technical indicators (SMA, RSI, etc.) independently
3. **Manual Watchlist Management**: Requires human intervention to add/remove symbols based on performance
4. **No Sentiment Integration**: Purely technical analysis; missing fundamental/sentiment overlay

Without these enhancements, the system cannot:
- Trade range-bound markets (mean reversion)
- Capture volatility expansion (breakouts)
- Exploit inter-symbol relationships (correlation arbitrage)
- Adapt watchlist based on changing market conditions
- Incorporate news sentiment into decision-making

## What Changes

**New Capabilities:**
- Technical indicators library with 10+ battle-tested functions (SMA, EMA, RSI, MACD, Bollinger Bands, ATR, etc.)
- Mean Reversion strategy template for range-bound markets
- Breakout Scout strategy template for volatility expansion
- Correlation Arbitrage strategy template for relative value trading
- Automated watchlist manager based on Swarm recommendations and performance metrics
- News sentiment integration (if MCP server available)

**Modified Components:**
- Vol Sniper and Trend Scout templates refactored to use shared indicator library
- Swarm core enhanced with watchlist update hooks
- Commander workflow updated to process watchlist change signals

**Performance Expectations:**
- 5 total strategy templates covering all major market regimes
- 50% reduction in indicator calculation code (shared library)
- Automated symbol rotation based on performance (top 20% performers prioritized)
- Sentiment-filtered trades (avoid high-risk news events)

## Goals

- ✅ Create reusable technical indicators library for all strategies
- ✅ Implement 3 new strategy templates (Mean Reversion, Breakout Scout, Correlation Arbitrage)
- ✅ Build automated watchlist manager with performance-based rotation
- ✅ Integrate news sentiment filtering (if MCP available)
- ✅ Refactor existing templates to use shared indicator library
- ✅ Maintain backward compatibility with existing Vol Sniper and Trend Scout

## Non-Goals

- ❌ Machine learning or AI-based indicator generation (use proven technical analysis only)
- ❌ Real-time tick-by-tick analysis (5-minute bars sufficient)
- ❌ Custom indicator development beyond industry standards
- ❌ Multi-asset class support (focus on equities/ETFs only)
- ❌ Sentiment analysis from social media (use professional news feeds only)

## Scope

### Capabilities Affected

- **NEW**: `technical-indicators` - Shared library of battle-tested technical analysis functions
- **NEW**: `mean-reversion-strategy` - Range-bound market strategy template
- **NEW**: `breakout-strategy` - Volatility expansion strategy template
- **NEW**: `correlation-arbitrage-strategy` - Relative value strategy template
- **NEW**: `watchlist-manager` - Automated symbol rotation based on performance
- **NEW**: `sentiment-integration` - News sentiment filtering capability
- **MODIFIED**: `swarm-templates` (existing) - Refactor to use shared indicator library

### Dependencies

- **Requires**: Market data cache (already implemented in `refactor-market-data-cache`)
- **Requires**: ThetaData MCP for historical data and options chains
- **Optional**: News sentiment MCP server (graceful degradation if unavailable)
- **Modifies**: `skills/` directory (add `technical_indicators.py`)
- **Modifies**: `swarm_intelligence/templates/` (3 new templates, 2 refactored)
- **Modifies**: `swarm_intelligence/active_instances/` (5+ new instance configs)

### Files Affected

**New Files:**
- `skills/technical_indicators.py` - Technical analysis library
- `skills/watchlist_manager.py` - Automated watchlist rotation
- `swarm_intelligence/templates/mean_reversion.md` - Mean reversion strategy
- `swarm_intelligence/templates/breakout_scout.md` - Breakout strategy
- `swarm_intelligence/templates/correlation_arbitrage.md` - Pairs trading strategy
- `swarm_intelligence/active_instances/spy_mean_reversion.json` - SPY range trader
- `swarm_intelligence/active_instances/tech_breakout_hunter.json` - Tech breakouts
- `swarm_intelligence/active_instances/sector_pairs_trader.json` - Sector correlation
- `tests/test_technical_indicators.py` - Indicator library tests
- `tests/test_watchlist_manager.py` - Watchlist automation tests

**Modified Files:**
- `skills/__init__.py` - Register new skills
- `swarm_intelligence/templates/vol_sniper.md` - Refactor to use indicator library
- `swarm_intelligence/templates/trend_scout.md` - Refactor to use indicator library
- `prompts/commander_system.md` - Add watchlist update handling
- `README.md` - Document new strategies and indicator library

## Impact Assessment

- **Risk:** Low - Purely additive capabilities with backward compatibility
- **Complexity:** Medium - Requires careful indicator implementation and testing
- **Performance Impact:**
  - Code reuse: ~50% reduction in redundant indicator calculations
  - Watchlist optimization: Focus on top 20% performers (higher win rate)
  - Sentiment filtering: Avoid 30-40% of high-risk trades during major news
- **Breaking Changes:** None - all new capabilities, existing templates remain functional

## Success Criteria

- [ ] Technical indicators library passes 100+ unit tests (edge cases, NaN handling, vectorization)
- [ ] All 3 new strategy templates generate valid JSON signals
- [ ] Watchlist manager successfully rotates underperformers out after 30 days
- [ ] Sentiment integration filters trades during earnings announcements (if available)
- [ ] Existing Vol Sniper and Trend Scout maintain identical behavior after refactor
- [ ] 5 total strategy templates cover all market regimes (trending, ranging, volatile, calm, correlating)
- [ ] Code duplication reduced by 50% (indicator calculations shared)
- [ ] All tests pass (unit, integration, template rendering)
- [ ] Documentation updated with strategy descriptions and indicator API reference
- [ ] `openspec validate enhance-swarm-intelligence --strict` passes

## Open Questions

1. **News Sentiment MCP**: Is a news sentiment MCP server available? If not, defer sentiment integration to future phase.
2. **Indicator Calculation Engine**: Use pure Python (easier debugging) or NumPy (faster)? Recommend NumPy for production.
3. **Watchlist Rotation Frequency**: How often to evaluate watchlist changes (daily, weekly, monthly)? Recommend weekly to avoid overtrading.
4. **Performance Metrics**: Which metrics to use for watchlist ranking (Sharpe ratio, win rate, P&L, consistency)? Recommend composite score.
5. **Correlation Window**: What lookback period for correlation arbitrage (30 days, 60 days, 90 days)? Recommend 60 days for stability.
