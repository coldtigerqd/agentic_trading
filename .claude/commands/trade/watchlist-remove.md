# Trade Watchlist Remove Command

从观察列表中移除一个或多个标的（软删除，保留历史数据）。

**用法**:
```
/trade:watchlist-remove SYMBOL [SYMBOL2 ...] [--force]
```

**示例**:
- 移除单个标的: `TSLA`
- 移除多个标的: `GOOGL META`
- 强制移除（即使有持仓）: `AAPL --force`

**安全检查**: 如果标的有活跃持仓，需要添加 `--force` 标志才能移除。

请根据用户提供的参数，运行以下 Python 代码移除标的：

```python
import sqlite3
from pathlib import Path
from datetime import datetime
import sys
import os

# 添加项目根目录到路径以导入 MCP 工具
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

DB_PATH = Path("data_lake/trades.db")

# 从用户输入解析参数
user_input = """USER_SYMBOLS_HERE"""  # 替换为用户实际输入

symbols = []
force = False

parts = user_input.strip().split()
for part in parts:
    if part.lower() in ['--force', 'force', '强制']:
        force = True
    else:
        symbols.append(part.upper())

if not symbols:
    print("错误：请提供至少一个标的符号")
    print()
    print("用法: /trade:watchlist-remove SYMBOL [--force]")
    exit(1)

# 检查 IBKR 持仓（如果可用）
def check_ibkr_positions(symbol):
    """检查标的是否有活跃持仓"""
    try:
        # 尝试导入 IBKR MCP 工具
        # 注意：在实际环境中需要确保 MCP 服务器已启动
        # 这里提供一个简化的检查逻辑
        # 实际实现中应该调用: mcp__ibkr__get_positions(symbol=symbol)

        # 由于我们在 slash command 中，直接检查不可行
        # 因此我们简化为检查最近是否有该标的的交易记录
        conn_temp = sqlite3.connect(str(DB_PATH))
        cursor_temp = conn_temp.cursor()

        cursor_temp.execute("""
            SELECT COUNT(*) FROM trades
            WHERE symbol = ?
            AND status IN ('FILLED', 'SUBMITTED')
            AND timestamp > datetime('now', '-30 days')
        """, (symbol,))

        recent_trades = cursor_temp.fetchone()[0]
        conn_temp.close()

        return recent_trades > 0
    except:
        return False

# 连接数据库
conn = sqlite3.connect(str(DB_PATH))
cursor = conn.cursor()

print("=" * 70)
print("从观察列表移除标的")
print("=" * 70)
print()

success_count = 0

for symbol in symbols:
    # 检查是否在观察列表中
    cursor.execute("SELECT active, priority FROM watchlist WHERE symbol = ?", (symbol,))
    existing = cursor.fetchone()

    if not existing:
        print(f"✗ {symbol}: 不在观察列表中")
        continue

    if existing[0] == 0:  # 已经被移除
        print(f"ℹ {symbol}: 已经被移除")
        continue

    # 检查是否有活跃持仓
    has_positions = check_ibkr_positions(symbol)

    if has_positions and not force:
        print(f"⚠ {symbol}: 检测到近期交易活动")
        print(f"   该标的可能有活跃持仓。使用 --force 强制移除。")
        print(f"   示例: /trade:watchlist-remove {symbol} --force")
        continue

    try:
        # 软删除：设置 active = 0，保留历史数据
        cursor.execute("""
            UPDATE watchlist
            SET active = 0, last_updated = ?
            WHERE symbol = ?
        """, (datetime.now().isoformat(), symbol))

        # 获取数据统计
        cursor.execute("""
            SELECT bar_count FROM data_freshness WHERE symbol = ?
        """, (symbol,))
        df_result = cursor.fetchone()
        bar_count = df_result[0] if df_result else 0

        conn.commit()

        print(f"✓ {symbol}: 已从观察列表移除（软删除）")
        if bar_count > 0:
            print(f"   历史数据已保留（{bar_count:,} 条数据）")
        if has_positions:
            print(f"   ⚠ 注意：该标的可能有活跃持仓，请自行管理")

        success_count += 1

    except Exception as e:
        conn.rollback()
        print(f"✗ {symbol}: 移除失败 - {str(e)}")

conn.close()

print()
print(f"成功移除: {success_count}/{len(symbols)} 个标的")

if success_count > 0:
    print()
    print("提示：")
    print("  - 历史数据已保留在数据库中")
    print("  - 如需重新添加标的，使用: /trade:watchlist-add SYMBOL")
    print("  - 查看当前观察列表: /trade:watchlist")

print("=" * 70)
```

**使用前请将 `USER_SYMBOLS_HERE` 替换为用户实际输入的参数。**
