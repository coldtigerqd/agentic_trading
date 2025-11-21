-- 数据库性能优化索引
-- 创建时间: 2025-11-21
-- 用途: 优化常见查询模式的性能

-- =============================================================================
-- 1. data_freshness 表优化
-- =============================================================================
-- 用于快速查找过期数据
CREATE INDEX IF NOT EXISTS idx_freshness_newest_bar
ON data_freshness(newest_bar DESC);

-- 用于监控活跃标的
CREATE INDEX IF NOT EXISTS idx_freshness_symbol_newest
ON data_freshness(symbol, newest_bar DESC);

-- =============================================================================
-- 2. trades 表优化
-- =============================================================================
-- 用于按信号源查询交易（分析蜂群实例表现）
CREATE INDEX IF NOT EXISTS idx_trades_signal_source
ON trades(signal_source, timestamp DESC);

-- 用于分析特定策略表现
CREATE INDEX IF NOT EXISTS idx_trades_strategy
ON trades(strategy, timestamp DESC);

-- 用于查询盈亏分析
CREATE INDEX IF NOT EXISTS idx_trades_pnl
ON trades(pnl, timestamp DESC)
WHERE pnl IS NOT NULL;

-- 用于实时监控待处理订单
CREATE INDEX IF NOT EXISTS idx_trades_status_timestamp
ON trades(status, timestamp DESC);

-- =============================================================================
-- 3. watchlist 表优化
-- =============================================================================
-- 用于按优先级查询活跃标的（数据同步中使用）
CREATE INDEX IF NOT EXISTS idx_watchlist_active_priority
ON watchlist(active, priority DESC)
WHERE active = 1;

-- =============================================================================
-- 4. market_data_bars 表额外优化
-- =============================================================================
-- 覆盖索引：用于最新价格查询（避免回表）
-- 注意：SQLite不支持INCLUDE语法，但复合索引可以提供覆盖效果
CREATE INDEX IF NOT EXISTS idx_bars_latest_price
ON market_data_bars(symbol, timestamp DESC, close);

-- 用于多时间周期数据查询优化
CREATE INDEX IF NOT EXISTS idx_bars_volume_analysis
ON market_data_bars(symbol, timestamp, volume)
WHERE volume > 0;

-- =============================================================================
-- 5. safety_events 表优化
-- =============================================================================
-- 用于按事件类型和时间分析安全事件
CREATE INDEX IF NOT EXISTS idx_safety_events_type_timestamp
ON safety_events(event_type, timestamp DESC);

-- =============================================================================
-- 查询性能分析
-- =============================================================================
-- 运行此脚本后，可以使用 EXPLAIN QUERY PLAN 来验证索引是否被使用
-- 示例:
--   EXPLAIN QUERY PLAN
--   SELECT close FROM market_data_bars
--   WHERE symbol = 'AAPL'
--   ORDER BY timestamp DESC
--   LIMIT 1;
