"""
Data Persistence Layer for Agentic AlphaHive.

This module provides a unified public API for all data persistence operations,
including trade logging, market data storage, and decision snapshot management.

Example Usage:
    >>> from data_lake import log_trade, insert_bars, save_snapshot
    >>>
    >>> # Log a trade
    >>> trade_id = log_trade(
    ...     symbol="AAPL",
    ...     strategy="PUT_SPREAD",
    ...     legs=[...],
    ...     max_risk=500.0,
    ...     capital_required=1000.0,
    ...     status="SUBMITTED"
    ... )
    >>>
    >>> # Insert market data
    >>> from data_lake import OHLCVBar
    >>> bars = [OHLCVBar(...), OHLCVBar(...)]
    >>> insert_bars("AAPL", bars)
    >>>
    >>> # Save decision snapshot
    >>> snapshot_id = save_snapshot(
    ...     instance_id="tech_aggressive",
    ...     template_name="vol_sniper.md",
    ...     rendered_prompt="...",
    ...     market_data={...}
    ... )
"""

# Core configuration
from .db_config import DB_PATH, get_db_connection

# Trade and safety event logging
from .db_helpers import (
    initialize_database,
    log_trade,
    update_trade_status,
    log_safety_event,
    query_trades,
    query_safety_events,
)

# Market data operations
from .market_data_manager import (
    OHLCVBar,
    insert_bars,
    get_bars,
    aggregate_bars,
    get_latest_bar,
    get_freshness_info,
    detect_gaps,
    cleanup_old_data,
)

# Snapshot management
from .snapshot_manager import (
    save_snapshot,
    update_snapshot_response,
    load_snapshot,
    list_snapshots,
    get_snapshot_stats,
)

# Watchlist seeding
from .seed_watchlist import seed_initial_watchlist


__all__ = [
    # Configuration
    "DB_PATH",
    "get_db_connection",
    # Trade logging
    "initialize_database",
    "log_trade",
    "update_trade_status",
    "log_safety_event",
    "query_trades",
    "query_safety_events",
    # Market data
    "OHLCVBar",
    "insert_bars",
    "get_bars",
    "aggregate_bars",
    "get_latest_bar",
    "get_freshness_info",
    "detect_gaps",
    "cleanup_old_data",
    # Snapshots
    "save_snapshot",
    "update_snapshot_response",
    "load_snapshot",
    "list_snapshots",
    "get_snapshot_stats",
    # Utilities
    "seed_initial_watchlist",
]
