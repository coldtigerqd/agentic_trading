# 市场数据持久化指南

## 概述

Agentic AlphaHive系统使用SQLite数据库存储市场数据，支持多时间周期的OHLCV（开高低收量）数据持久化。

## 数据库架构

### 主数据库: `data_lake/trades.db`

系统使用统一的 `trades.db` 数据库存储所有数据，包括：

#### 1. `market_data_bars` 表 - 市场数据缓存

```sql
CREATE TABLE market_data_bars (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,              -- 股票代码（如 "AAPL"）
    interval TEXT NOT NULL,             -- 时间周期（"5min", "15min", "1h", "daily"）
    timestamp TEXT NOT NULL,            -- ISO格式时间戳
    open REAL NOT NULL,                 -- 开盘价
    high REAL NOT NULL,                 -- 最高价
    low REAL NOT NULL,                  -- 最低价
    close REAL NOT NULL,                -- 收盘价
    volume INTEGER NOT NULL,            -- 成交量
    vwap REAL,                          -- 成交量加权平均价
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(symbol, interval, timestamp) -- 防止重复数据
);
```

**索引**（用于快速查询）:
- `idx_bars_symbol`: 按代码查询
- `idx_bars_timestamp`: 按时间查询
- `idx_bars_symbol_interval`: 按代码和周期查询
- `idx_bars_symbol_interval_timestamp`: 复合索引，最快查询

#### 2. `watchlist` 表 - 观察列表

```sql
CREATE TABLE watchlist (
    symbol TEXT PRIMARY KEY,
    added_at TEXT NOT NULL,
    active BOOLEAN DEFAULT 1,
    last_updated TEXT,
    priority INTEGER DEFAULT 0,    -- 优先级（越高越先更新）
    notes TEXT                      -- 备注（策略标签等）
);
```

#### 3. `trades` 表 - 交易记录

记录所有订单提交和执行情况（详见交易数据库文档）。

#### 4. `safety_events` 表 - 安全事件

记录所有安全层拦截和熔断触发事件。

## 数据持久化方式

### 方法 1: 使用 populate_market_data.py 脚本（推荐用于测试）

这是最简单的方式，适合快速填充示例数据进行测试：

```bash
# 添加默认观察列表并填充30天数据
python scripts/populate_market_data.py --add-default --days 30

# 为特定代码填充数据
python scripts/populate_market_data.py --symbols AAPL,NVDA,TSLA --days 60

# 为现有观察列表填充数据
python scripts/populate_market_data.py --watchlist --days 45
```

**特点**:
- ✅ 快速：每个代码约0.02秒
- ✅ 生成真实感的随机游走数据
- ⚠️  仅用于测试：数据是模拟的，不是真实市场数据

### 方法 2: 通过 ThetaData MCP 获取真实数据（生产环境）

在生产环境中，应该使用ThetaData MCP工具获取真实市场数据：

#### Python代码示例

```python
from runtime.data_fetcher import process_thetadata_ohlc
from data_lake.market_data_manager import insert_bars, OHLCVBar

# 方式 A: Claude Code调用MCP工具（推荐）
# 在Commander工作流程中，Claude Code会自动调用：

# 1. 获取OHLC快照
ohlc_result = mcp__ThetaData__stock_snapshot_ohlc(symbol="AAPL")

# 2. 处理并缓存数据
from runtime.data_fetcher import process_thetadata_ohlc
cached = process_thetadata_ohlc("AAPL", ohlc_result)

if cached["success"]:
    print(f"✓ 已缓存 {cached['symbol']} 数据")

# 方式 B: 手动构造并插入（适用于批量导入）
bars = []
for data_point in your_data_source:
    bar = OHLCVBar(
        symbol="AAPL",
        timestamp=data_point["timestamp"],  # ISO格式
        open=data_point["open"],
        high=data_point["high"],
        low=data_point["low"],
        close=data_point["close"],
        volume=data_point["volume"],
        vwap=data_point.get("vwap")  # 可选
    )
    bars.append(bar)

# 批量插入
from data_lake.market_data_manager import insert_bars
count = insert_bars("AAPL", bars)
print(f"✓ 插入了 {count} 条数据")
```

### 方法 3: 后台自动更新（运行时）

系统支持在runtime中设置后台任务，自动更新观察列表数据：

