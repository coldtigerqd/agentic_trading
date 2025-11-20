"""
Skills Library for Agentic AlphaHive Runtime.

This package provides computational primitives that Claude Code (Commander agent)
can invoke to perform deterministic operations including:
- Swarm intelligence orchestration
- Mathematical calculations (Kelly criterion, Black-Scholes IV)
- Validated order execution through safety layer
"""

from .swarm_core import consult_swarm
from .math_core import (
    kelly_criterion,
    black_scholes_iv,
    black_scholes_price,
    calculate_delta,
    calculate_gamma,
    calculate_theta,
    calculate_vega
)
from .execution_gate import place_order_with_guard, OrderResult
from .mcp_bridge import (
    execute_order_with_ibkr,
    fetch_market_data_for_symbols,
    find_target_expiration
)
from .market_data import (
    get_historical_bars,
    get_latest_price,
    add_to_watchlist,
    remove_from_watchlist,
    get_watchlist,
    get_multi_timeframe_data
)
from .technical_indicators import (
    # Moving Averages
    calculate_sma,
    calculate_ema,
    calculate_wma,
    # Momentum Indicators
    calculate_rsi,
    calculate_macd,
    calculate_stochastic,
    # Volatility Indicators
    calculate_bollinger_bands,
    calculate_atr,
    calculate_historical_volatility,
    # Trend Detection
    calculate_adx,
    detect_trend,
    # Support/Resistance
    find_swing_highs,
    find_swing_lows,
    calculate_pivot_points,
    # Volume Indicators
    calculate_obv,
    calculate_vwap
)
from .watchlist_manager import (
    calculate_symbol_score,
    update_watchlist,
    get_watchlist_performance_report,
    get_symbol_sector,
    get_current_watchlist
)

__all__ = [
    # Swarm Intelligence
    "consult_swarm",
    # Math Core
    "kelly_criterion",
    "black_scholes_iv",
    "black_scholes_price",
    "calculate_delta",
    "calculate_gamma",
    "calculate_theta",
    "calculate_vega",
    # Execution
    "place_order_with_guard",
    "OrderResult",
    "execute_order_with_ibkr",
    "fetch_market_data_for_symbols",
    "find_target_expiration",
    # Market Data
    "get_historical_bars",
    "get_latest_price",
    "add_to_watchlist",
    "remove_from_watchlist",
    "get_watchlist",
    "get_multi_timeframe_data",
    # Technical Indicators - Moving Averages
    "calculate_sma",
    "calculate_ema",
    "calculate_wma",
    # Technical Indicators - Momentum
    "calculate_rsi",
    "calculate_macd",
    "calculate_stochastic",
    # Technical Indicators - Volatility
    "calculate_bollinger_bands",
    "calculate_atr",
    "calculate_historical_volatility",
    # Technical Indicators - Trend Detection
    "calculate_adx",
    "detect_trend",
    # Technical Indicators - Support/Resistance
    "find_swing_highs",
    "find_swing_lows",
    "calculate_pivot_points",
    # Technical Indicators - Volume
    "calculate_obv",
    "calculate_vwap",
    # Watchlist Manager
    "calculate_symbol_score",
    "update_watchlist",
    "get_watchlist_performance_report",
    "get_symbol_sector",
    "get_current_watchlist"
]

__version__ = "1.0.0"
