# Spec Delta: Data Persistence Consolidation

## MODIFIED Requirements

### Requirement: Unified Database Connection Management

All database connections SHALL use a single, centralized connection manager with consistent configuration, error handling, and resource management. The system MUST define `get_db_connection()` in exactly one location: `data_lake/db_config.py`.

**Rationale**: Multiple implementations of database connection logic lead to inconsistent behavior, resource leaks, and maintenance burden. A single source of truth ensures reliability.

#### Scenario: Application code needs database connection

**Given** any module needs to access the database
**When** it imports from data_lake
**Then** it should use `from data_lake.db_config import get_db_connection`
**And** it should use the context manager pattern: `with get_db_connection() as conn:`
**And** connection should have WAL mode enabled
**And** connection should auto-commit on success or rollback on error

#### Scenario: Database connection fails

**Given** a database operation is attempted
**When** an error occurs during the operation
**Then** the transaction should automatically rollback
**And** the connection should be properly closed
**And** the exception should propagate to the caller

---

### Requirement: Consistent PRAGMA Settings

All database connections SHALL use consistent SQLite PRAGMA settings optimized for the application's access patterns. Connections MUST enable `journal_mode=WAL` and `synchronous=NORMAL`.

**Rationale**: Inconsistent PRAGMA settings lead to unpredictable performance and potential data integrity issues.

#### Scenario: Multiple processes access database

**Given** both skills and daemons access the database
**When** connections are established
**Then** all connections should use `PRAGMA journal_mode=WAL`
**And** all connections should use `PRAGMA synchronous=NORMAL`
**And** write-ahead logging should allow concurrent reads during writes

---

## ADDED Requirements

### Requirement: Unified Public API for Data Persistence

The data_lake module SHALL provide a clean, documented public API that abstracts internal implementation details. The module MUST export all public functions via `__init__.py` with an `__all__` list.

**Rationale**: External code should not need to know about internal module structure. A public API provides stability and clear interfaces.

#### Scenario: Skills module logs a trade

**Given** the execution_gate skill wants to log a trade
**When** it imports data_lake
**Then** it should be able to: `from data_lake import log_trade`
**And** it should NOT need to know about db_helpers.py
**And** log_trade should handle all database interactions internally

#### Scenario: Market data skill inserts bars

**Given** the market_data skill has new OHLCV data
**When** it imports data_lake
**Then** it should be able to: `from data_lake import insert_bars, OHLCVBar`
**And** it should NOT need to know about market_data_manager.py
**And** insert_bars should handle connection management automatically

#### Scenario: Swarm core saves snapshot

**Given** the swarm_core skill wants to save a decision snapshot
**When** it imports data_lake
**Then** it should be able to: `from data_lake import save_snapshot`
**And** snapshots should be independent of database (use filesystem)
**And** snapshot_manager should not require database connection

---

## REMOVED Requirements

None. All previous requirements remain valid; this change consolidates implementation without changing external contracts.

---

## Technical Specifications

### DB_PATH Definition
```python
# data_lake/db_config.py (ONLY location)
DB_PATH = Path(__file__).parent / "trades.db"
```

### Connection Manager Signature
```python
@contextmanager
def get_db_connection() -> Generator[sqlite3.Connection, None, None]:
    """
    Context manager for database connections.

    Yields:
        sqlite3.Connection with WAL mode, NORMAL sync, and Row factory

    Behavior:
        - Auto-commits on successful exit
        - Auto-rollbacks on exception
        - Auto-closes connection in finally block
    """
```

### Public API Surface
```python
# data_lake/__init__.py
__all__ = [
    # Core config
    'DB_PATH',
    'get_db_connection',

    # Trade logging
    'log_trade',
    'update_trade_status',
    'log_safety_event',
    'query_trades',
    'query_safety_events',

    # Market data
    'OHLCVBar',
    'insert_bars',
    'get_bars',
    'get_latest_bar',
    'get_freshness_info',

    # Snapshots
    'save_snapshot',
    'load_snapshot',
    'list_snapshots',
]
```

---

## Migration Guide

### For Existing Code Using Old Pattern

**Before** (market_data_manager.py pattern):
```python
from data_lake.market_data_manager import get_db_connection

conn = get_db_connection()
try:
    cursor = conn.cursor()
    cursor.execute("SELECT ...")
    conn.commit()
finally:
    conn.close()
```

**After** (unified pattern):
```python
from data_lake import get_db_connection

with get_db_connection() as conn:
    cursor = conn.cursor()
    cursor.execute("SELECT ...")
    # Auto-commits on exit
```

### For Existing Code Defining DB_PATH

**Before**:
```python
from pathlib import Path
DB_PATH = Path(__file__).parent / "trades.db"
conn = sqlite3.connect(DB_PATH)
```

**After**:
```python
from data_lake import get_db_connection

with get_db_connection() as conn:
    # Use connection
```
