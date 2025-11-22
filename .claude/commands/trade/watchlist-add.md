---
description: "添加标的 - 将股票添加到观察列表"
---

# Trade Watchlist Add Command

添加一个或多个标的到观察列表。

**用法**:
```
/trade:watchlist-add SYMBOL [SYMBOL2 ...] [优先级] [备注]
```

**示例**:
- 添加单个标的（默认优先级5）: `AAPL`
- 添加多个标的: `GOOGL META TSLA`
- 指定优先级（1-10）: `NVDA 优先级=1`
- 添加备注: `AMD 优先级=3 备注=半导体板块`

请根据用户提供的参数，运行以下 Python 代码添加标的：

```python
import sqlite3
import re
from pathlib import Path
from datetime import datetime

DB_PATH = Path("data_lake/trades.db")

# 从用户输入解析参数（示例：["AAPL", "MSFT", "priority=3", "notes=科技股"]）
user_input = """USER_SYMBOLS_HERE"""  # 替换为用户实际输入

symbols = []
priority = 5  # 默认优先级
notes = None

# 解析输入
parts = user_input.strip().split()
for part in parts:
    part_lower = part.lower()
    if '=' in part_lower:
        key, value = part.split('=', 1)
        if 'prior' in key.lower():  # priority, 优先级
            try:
                priority = int(value)
                if not 1 <= priority <= 10:
                    print("错误：优先级必须在 1-10 之间")
                    exit(1)
            except ValueError:
                print(f"错误：无效的优先级 '{value}'")
                exit(1)
        elif 'note' in key.lower() or '备注' in key:
            notes = value
    else:
        # 假定是标的符号，转换为大写
        symbols.append(part.upper())

# 验证标的格式
def validate_symbol(symbol):
    return bool(re.match(r'^[A-Z]{2,5}$', symbol))

# 连接数据库
conn = sqlite3.connect(str(DB_PATH))
cursor = conn.cursor()

print("=" * 70)
print("添加标的到观察列表")
print("=" * 70)
print()

success_count = 0
added_symbols = []

for symbol in symbols:
    if not validate_symbol(symbol):
        print(f"✗ {symbol}: 无效格式（必须是2-5个大写字母）")
        continue

    # 检查是否已存在
    cursor.execute("SELECT active FROM watchlist WHERE symbol = ?", (symbol,))
    existing = cursor.fetchone()

    try:
        if existing:
            # 更新现有标的
            cursor.execute("""
                UPDATE watchlist
                SET priority = ?, notes = ?, active = 1, last_updated = ?
                WHERE symbol = ?
            """, (priority, notes, datetime.now().isoformat(), symbol))
            conn.commit()

            if existing[0] == 1:
                print(f"ℹ {symbol}: 已在观察列表中，已更新优先级为 {priority}")
            else:
                print(f"✓ {symbol}: 重新激活（优先级={priority}）")
                added_symbols.append(symbol)
        else:
            # 插入新标的
            cursor.execute("""
                INSERT INTO watchlist (symbol, added_at, priority, notes, active)
                VALUES (?, ?, ?, ?, 1)
            """, (symbol, datetime.now().isoformat(), priority, notes))

            # 初始化数据新鲜度记录
            cursor.execute("""
                INSERT OR IGNORE INTO data_freshness (symbol, bar_count, last_checked)
                VALUES (?, 0, ?)
            """, (symbol, datetime.now().isoformat()))

            conn.commit()
            print(f"✓ {symbol}: 已添加（优先级={priority}）")
            added_symbols.append(symbol)

        success_count += 1

    except Exception as e:
        conn.rollback()
        print(f"✗ {symbol}: 添加失败 - {str(e)}")

conn.close()

if notes:
    print(f"\n备注: {notes}")

print()
print(f"成功添加/更新: {success_count}/{len(symbols)} 个标的")

if added_symbols:
    print()
    print("下一步：")
    print(f"  运行回填获取历史数据：")
    print(f"  python scripts/backfill_historical_data.py --symbols {','.join(added_symbols)} --days 1095")
    print()
    print(f"  或等待每日同步守护进程自动填充数据")

print("=" * 70)
```

**使用前请将 `USER_SYMBOLS_HERE` 替换为用户实际输入的参数。**
