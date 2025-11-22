---
description: "分析标的 - 用指定策略分析特定股票"
---

# Trade Analyze Symbol Command

使用特定策略分析特定标的（用于测试和学习）。

**用法**:
```
/trade:analyze-symbol SYMBOL INSTANCE_ID
```

**示例**:
```
/trade:analyze-symbol AAPL momentum_tech_short
/trade:analyze-symbol TSLA mean_reversion_energy
```

请根据用户提供的标的和策略实例ID，运行以下 Python 代码：

```python
import sys
from pathlib import Path
from datetime import datetime, timedelta

# 添加项目根目录到路径
PROJECT_ROOT = Path.cwd()
sys.path.insert(0, str(PROJECT_ROOT))

from skills.strategy_manager import analyze_with_strategy, get_strategy_config

# 从用户输入获取参数
user_input = """USER_INPUT_HERE"""  # 替换为用户实际输入，格式: "SYMBOL INSTANCE_ID"

parts = user_input.strip().split()

if len(parts) < 2:
    print("错误：请提供标的符号和策略实例ID")
    print()
    print("用法: /trade:analyze-symbol SYMBOL INSTANCE_ID")
    print("示例: /trade:analyze-symbol AAPL momentum_tech_short")
    print()
    print("查看可用策略: /trade:strategies")
    exit(1)

symbol = parts[0].upper()
instance_id = parts[1]

print("=" * 90)
print(f"标的-策略分析")
print("=" * 90)
print()
print(f"标的: {symbol}")
print(f"策略: {instance_id}")

# 获取策略配置
config = get_strategy_config(instance_id)

if not config:
    print()
    print(f"✗ 错误: 策略实例 '{instance_id}' 不存在")
    print()
    print("使用 /trade:strategies 查看可用的策略实例")
    print("=" * 90)
    exit(1)

print(f"模板: {config.get('template_name', 'N/A')}")
print()

# 检查数据状态
import sqlite3
DB_PATH = Path("data_lake/trades.db")

conn = sqlite3.connect(str(DB_PATH))
cursor = conn.cursor()

cursor.execute("""
    SELECT newest_bar, bar_count
    FROM data_freshness
    WHERE symbol = ?
""", (symbol,))

freshness = cursor.fetchone()

if freshness and freshness[0]:
    try:
        ts = datetime.fromisoformat(freshness[0].replace('Z', '+00:00'))
        now = datetime.now(ts.tzinfo) if ts.tzinfo else datetime.now()
        age = now - ts

        if age <= timedelta(hours=24):
            data_status = "✓ GOOD"
        elif age <= timedelta(days=7):
            data_status = "⚠ STALE"
            print(f"⚠ 警告: {symbol} 数据已过期 {age.days} 天，结果可能不准确")
            print()
        else:
            data_status = "✗ CRITICAL"
            print(f"✗ 错误: {symbol} 数据严重过期（{age.days} 天）")
            print(f"  建议运行回填: python scripts/backfill_historical_data.py --symbols {symbol} --days 7")
            print()

        print(f"数据状态: {data_status} (最新: {freshness[0]}, {freshness[1]:,} 条数据)")
    except:
        data_status = "✗ CRITICAL"
        print(f"数据状态: {data_status} (无效的时间戳)")
else:
    data_status = "✗ CRITICAL"
    print(f"数据状态: {data_status} (无数据)")
    print()
    print(f"  {symbol} 不在缓存中")
    print(f"  建议先添加到观察列表: /trade:watchlist-add {symbol}")
    print(f"  然后运行回填: python scripts/backfill_historical_data.py --symbols {symbol} --days 1095")
    print()

conn.close()

print()
print("--- 分析结果 ---")
print()

# 执行分析（注意：当前为占位符实现）
result = analyze_with_strategy(symbol, instance_id)

# 显示信号和置信度
signal = result.get('signal', 'UNKNOWN')
confidence = result.get('confidence', 0.0)

confidence_label = "HIGH" if confidence >= 0.80 else "MEDIUM" if confidence >= 0.70 else "LOW"

print(f"信号: {signal}")
print(f"置信度: {confidence:.2f} ({confidence_label})")

if confidence < 0.70:
    print("  ⚠ 低于可操作阈值（0.70），不建议执行")

print()

# 显示推理
reasoning = result.get('reasoning', 'N/A')
print(f"推理:")
for line in reasoning.split('\n'):
    if line.strip():
        print(f"  {line}")

print()

# 显示关键指标
metrics = result.get('metrics', {})
if metrics:
    print(f"关键指标:")
    for key, value in metrics.items():
        print(f"  {key}: {value}")
    print()

# 显示建议交易
suggested_trade = result.get('suggested_trade')
if suggested_trade:
    print(f"建议交易:")
    for key, value in suggested_trade.items():
        print(f"  {key}: {value}")
    print()

# 显示警告
warnings = result.get('warnings', [])
if warnings:
    print(f"警告:")
    for warning in warnings:
        print(f"  ⚠ {warning}")
    print()

# 下一步建议
if signal in ['BUY', 'SELL'] and confidence >= 0.70:
    print("--- 下一步 ---")
    print()
    print("如需执行此信号：")
    print("  1. 验证市场状况: /trade:health")
    print("  2. 运行完整分析: /trade:analyze")
    print("  3. 使用 place_order_with_guard() 执行订单")
elif signal == 'HOLD' or confidence < 0.70:
    print("--- 建议 ---")
    print()
    print("当前信号不可操作。可以尝试：")
    print(f"  - 使用其他策略分析 {symbol}")
    print("  - 等待更好的市场条件")
    print("  - 查看适合该板块的策略: /trade:strategies")

print()
print("=" * 90)
```

**使用前请将 `USER_INPUT_HERE` 替换为用户实际输入（格式: "SYMBOL INSTANCE_ID"）。**

**注意**: `analyze_with_strategy()` 当前为占位符实现。完整实现需要集成策略模板执行逻辑。
