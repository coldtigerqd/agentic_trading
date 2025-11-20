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

-- Market data bars table: 5-minute OHLCV bars for historical analysis
CREATE TABLE IF NOT EXISTS market_data_bars (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    timestamp TEXT NOT NULL,  -- ISO format: 2025-11-20T09:30:00
    open REAL NOT NULL,
    high REAL NOT NULL,
    low REAL NOT NULL,
    close REAL NOT NULL,
    volume INTEGER NOT NULL,
    vwap REAL,  -- Volume-weighted average price
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(symbol, timestamp)
);

-- Watchlist table: Symbols to track for market data updates
CREATE TABLE IF NOT EXISTS watchlist (
    symbol TEXT PRIMARY KEY,
    added_at TEXT NOT NULL,
    active BOOLEAN DEFAULT 1,
    last_updated TEXT,
    priority INTEGER DEFAULT 0,  -- Higher priority symbols updated first
    notes TEXT  -- Optional metadata (strategy tags, etc.)
);

-- Data freshness table: Tracks data coverage and quality for each symbol
CREATE TABLE IF NOT EXISTS data_freshness (
    symbol TEXT PRIMARY KEY,
    oldest_bar TEXT,  -- Oldest bar timestamp in cache
    newest_bar TEXT,  -- Newest bar timestamp in cache
    bar_count INTEGER DEFAULT 0,
    last_checked TEXT,
    gaps_detected TEXT,  -- JSON array of detected gap ranges
    FOREIGN KEY (symbol) REFERENCES watchlist(symbol)
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_trades_timestamp ON trades(timestamp);
CREATE INDEX IF NOT EXISTS idx_trades_symbol ON trades(symbol);
CREATE INDEX IF NOT EXISTS idx_trades_status ON trades(status);
CREATE INDEX IF NOT EXISTS idx_safety_events_timestamp ON safety_events(timestamp);
CREATE INDEX IF NOT EXISTS idx_safety_events_type ON safety_events(event_type);

-- Indexes for market data queries
CREATE INDEX IF NOT EXISTS idx_bars_symbol ON market_data_bars(symbol);
CREATE INDEX IF NOT EXISTS idx_bars_timestamp ON market_data_bars(timestamp);
CREATE INDEX IF NOT EXISTS idx_bars_symbol_timestamp ON market_data_bars(symbol, timestamp);
CREATE INDEX IF NOT EXISTS idx_watchlist_active ON watchlist(active);
CREATE INDEX IF NOT EXISTS idx_watchlist_priority ON watchlist(priority DESC);