```python
# 在 runtime/main_loop.py 中
import asyncio
from runtime.data_fetcher import (
    is_trading_hours,
    get_active_watchlist,
    process_thetadata_ohlc
)

async def market_data_updater_task():
    """后台市场数据更新任务"""
    while True:
        try:
            if is_trading_hours():  # 仅在交易时段更新
                watchlist = get_active_watchlist()

                for symbol_info in watchlist:
                    symbol = symbol_info["symbol"]

                    try:
                        # Claude Code调用ThetaData MCP
                        ohlc_data = mcp__ThetaData__stock_snapshot_ohlc(
                            symbol=symbol
                        )

                        # 处理并缓存
                        result = process_thetadata_ohlc(symbol, ohlc_data)

                        if result["success"]:
                            print(f"✓ 更新 {symbol}")

                    except Exception as e:
                        print(f"✗ 获取 {symbol} 失败: {e}")

            # 每5分钟更新一次
            await asyncio.sleep(300)

        except Exception as e:
            print(f"✗ 更新任务错误: {e}")
            await asyncio.sleep(60)  # 出错后1分钟重试

# 启动任务
asyncio.create_task(market_data_updater_task())
```

## 数据查询

### 使用Skills库查询（推荐）

```python
from skills import get_historical_bars, get_latest_price, get_multi_timeframe_data

# 1. 获取历史K线数据
result = get_historical_bars(
    symbol="AAPL",
    interval="5min",  # "5min", "15min", "1h", "daily"
    lookback_days=30
)

if result["cache_hit"]:
    print(f"✓ 获取了 {result['bar_count']} 条K线")
    for bar in result["bars"][:5]:
        print(f"{bar['timestamp']}: ${bar['close']}")
else:
    print(f"⚠️  缓存未命中，需要回填数据")

# 2. 获取最新价格
latest = get_latest_price("NVDA")
if latest["success"]:
    print(f"NVDA最新价: ${latest['price']:.2f}")
    print(f"数据时效: {latest['age_seconds']}秒前")
    if latest["is_stale"]:
        print("⚠️  数据已过时")

# 3. 多时间周期数据（最高效）
mtf_data = get_multi_timeframe_data(
    symbol="SPY",
    intervals=["5min", "1h", "daily"],
    lookback_days=30
)

for interval, data in mtf_data["timeframes"].items():
    print(f"{interval}: {data['bar_count']} 条K线")
```

### 直接SQL查询

```python
import sqlite3
from pathlib import Path

db_path = Path("data_lake/trades.db")
conn = sqlite3.connect(str(db_path))
conn.row_factory = sqlite3.Row  # 允许按列名访问
cursor = conn.cursor()

# 查询最近100条5分钟K线
cursor.execute("""
    SELECT timestamp, open, high, low, close, volume
    FROM market_data_bars
    WHERE symbol = ? AND interval = ?
    ORDER BY timestamp DESC
    LIMIT 100
""", ("AAPL", "5min"))

bars = cursor.fetchall()
for bar in bars[:5]:
    print(f"{bar['timestamp']}: O=${bar['open']:.2f} H=${bar['high']:.2f} "
          f"L=${bar['low']:.2f} C=${bar['close']:.2f} V={bar['volume']:,}")

conn.close()
```

## 数据质量验证

系统提供自动数据质量验证：

```python
from skills.data_quality import validate_data_quality

result = validate_data_quality(
    symbols=["AAPL", "NVDA", "SPY"],
    min_daily_bars=30,      # 最少30条日线
    min_hourly_bars=50,     # 最少50条小时线
    min_5min_bars=390,      # 最少390条5分钟线（约3个交易日）
    max_age_hours=1.0,      # 数据不超过1小时（市场开盘时）
    require_all_intervals=True  # 是否要求所有时间周期都有数据
)

if result["valid"]:
    print(f"✓ 数据质量验证通过！")
    print(f"  通过: {len(result['symbols_passed'])} 个代码")
else:
    print(f"✗ 数据质量验证失败")
    print(f"  失败: {len(result['symbols_failed'])} 个代码")
    print(f"\n问题:")
    for issue in result["issues"]:
        print(f"  [{issue['severity']}] {issue['symbol']}: {issue['issue']}")
```

## 观察列表管理

```python
from skills import add_to_watchlist, remove_from_watchlist, get_watchlist

# 添加代码到观察列表
add_to_watchlist(
    symbol="TSLA",
    priority=8,  # 优先级（越高越先更新）
    notes="高动量科技股"
)

# 获取观察列表
watchlist = get_watchlist()
print(f"观察列表: {watchlist['total_count']} 个代码")
for sym in watchlist['symbols']:
    print(f"  {sym['symbol']}: 优先级 {sym['priority']}")

# 移除代码（软删除，保留数据）
remove_from_watchlist("TSLA")
```

