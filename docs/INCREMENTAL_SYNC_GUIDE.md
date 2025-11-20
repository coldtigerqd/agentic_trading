# 增量数据同步指南

## 概述

本系统提供**每10分钟自动增量同步**市场数据的功能，只获取新数据，自动去重，避免重复存储。

## 核心特性

### ✅ 增量更新
- **自动去重**：数据库 `UNIQUE(symbol, interval, timestamp)` 约束自动忽略重复数据
- **零重复成本**：重复调用不会增加存储空间
- **智能检测**：`process_snapshot_and_cache()` 返回 `bars_added=0` 表示数据已存在

### ✅ 市场感知
- **交易时段检测**：只在市场开盘时主动同步
- **市场关闭时**：可选择跳过同步或继续获取快照
- **时区支持**：自动处理美东时间（ET）

### ✅ 数据新鲜度
- **过时检测**：超过15分钟的数据标记为 `is_stale`
- **新鲜度报告**：`get_data_freshness_report()` 提供详细状态
- **自动时间戳**：四舍五入到5分钟间隔

---

## 架构设计

```
┌─────────────────────────────────────────────────────────────┐
│                    Commander / Cron Job                      │
│                                                               │
│  每10分钟触发一次同步周期                                     │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              Skills: sync_watchlist_incremental()            │
│                                                               │
│  1. 检查市场状态（是否开盘）                                  │
│  2. 获取观察列表（活跃股票）                                  │
│  3. 返回需要同步的股票列表                                    │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│          对每个股票调用 ThetaData MCP                         │
│                                                               │
│  mcp__ThetaData__stock_snapshot_ohlc(symbol=[symbol])        │
│                                                               │
│  返回: {open, high, low, close, volume, vwap}                │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│         Skills: process_snapshot_and_cache()                 │
│                                                               │
│  1. 生成时间戳（四舍五入到5分钟）                             │
│  2. 构造 OHLCVBar 对象                                        │
│  3. 插入数据库（自动去重）                                    │
│  4. 返回 bars_added (0=已存在, 1=新增)                       │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              SQLite: data_lake/trades.db                     │
│                                                               │
│  market_data_bars 表:                                         │
│    - UNIQUE(symbol, interval, timestamp) → 自动去重           │
│    - 索引优化，快速查询                                       │
└─────────────────────────────────────────────────────────────┘
```

---

## 使用方法

### 方法 1: Commander 工作流集成（推荐）

在 Commander 系统提示中添加数据同步步骤：

```python
from skills import (
    sync_watchlist_incremental,
    process_snapshot_and_cache,
    get_data_freshness_report
)

# ===== 数据同步工作流 =====

# 1. 检查是否需要同步
sync_info = sync_watchlist_incremental(skip_if_market_closed=True)

if not sync_info['should_sync']:
    print(f"⏭️  Skip sync: {sync_info['message']}")
else:
    symbols = sync_info['symbols_to_sync']
    print(f"📊 Syncing {len(symbols)} symbols...")

    # 2. 同步每个股票
    new_bars_count = 0
    for symbol in symbols:
        # 调用 ThetaData MCP 获取快照
        snapshot = mcp__ThetaData__stock_snapshot_ohlc(symbol=[symbol])

        # 处理并缓存
        result = process_snapshot_and_cache(symbol, snapshot)

        if result['success']:
            if result['bars_added'] > 0:
                print(f"✅ {symbol}: New data @ {result['timestamp']}")
                new_bars_count += 1
            else:
                print(f"⏭️  {symbol}: Duplicate (skipped)")
        else:
            print(f"❌ {symbol}: {result['error']}")

    print(f"\n✅ Sync complete: {new_bars_count} new bars added")
```

### 方法 2: 定时任务（Cron）

**每10分钟自动同步**：

```bash
# 编辑 crontab
crontab -e

# 添加以下行（每10分钟运行一次）
*/10 * * * * cd /home/adt/project/agentic_trading && /usr/bin/python3 runtime/data_sync_daemon.py --once >> logs/data_sync.log 2>&1
```

**验证 cron 任务**：

```bash
# 查看当前 cron 任务
crontab -l

# 查看日志
tail -f logs/data_sync.log
```

### 方法 3: 后台守护进程

**持续运行（自带10分钟循环）**：

```bash
# 创建日志目录
mkdir -p logs

# 后台运行守护进程
nohup python runtime/data_sync_daemon.py --interval 10 > logs/data_sync.log 2>&1 &

# 查看进程
ps aux | grep data_sync_daemon

# 查看日志
tail -f logs/data_sync.log

# 停止守护进程
pkill -f data_sync_daemon
```

### 方法 4: systemd 服务（推荐生产环境）

创建服务文件 `/etc/systemd/system/agentic-data-sync.service`：

