---
description: "创建策略 - 创建新的策略实例"
---

# Trade Strategy Create Command

创建新的策略实例。

**用法**:
```
/trade:strategy-create INSTANCE_ID TEMPLATE [OPTIONS]
```

**参数**:
- `INSTANCE_ID`: 策略实例ID（唯一标识符，只允许字母、数字、下划线、连字符）
- `TEMPLATE`: 策略模板名称（不含.md扩展名）

**可选参数**:
- `symbols=SYMBOL1,SYMBOL2,...` - 标的池（逗号分隔）
- `priority=1-10` - 优先级（默认5）
- `enabled=true|false` - 是否启用（默认true）
- `description="描述文本"` - 策略描述

**示例**:
```
# 基本用法（最少参数）
/trade:strategy-create my_strategy trend_scout symbols=AAPL,MSFT,GOOGL

# 指定所有参数
/trade:strategy-create energy_play vol_sniper symbols=XLE,XOM,CVX priority=8 enabled=true description="能源板块波动策略"

# 创建但不启用
/trade:strategy-create test_strategy mean_reversion symbols=SPY,QQQ enabled=false
```

**可用模板**:
- `breakout_scout` - 突破侦察策略
- `correlation_arbitrage` - 相关性套利策略
- `mean_reversion` - 均值回归策略
- `trend_scout` - 趋势侦察策略
- `vol_sniper` - 波动率狙击策略

---

请根据用户提供的参数，运行以下 Python 代码创建策略：

```python
import sys
from pathlib import Path

# 添加项目根目录到路径
PROJECT_ROOT = Path.cwd()
sys.path.insert(0, str(PROJECT_ROOT))

from skills.strategy_manager import create_strategy

# 从用户输入获取参数
user_input = """USER_INPUT_HERE"""  # 替换为用户实际输入

parts = user_input.strip().split()

if len(parts) < 2:
    print("错误：请提供实例ID和模板名称")
    print()
    print("用法: /trade:strategy-create INSTANCE_ID TEMPLATE [OPTIONS]")
    print("示例: /trade:strategy-create my_strategy trend_scout symbols=AAPL,MSFT")
    print()
    print("可用模板: breakout_scout, correlation_arbitrage, mean_reversion, trend_scout, vol_sniper")
    exit(1)

instance_id = parts[0]
template_name = parts[1]

# 解析可选参数
symbol_pool = []
priority = 5
enabled = True
description = ""
extra_params = {}

for part in parts[2:]:
    if '=' in part:
        key, value = part.split('=', 1)
        key = key.lower()

        if key == 'symbols':
            # 解析标的池（逗号分隔）
            symbol_pool = [s.strip().upper() for s in value.split(',')]
        elif key == 'priority':
            try:
                priority = int(value)
            except ValueError:
                print(f"警告: 优先级 '{value}' 无效，使用默认值 5")
        elif key == 'enabled':
            enabled = value.lower() in ['true', '1', 'yes', 'on']
        elif key == 'description' or key == '描述':
            # 移除引号（如果有）
            description = value.strip('"\'')
        else:
            # 其他参数添加到 extra_params
            try:
                # 尝试转换为数字
                if '.' in value:
                    extra_params[key] = float(value)
                else:
                    extra_params[key] = int(value)
            except ValueError:
                extra_params[key] = value

# 验证必需参数
if not symbol_pool:
    print("错误：必须提供标的池（symbols=SYMBOL1,SYMBOL2,...）")
    print()
    print("示例: /trade:strategy-create my_strategy trend_scout symbols=AAPL,MSFT,GOOGL")
    exit(1)

print("=" * 70)
print(f"创建策略实例: {instance_id}")
print("=" * 70)
print()
print(f"模板: {template_name}")
print(f"标的池: {', '.join(symbol_pool)} ({len(symbol_pool)} 个)")
print(f"优先级: {priority}/10")
print(f"启用: {'是' if enabled else '否'}")
if description:
    print(f"描述: {description}")
if extra_params:
    print(f"额外参数: {extra_params}")
print()

# 创建策略
success = create_strategy(
    instance_id=instance_id,
    template_name=template_name,
    symbol_pool=symbol_pool,
    parameters=extra_params if extra_params else None,
    description=description,
    priority=priority,
    enabled=enabled
)

if success:
    print()
    print("策略实例已创建！")
    print()
    print("下一步：")
    print(f"  查看策略: /trade:strategies")
    print(f"  测试分析: /trade:analyze-symbol {symbol_pool[0]} {instance_id}")
    if enabled:
        print(f"  该策略已启用，将在下次分析时生效")
    else:
        print(f"  启用策略: /trade:strategy-enable {instance_id}")
else:
    print()
    print("创建失败！请检查错误信息并重试。")

print()
print("=" * 70)
```

**使用前请将 `USER_INPUT_HERE` 替换为用户实际输入的参数。**