## 数据聚合（多时间周期）

系统支持从5分钟基础数据自动聚合到更大周期：

```python
from data_lake.market_data_manager import get_bars
from datetime import datetime, timedelta

symbol = "AAPL"
end = datetime.now()
start = end - timedelta(days=7)

# 自动聚合到不同周期
bars_5min = get_bars(symbol, start, end, interval="5min")
bars_15min = get_bars(symbol, start, end, interval="15min")  # 自动聚合
bars_1h = get_bars(symbol, start, end, interval="1h")        # 自动聚合
bars_daily = get_bars(symbol, start, end, interval="daily")  # 自动聚合

print(f"5分钟: {len(bars_5min)} 条")
print(f"15分钟: {len(bars_15min)} 条")
print(f"1小时: {len(bars_1h)} 条")
print(f"日线: {len(bars_daily)} 条")
```

## 最佳实践

### 1. 初始化系统

```bash
# 1. 创建数据库（已自动完成）
# 2. 添加观察列表并填充数据
python scripts/populate_market_data.py --add-default --days 60

# 3. 验证数据
python -c "
from skills.data_quality import validate_data_quality
result = validate_data_quality(['AAPL', 'SPY'], min_5min_bars=100, max_age_hours=None)
print('验证结果:', result['summary'])
"
```

### 2. 生产环境数据流

```
ThetaData MCP → process_thetadata_ohlc() → market_data_bars表
                                           ↓
                            数据质量验证 → Swarm Intelligence → 交易决策
```

### 3. 性能优化

- ✅ 使用索引：所有查询都应利用 `(symbol, interval, timestamp)` 索引
- ✅ 批量插入：使用 `insert_bars()` 批量插入，而非逐条插入
- ✅ 缓存策略：高频查询的数据应缓存在内存中
- ✅ 定期维护：定期运行 `VACUUM` 和 `ANALYZE` 优化数据库

### 4. 数据备份

```bash
# 备份数据库
cp data_lake/trades.db data_lake/trades.db.backup.$(date +%Y%m%d)

# 或使用SQLite备份命令
sqlite3 data_lake/trades.db ".backup data_lake/trades.db.backup"
```

## 故障排查

### 问题：数据质量验证失败

```bash
# 检查数据库内容
python -c "
import sqlite3
conn = sqlite3.connect('data_lake/trades.db')
cursor = conn.cursor()
cursor.execute('SELECT symbol, interval, COUNT(*) FROM market_data_bars GROUP BY symbol, interval')
for row in cursor.fetchall():
    print(row)
"
```

### 问题：缓存未命中

**原因**：数据库中没有足够的历史数据

**解决**：
```bash
# 填充更多历史数据
python scripts/populate_market_data.py --symbols AAPL --days 90
```

### 问题：ThetaData API限流

**解决**：
- 使用重试机制（`fetch_with_retry`）
- 增加请求间隔
- 批量获取数据而非逐个请求

## 技术指标计算

所有技术指标都依赖市场数据缓存：

```python
from skills import (
    calculate_sma,
    calculate_rsi,
    calculate_bollinger_bands,
    calculate_macd,
    get_historical_bars
)

# 获取数据
bars_result = get_historical_bars("AAPL", "daily", lookback_days=60)
bars = bars_result["bars"]

# 提取收盘价
closes = [bar["close"] for bar in bars]

# 计算技术指标
sma_20 = calculate_sma(closes, period=20)
rsi_14 = calculate_rsi(closes, period=14)
bb = calculate_bollinger_bands(closes, period=20, std_dev=2)
macd = calculate_macd(closes, fast=12, slow=26, signal=9)

print(f"SMA(20): {sma_20[-1]:.2f}")
print(f"RSI(14): {rsi_14[-1]:.2f}")
print(f"BB Upper: {bb['upper'][-1]:.2f}")
print(f"MACD: {macd['macd'][-1]:.4f}")
```

## 总结

数据持久化是Agentic AlphaHive系统的核心基础设施：

1. **统一存储**：所有数据存储在 `trades.db` 数据库
2. **多时间周期**：支持5分钟、15分钟、1小时、日线数据
3. **自动验证**：内置数据质量检查，确保数据可靠性
4. **高效查询**：完善的索引系统，支持快速查询
5. **灵活集成**：可与ThetaData MCP、技术指标、Swarm Intelligence无缝集成

遵循本指南，您可以建立一个可靠、高效的市场数据持久化系统，为自动化交易提供坚实的数据基础。
