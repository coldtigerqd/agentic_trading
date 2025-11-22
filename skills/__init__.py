"""
Agentic AlphaHive 运行时技能库。

本软件包提供 Claude Code (Commander 代理) 可调用的计算原语，
用于执行确定性操作，包括：
- 蜂群智能编排
- 数学计算 (Kelly Criterion, Black-Scholes IV)
- 通过安全层验证的订单执行
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
from .indicator_helpers import (
    # Exception Classes
    InsufficientDataError,
    InvalidDataError,
    # Safe Wrapper Functions
    safe_calculate_sma,
    safe_calculate_rsi,
    safe_calculate_macd,
    safe_calculate_historical_volatility,
    safe_detect_trend,
    calculate_all_indicators_safe
)
from .watchlist_manager import (
    calculate_symbol_score,
    update_watchlist,
    get_watchlist_performance_report,
    get_symbol_sector,
    get_current_watchlist
)
from .data_sync import (
    sync_watchlist_incremental,
    process_snapshot_and_cache,
    get_data_freshness_report,
    get_watchlist_symbols
)
from .workflow_skills import (
    run_full_trading_analysis,
    run_market_health_check,
    run_position_risk_analysis,
    TradingAnalysisResult
)
from .strategy_manager import (
    list_active_strategies,
    get_strategy_config,
    enable_strategy,
    disable_strategy,
    analyze_with_strategy
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
    # Technical Indicators - Safe Helpers
    "InsufficientDataError",
    "InvalidDataError",
    "safe_calculate_sma",
    "safe_calculate_rsi",
    "safe_calculate_macd",
    "safe_calculate_historical_volatility",
    "safe_detect_trend",
    "calculate_all_indicators_safe",
    # Watchlist Manager
    "calculate_symbol_score",
    "update_watchlist",
    "get_watchlist_performance_report",
    "get_symbol_sector",
    "get_current_watchlist",
    # Data Sync
    "sync_watchlist_incremental",
    "process_snapshot_and_cache",
    "get_data_freshness_report",
    "get_watchlist_symbols",
    # Workflow Skills (High-Level)
    "run_full_trading_analysis",
    "run_market_health_check",
    "run_position_risk_analysis",
    "TradingAnalysisResult",
    # Strategy Manager
    "list_active_strategies",
    "get_strategy_config",
    "enable_strategy",
    "disable_strategy",
    "analyze_with_strategy"
]

__version__ = "2.0.0"  # 升级版本号，反映架构优化
