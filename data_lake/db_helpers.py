"""
Database helper functions for trade and safety event logging.

Provides functions to interact with SQLite database for persistent storage.
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from contextlib import contextmanager


DB_PATH = Path(__file__).parent / "trades.db"


@contextmanager
def get_db_connection():
    """
    Context manager for database connections.

    Yields:
        sqlite3.Connection: Database connection with WAL mode enabled
    """
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row  # Return rows as dictionaries

    # Enable WAL mode for better concurrency
    conn.execute("PRAGMA journal_mode=WAL")

    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def initialize_database():
    """Initialize database with schema if it doesn't exist."""
    schema_path = Path(__file__).parent / "schema.sql"

    with open(schema_path, 'r') as f:
        schema_sql = f.read()

    with get_db_connection() as conn:
        conn.executescript(schema_sql)


def log_trade(
    symbol: str,
    strategy: str,
    legs: List[Dict],
    max_risk: float,
    capital_required: float,
    status: str,
    signal_source: Optional[str] = None,
    confidence: Optional[float] = None,
    reasoning: Optional[str] = None,
    order_id: Optional[int] = None,
    fill_price: Optional[float] = None,
    pnl: Optional[float] = None,
    metadata: Optional[Dict] = None
) -> int:
    """
    Log a trade order to the database.

    Args:
        symbol: Trading symbol
        strategy: Strategy name (e.g., "PUT_SPREAD", "IRON_CONDOR")
        legs: List of order legs with action/strike/expiry/quantity/price
        max_risk: Maximum risk for this trade ($)
        capital_required: Capital to deploy ($)
        status: Order status ('SUBMITTED', 'FILLED', 'REJECTED', etc.)
        signal_source: Instance ID that generated the signal
        confidence: Signal confidence score (0.0-1.0)
        reasoning: Human-readable explanation
        order_id: IBKR order ID (if submitted)
        fill_price: Actual fill price (if filled)
        pnl: Profit/loss (if closed)
        metadata: Additional context as dictionary

    Returns:
        trade_id: Database row ID
    """
    timestamp = datetime.now().isoformat()
    legs_json = json.dumps(legs)
    metadata_json = json.dumps(metadata) if metadata else None

    with get_db_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO trades (
                timestamp, symbol, strategy, signal_source, legs,
                max_risk, capital_required, confidence, reasoning,
                order_id, status, fill_price, pnl, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                timestamp, symbol, strategy, signal_source, legs_json,
                max_risk, capital_required, confidence, reasoning,
                order_id, status, fill_price, pnl, metadata_json
            )
        )
        return cursor.lastrowid


def update_trade_status(
    trade_id: int,
    status: str,
    order_id: Optional[int] = None,
    fill_price: Optional[float] = None,
    pnl: Optional[float] = None
):
    """
    Update trade status after execution.

    Args:
        trade_id: Database trade ID
        status: New status
        order_id: IBKR order ID (if available)
        fill_price: Fill price (if filled)
        pnl: Profit/loss (if closed)
    """
    with get_db_connection() as conn:
        conn.execute(
            """
            UPDATE trades
            SET status = ?, order_id = COALESCE(?, order_id),
                fill_price = COALESCE(?, fill_price),
                pnl = COALESCE(?, pnl)
            WHERE trade_id = ?
            """,
            (status, order_id, fill_price, pnl, trade_id)
        )


def log_safety_event(
    event_type: str,
    details: Dict[str, Any],
    action_taken: str
) -> int:
    """
    Log a safety event (violation, circuit breaker, etc.).

    Args:
        event_type: Type of event (e.g., 'ORDER_REJECTED', 'CIRCUIT_BREAKER')
        details: Event details as dictionary
        action_taken: Description of action taken

    Returns:
        event_id: Database row ID
    """
    timestamp = datetime.now().isoformat()
    details_json = json.dumps(details)

    with get_db_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO safety_events (timestamp, event_type, details, action_taken)
            VALUES (?, ?, ?, ?)
            """,
            (timestamp, event_type, details_json, action_taken)
        )
        return cursor.lastrowid


def query_trades(
    symbol: Optional[str] = None,
    status: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 100
) -> List[Dict]:
    """
    Query trades with optional filters.

    Args:
        symbol: Filter by symbol
        status: Filter by status
        start_date: Filter by start date (ISO format)
        end_date: Filter by end date (ISO format)
        limit: Maximum number of results

    Returns:
        List of trade dictionaries
    """
    query = "SELECT * FROM trades WHERE 1=1"
    params = []

    if symbol:
        query += " AND symbol = ?"
        params.append(symbol)

    if status:
        query += " AND status = ?"
        params.append(status)

    if start_date:
        query += " AND timestamp >= ?"
        params.append(start_date)

    if end_date:
        query += " AND timestamp <= ?"
        params.append(end_date)

    query += " ORDER BY timestamp DESC LIMIT ?"
    params.append(limit)

    with get_db_connection() as conn:
        cursor = conn.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]


def query_safety_events(
    event_type: Optional[str] = None,
    start_date: Optional[str] = None,
    limit: int = 100
) -> List[Dict]:
    """
    Query safety events with optional filters.

    Args:
        event_type: Filter by event type
        start_date: Filter by start date (ISO format)
        limit: Maximum number of results

    Returns:
        List of safety event dictionaries
    """
    query = "SELECT * FROM safety_events WHERE 1=1"
    params = []

    if event_type:
        query += " AND event_type = ?"
        params.append(event_type)

    if start_date:
        query += " AND timestamp >= ?"
        params.append(start_date)

    query += " ORDER BY timestamp DESC LIMIT ?"
    params.append(limit)

    with get_db_connection() as conn:
        cursor = conn.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]


# Initialize database on module import
initialize_database()
