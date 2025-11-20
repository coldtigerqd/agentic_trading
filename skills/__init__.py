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

__all__ = [
    "consult_swarm",
    "kelly_criterion",
    "black_scholes_iv",
    "black_scholes_price",
    "calculate_delta",
    "calculate_gamma",
    "calculate_theta",
    "calculate_vega",
    "place_order_with_guard",
    "OrderResult",
    "execute_order_with_ibkr",
    "fetch_market_data_for_symbols",
    "find_target_expiration",
    "get_historical_bars",
    "get_latest_price",
    "add_to_watchlist",
    "remove_from_watchlist",
    "get_watchlist",
    "get_multi_timeframe_data"
]

__version__ = "1.0.0"
