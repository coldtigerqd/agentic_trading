# 快速开始：10分钟增量数据同步

## 🎯 目标

每10分钟自动获取观察列表中所有股票的最新市场数据，并增量保存到本地数据库。

## ✅ 核心特性

- **增量更新**：只获取新数据，自动去重
- **10分钟周期**：可配置同步间隔
- **市场感知**：自动检测市场开盘状态
- **零维护**：设置一次，自动运行

---

## 📋 前置条件

1. **ThetaData MCP 已配置**：确保 `.mcp.json` 中有 ThetaData 配置
2. **数据库已初始化**：运行过 `schema.sql`
3. **观察列表已配置**：有活跃的观察列表股票

---

## 🚀 方法一：通过 Commander 自动同步（推荐）

在你的 Commander 工作流中添加以下代码：

```python
# ===== 增量数据同步 =====
from skills import sync_watchlist_incremental, process_snapshot_and_cache

# 检查是否需要同步
sync_info = sync_watchlist_incremental(skip_if_market_closed=True)

if sync_info['should_sync']:
    symbols = sync_info['symbols_to_sync']
    print(f"📊 Syncing {len(symbols)} symbols...")

    new_bars = 0
    for symbol in symbols:
        # 调用 ThetaData MCP
        snapshot = mcp__ThetaData__stock_snapshot_ohlc(symbol=[symbol])

        # 处理并缓存
        result = process_snapshot_and_cache(symbol, snapshot)

        if result['success'] and result['bars_added'] > 0:
            print(f"✅ {symbol}: New data")
            new_bars += 1

    print(f"✅ Sync complete: {new_bars} new bars")
else:
    print(f"⏭️  {sync_info['message']}")
```

**说明**：
- 每次 Commander 运行时会自动同步
- 如果市场关闭，会自动跳过
- 重复的数据自动忽略（零成本）

---

## 🚀 方法二：Cron 定时任务（生产环境）

### 步骤 1: 创建日志目录

```bash
mkdir -p logs
```

### 步骤 2: 测试脚本

```bash
# 单次运行测试
python runtime/data_sync_daemon.py --once
```

### 步骤 3: 配置 Cron

```bash
# 编辑 crontab
crontab -e

# 添加以下行（每10分钟运行）
*/10 * * * * cd /home/adt/project/agentic_trading && /usr/bin/python3 runtime/data_sync_daemon.py --once >> logs/data_sync_cron.log 2>&1
```

### 步骤 4: 验证

```bash
# 查看 cron 任务
crontab -l

# 等待10分钟后查看日志
tail -f logs/data_sync_cron.log
```

---

## 🚀 方法三：后台守护进程

### 启动守护进程

```bash
# 创建日志目录
mkdir -p logs

# 后台运行（每10分钟自动同步）
nohup python runtime/data_sync_daemon.py --interval 10 > logs/data_sync.log 2>&1 &

# 记录进程ID
echo $! > logs/data_sync.pid
```

### 查看日志

```bash
tail -f logs/data_sync.log
```

### 停止守护进程

```bash
# 方法 1: 使用 PID 文件
kill $(cat logs/data_sync.pid)

# 方法 2: 查找并杀死进程
pkill -f data_sync_daemon
```

---

## 📊 验证数据同步

### 1. 查看数据库内容

```bash
sqlite3 data_lake/trades.db "
  SELECT symbol,
         COUNT(*) as total_bars,
         MAX(timestamp) as latest
  FROM market_data_bars
  GROUP BY symbol
  ORDER BY symbol;
"
```

### 2. 检查数据新鲜度

```python
from skills import get_data_freshness_report

report = get_data_freshness_report()

for item in report['symbols']:
    status = "✅" if not item['is_stale'] else "❌"
    age = item['age_minutes'] or 'N/A'
    print(f"{status} {item['symbol']:6s}: {age} minutes ago")
```

### 3. 查看最新数据

```bash
sqlite3 data_lake/trades.db "
  SELECT symbol, timestamp, close
  FROM market_data_bars
  WHERE symbol = 'AAPL'
  ORDER BY timestamp DESC
  LIMIT 10;
"
```

---

## 🔧 调整同步间隔

### Cron 方式

```bash
# 每5分钟
*/5 * * * * cd /path/to/agentic_trading && python runtime/data_sync_daemon.py --once

# 每15分钟
*/15 * * * * cd /path/to/agentic_trading && python runtime/data_sync_daemon.py --once

# 每小时
0 * * * * cd /path/to/agentic_trading && python runtime/data_sync_daemon.py --once
```

### 守护进程方式

```bash
# 每5分钟
python runtime/data_sync_daemon.py --interval 5

# 每15分钟
python runtime/data_sync_daemon.py --interval 15

# 每30分钟
python runtime/data_sync_daemon.py --interval 30
```

---

## 📈 监控和日志

### 查看实时日志

```bash
# Cron 日志
tail -f logs/data_sync_cron.log

# 守护进程日志
tail -f logs/data_sync.log
```

### 日志示例

```
======================================================================
📊 Starting Data Sync Cycle
======================================================================
Market Status: REGULAR
Market Open: ✅ YES
📋 Symbols to sync: 12
📌 Symbols: SPY, QQQ, AAPL, MSFT, NVDA...
📈 Data freshness: 3/12 symbols stale

──────────────────────────────────────────────────────────────────────
Starting symbol-by-symbol sync...
──────────────────────────────────────────────────────────────────────

[1/12] Fetching SPY...
   ✅ SPY: New bar added @ 2025-11-20T10:30:00-05:00

[2/12] Fetching QQQ...
   ⏭️  QQQ: Duplicate (already in DB)

...

======================================================================
📊 Sync Cycle Complete
======================================================================
✅ Success:    12/12
🆕 New Bars:   3
⏭️  Duplicates: 9
❌ Failed:     0
⏱️  Duration:   2.45s
======================================================================

⏳ Waiting 10 minutes...
⏰ Next sync: 2025-11-20 10:40:00
```

---

## 🐛 故障排查

### 问题：Cron 不运行

```bash
# 检查 cron 服务
sudo systemctl status cron

# 查看系统日志
sudo grep CRON /var/log/syslog

# 确保使用绝对路径
which python3
# 使用输出的路径替换 crontab 中的 /usr/bin/python3
```

### 问题：数据库锁定

```bash
# 确保没有其他进程在写入数据库
lsof data_lake/trades.db

# 如果有，等待完成或杀死进程
```

### 问题：MCP 调用失败

**原因**：此系统需要在 Claude Code 环境中运行。

**解决**：
- 通过 Claude Code 会话运行
- 或配置独立 MCP 客户端（高级）

---

## 📚 更多信息

- **完整指南**：`docs/INCREMENTAL_SYNC_GUIDE.md`
- **数据持久化**：`docs/DATA_PERSISTENCE_GUIDE.md`
- **Skills API**：`skills/data_sync.py`

---

## ✅ 总结

选择最适合你的方法：

| 方法 | 适用场景 | 优点 | 缺点 |
|------|---------|------|------|
| **Commander 集成** | 交易策略运行时 | 简单，自动 | 依赖 Commander 周期 |
| **Cron 任务** | 生产环境 | 可靠，系统级 | 需要配置 cron |
| **守护进程** | 开发/测试 | 灵活，独立 | 需要手动管理进程 |

**推荐配置**：

- 开发环境：Commander 集成
- 生产环境：Cron 任务（每10分钟）

现在你已经有了一个**每10分钟自动增量同步**的可靠数据管道！ 🎉