```ini
[Unit]
Description=Agentic AlphaHive Data Sync Daemon
After=network.target

[Service]
Type=simple
User=adt
WorkingDirectory=/home/adt/project/agentic_trading
ExecStart=/usr/bin/python3 runtime/data_sync_daemon.py --interval 10
Restart=on-failure
RestartSec=30
StandardOutput=append:/home/adt/project/agentic_trading/logs/data_sync.log
StandardError=append:/home/adt/project/agentic_trading/logs/data_sync.log

[Install]
WantedBy=multi-user.target
```

**管理服务**：

```bash
# 重载服务配置
sudo systemctl daemon-reload

# 启动服务
sudo systemctl start agentic-data-sync

# 设置开机自启
sudo systemctl enable agentic-data-sync

# 查看状态
sudo systemctl status agentic-data-sync

# 查看日志
journalctl -u agentic-data-sync -f
```

---

## Skills API 参考

### `sync_watchlist_incremental()`

检查哪些股票需要同步。

**参数**：
- `skip_if_market_closed: bool = True` - 市场关闭时是否跳过
- `max_symbols: int = None` - 最多同步多少个（用于测试）

**返回**：
```python
{
    'should_sync': bool,              # 是否应该同步
    'market_status': {                # 市场状态
        'session': 'regular',         # 会话类型
        'market_open': True           # 是否开盘
    },
    'symbols_to_sync': ['AAPL', ...], # 需要同步的股票列表
    'total_symbols': 10,              # 总股票数
    'message': 'Ready to sync...'     # 状态消息
}
```

### `process_snapshot_and_cache()`

处理 ThetaData 快照并缓存到数据库。

**参数**：
- `symbol: str` - 股票代码
- `snapshot_data: Dict` - ThetaData MCP 返回的快照

**返回**：
```python
{
    'success': True,
    'symbol': 'AAPL',
    'bars_added': 1,          # 0 = 已存在, 1 = 新增
    'timestamp': '2025-11-20T10:30:00-05:00',
    'bar': {...}              # OHLCV 数据
}
```

### `get_data_freshness_report()`

获取数据新鲜度报告。

**参数**：
- `symbols: List[str] = None` - 要检查的股票（None = 所有观察列表股票）

**返回**：
```python
{
    'timestamp': '2025-11-20T10:35:00-05:00',
    'symbols': [
        {
            'symbol': 'AAPL',
            'latest_timestamp': '2025-11-20T10:30:00-05:00',
            'age_minutes': 5.2,
            'is_stale': False  # > 15分钟为 True
        }
    ]
}
```

---

## 数据库自动去重机制

### UNIQUE 约束

```sql
CREATE TABLE market_data_bars (
    ...
    symbol TEXT NOT NULL,
    interval TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    ...
    UNIQUE(symbol, interval, timestamp)  -- 自动去重
);
```

### 去重行为

```python
# 第一次插入
bar1 = OHLCVBar(symbol='AAPL', timestamp='2025-11-20T10:30:00', ...)
count = insert_bars('AAPL', [bar1])
# count = 1  ✅ 新增

# 第二次插入（相同时间戳）
bar2 = OHLCVBar(symbol='AAPL', timestamp='2025-11-20T10:30:00', ...)
count = insert_bars('AAPL', [bar2])
# count = 0  ⏭️  跳过（不报错）

# 不同时间戳
bar3 = OHLCVBar(symbol='AAPL', timestamp='2025-11-20T10:35:00', ...)
count = insert_bars('AAPL', [bar3])
# count = 1  ✅ 新增
```

### 时间戳生成规则

```python
from datetime import datetime
import pytz

ET = pytz.timezone('US/Eastern')

# 当前时间: 10:32:47
now = datetime.now(ET)

# 四舍五入到5分钟
minutes = (now.minute // 5) * 5  # 32 // 5 * 5 = 30
timestamp = now.replace(minute=minutes, second=0, microsecond=0)

# 结果: 2025-11-20T10:30:00-05:00
```

**时间戳映射表**：

| 实际时间 | 四舍五入 | 时间戳 |
|---------|---------|--------|
| 10:00:00 | 10:00 | `10:00:00` |
| 10:02:30 | 10:00 | `10:00:00` |
| 10:04:59 | 10:00 | `10:00:00` |
| 10:05:00 | 10:05 | `10:05:00` |
| 10:07:15 | 10:05 | `10:05:00` |
| 10:09:59 | 10:05 | `10:05:00` |
| 10:10:00 | 10:10 | `10:10:00` |

---

## 测试和验证

### 1. 演示脚本

```bash
# 运行演示脚本（展示工作流）
python scripts/demo_incremental_sync.py
```

### 2. 单次同步测试

```bash
# 运行一次完整同步
python runtime/data_sync_daemon.py --once
```

### 3. 验证数据

