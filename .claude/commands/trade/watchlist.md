# Trade Watchlist Command

显示当前观察列表，包括所有标的、优先级和数据新鲜度状态。

请运行以下 Python 代码：

```python
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta

DB_PATH = Path("data_lake/trades.db")

def get_data_freshness_status(timestamp_str):
    """根据时间戳判断数据新鲜度"""
    if not timestamp_str:
        return "✗ CRITICAL", "No data"

    try:
        ts = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        now = datetime.now(ts.tzinfo) if ts.tzinfo else datetime.now()
        age = now - ts

        if age <= timedelta(hours=24):
            return "✓ GOOD", timestamp_str
        elif age <= timedelta(days=7):
            return "⚠ STALE", timestamp_str
        else:
            return "✗ CRITICAL", timestamp_str
    except:
        return "✗ CRITICAL", "Invalid timestamp"

conn = sqlite3.connect(str(DB_PATH))
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# 获取观察列表和数据新鲜度信息
cursor.execute("""
    SELECT
        w.symbol,
        w.priority,
        w.notes,
        w.active,
        w.added_at,
        df.newest_bar,
        df.bar_count
    FROM watchlist w
    LEFT JOIN data_freshness df ON w.symbol = df.symbol
    WHERE w.active = 1
    ORDER BY w.priority DESC, w.symbol
""")

results = cursor.fetchall()

print("=" * 90)
print("当前观察列表")
print("=" * 90)
print()

if not results:
    print("观察列表为空")
    print()
    print("提示：使用以下命令添加标的：")
    print("  /trade:watchlist-add SYMBOL")
else:
    print(f"{'标的':<10} {'优先级':>8} {'状态':<15} {'最新数据':<25} {'数据条数':>12}")
    print("-" * 90)

    good_count = 0
    stale_count = 0
    critical_count = 0

    for row in results:
        status, latest = get_data_freshness_status(row['newest_bar'])
        bar_count = row['bar_count'] or 0

        # 统计数据质量
        if "GOOD" in status:
            good_count += 1
        elif "STALE" in status:
            stale_count += 1
        else:
            critical_count += 1

        print(f"{row['symbol']:<10} {row['priority']:>8} {status:<15} {latest:<25} {bar_count:>12,}")

        if row['notes']:
            print(f"  备注: {row['notes']}")

    print("-" * 90)
    print(f"总计: {len(results)} 个标的 | 数据状态: {good_count} GOOD, {stale_count} STALE, {critical_count} CRITICAL")

print()
print("=" * 90)

conn.close()
```

运行完成后，向用户汇报观察列表状态。
