"""
Unified database connection configuration for Agentic AlphaHive.

This module provides a single source of truth for database connection
management, ensuring consistent configuration and error handling across
all data persistence operations.

Configuration Choices:
- journal_mode=WAL: Write-Ahead Logging for better concurrency
- synchronous=NORMAL: Balanced durability/performance trade-off
- row_factory=Row: Dictionary-like row access
"""

import sqlite3
from pathlib import Path
from contextlib import contextmanager
from typing import Generator


# Single source of truth for database path
DB_PATH = Path(__file__).parent / "trades.db"


@contextmanager
def get_db_connection() -> Generator[sqlite3.Connection, None, None]:
    """
    Context manager for database connections with optimized settings.

    Provides automatic transaction management:
    - Auto-commits on successful completion
    - Auto-rollbacks on exceptions
    - Auto-closes connection in all cases

    Yields:
        sqlite3.Connection: Configured database connection with:
            - WAL mode enabled for concurrent access
            - NORMAL synchronous mode for performance
            - Row factory for dictionary-style access

    Example:
        >>> with get_db_connection() as conn:
        ...     cursor = conn.cursor()
        ...     cursor.execute("SELECT * FROM trades")
        ...     # Auto-commits on exit

    Performance Notes:
        - WAL mode allows readers during writes
        - NORMAL sync trades absolute durability for speed
        - Safe for development and paper trading
        - Consider FULL sync for live trading with real money
    """
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row  # Enable dict-like row access

    # Performance optimization: Write-Ahead Logging
    conn.execute("PRAGMA journal_mode=WAL")

    # Performance optimization: Balanced sync mode
    conn.execute("PRAGMA synchronous=NORMAL")

    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