```bash
# 检查数据库内容
sqlite3 data_lake/trades.db "
  SELECT symbol, COUNT(*) as bars,
         MIN(timestamp) as earliest,
         MAX(timestamp) as latest
  FROM market_data_bars
  GROUP BY symbol
  ORDER BY symbol;
"

# 检查最新数据时间戳
sqlite3 data_lake/trades.db "
  SELECT symbol, timestamp, close
  FROM market_data_bars
  WHERE symbol = 'AAPL'
  ORDER BY timestamp DESC
  LIMIT 5;
"
```

### 4. 数据新鲜度检查

```python
from skills import get_data_freshness_report

report = get_data_freshness_report(['AAPL', 'NVDA', 'SPY'])

for item in report['symbols']:
    status = "✅ Fresh" if not item['is_stale'] else "❌ Stale"
    age = item['age_minutes'] or 'N/A'
    print(f"{item['symbol']:6s}: {status} ({age} minutes ago)")
```

---

## 故障排查

### 问题 1: cron 任务不执行

**症状**：cron 任务没有运行，日志文件为空。

**解决**：

```bash
# 1. 检查 cron 服务状态
sudo systemctl status cron

# 2. 检查 cron 日志
sudo grep CRON /var/log/syslog

# 3. 确保脚本有执行权限
chmod +x runtime/data_sync_daemon.py

# 4. 使用绝对路径
*/10 * * * * /usr/bin/python3 /home/adt/project/agentic_trading/runtime/data_sync_daemon.py --once
```

### 问题 2: MCP 调用失败

**症状**：脚本运行但无法调用 ThetaData MCP。

**解决**：

这个系统需要在 **Claude Code 环境**中运行才能访问 MCP 工具。

**两种运行方式**：

1. **通过 Claude Code**：在 Claude Code 会话中运行
2. **独立 MCP 客户端**：配置 `.mcp.json` 并使用 MCP 客户端库

### 问题 3: 数据重复

**症状**：相同时间戳的数据被插入多次。

**检查**：

```bash
# 检查是否有重复数据
sqlite3 data_lake/trades.db "
  SELECT symbol, timestamp, COUNT(*) as duplicates
  FROM market_data_bars
  GROUP BY symbol, timestamp
  HAVING COUNT(*) > 1;
"
```

**解决**：

理论上不应该发生（有 UNIQUE 约束），如果发生则检查：
- 数据库是否正确初始化（运行 `schema.sql`）
- `insert_bars()` 是否使用 `INSERT OR IGNORE` 语法

### 问题 4: 数据过时

**症状**：`get_data_freshness_report()` 显示所有数据都 `is_stale`。

**解决**：

```bash
# 1. 检查市场是否开盘
python -c "
from skills.market_calendar import get_market_session_info
print(get_market_session_info())
"

# 2. 手动运行一次同步
python runtime/data_sync_daemon.py --once

# 3. 检查同步日志
tail -f logs/data_sync.log
```

---

## 性能优化

### 1. 批量获取（推荐）

如果 ThetaData MCP 支持批量获取，使用批量调用：

```python
# 批量获取（假设 MCP 支持）
symbols = ['AAPL', 'NVDA', 'TSLA', 'SPY']
batch_result = mcp__ThetaData__stock_snapshot_ohlc(symbol=symbols)

# 批量处理
for symbol, snapshot in batch_result.items():
    process_snapshot_and_cache(symbol, snapshot)
```

### 2. 并发处理

使用 `concurrent.futures` 并发处理多个股票：

```python
from concurrent.futures import ThreadPoolExecutor

def sync_symbol(symbol):
    snapshot = mcp__ThetaData__stock_snapshot_ohlc(symbol=[symbol])
    return process_snapshot_and_cache(symbol, snapshot)

symbols = sync_info['symbols_to_sync']

with ThreadPoolExecutor(max_workers=5) as executor:
    results = list(executor.map(sync_symbol, symbols))

new_bars = sum(r['bars_added'] for r in results if r['success'])
print(f"✅ Added {new_bars} new bars")
```

### 3. 数据库优化

```sql
-- 定期运行 VACUUM 和 ANALYZE
VACUUM;
ANALYZE;

-- 检查索引使用情况
EXPLAIN QUERY PLAN
SELECT * FROM market_data_bars
WHERE symbol = 'AAPL' AND interval = '5min'
ORDER BY timestamp DESC
LIMIT 100;
```

---

## 总结

增量数据同步系统的关键点：

1. **自动去重**：依赖数据库 UNIQUE 约束，无需手动检查
2. **市场感知**：只在交易时段主动同步，避免无效调用
3. **灵活部署**：支持 Commander 集成、Cron、守护进程、systemd 服务
4. **数据质量**：提供新鲜度检查，确保数据可靠性
5. **安全增量**：重复调用不会导致错误或数据膨胀

遵循本指南，你可以建立一个**每10分钟自动增量同步**的可靠数据管道！
