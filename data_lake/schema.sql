-- Database schema for Agentic AlphaHive Runtime
-- SQLite database for trade records and safety events

-- Trades table: Records all order submissions
CREATE TABLE IF NOT EXISTS trades (
    trade_id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    symbol TEXT NOT NULL,
    strategy TEXT NOT NULL,
    signal_source TEXT,  -- instance_id that generated the signal
    legs TEXT NOT NULL,  -- JSON array of order legs
    max_risk REAL NOT NULL,
    capital_required REAL NOT NULL,
    confidence REAL,
    reasoning TEXT,
    order_id INTEGER,
    status TEXT NOT NULL,  -- 'SUBMITTED', 'FILLED', 'REJECTED', 'CANCELLED', 'PENDING'
    fill_price REAL,
    pnl REAL,
    metadata TEXT,  -- JSON object with additional context
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Safety events table: Records all safety violations and circuit breaker triggers
CREATE TABLE IF NOT EXISTS safety_events (
    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    event_type TEXT NOT NULL,  -- 'ORDER_REJECTED', 'CIRCUIT_BREAKER', 'WATCHDOG_ALERT', etc.
    details TEXT NOT NULL,  -- JSON object with event details
    action_taken TEXT NOT NULL,  -- Description of action taken
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_trades_timestamp ON trades(timestamp);
CREATE INDEX IF NOT EXISTS idx_trades_symbol ON trades(symbol);
CREATE INDEX IF NOT EXISTS idx_trades_status ON trades(status);
CREATE INDEX IF NOT EXISTS idx_safety_events_timestamp ON safety_events(timestamp);
CREATE INDEX IF NOT EXISTS idx_safety_events_type ON safety_events(event_type);
