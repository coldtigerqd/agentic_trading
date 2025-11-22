# Trade Strategy Disable Command

禁用一个策略实例（保留所有配置）。

**用法**:
```
/trade:strategy-disable INSTANCE_ID
```

**示例**:
```
/trade:strategy-disable momentum_tech_short
/trade:strategy-disable iron_condor_tech
```

请根据用户提供的实例ID，运行以下 Python 代码：

```python
import sys
from pathlib import Path

# 添加项目根目录到路径
PROJECT_ROOT = Path.cwd()
sys.path.insert(0, str(PROJECT_ROOT))

from skills.strategy_manager import disable_strategy, get_strategy_config

# 从用户输入获取实例ID
instance_id = """USER_INSTANCE_ID_HERE"""  # 替换为用户实际输入

instance_id = instance_id.strip()

if not instance_id or instance_id == "USER_INSTANCE_ID_HERE":
    print("错误：请提供策略实例ID")
    print()
    print("用法: /trade:strategy-disable INSTANCE_ID")
    print("查看可用策略: /trade:strategies")
    exit(1)

print("=" * 70)
print(f"禁用策略实例: {instance_id}")
print("=" * 70)
print()

# 获取策略配置
config = get_strategy_config(instance_id)

if not config:
    print(f"✗ 错误: 策略实例 '{instance_id}' 不存在")
    print()
    print("使用 /trade:strategies 查看可用的策略实例")
    print("=" * 70)
    exit(1)

# 禁用策略
success = disable_strategy(instance_id)

if success:
    print(f"✓ 已禁用策略实例: {instance_id}")
    print(f"  模板: {config.get('template_name', 'N/A')}")
    print(f"  板块: {config.get('sector', 'N/A')}")
    print(f"  标的池: {len(config.get('symbol_pool', []))} 个标的")
    print()
    print("该策略不会参与未来的蜂群咨询。")
    print("所有配置已保留。随时可以重新启用：")
    print(f"  /trade:strategy-enable {instance_id}")
else:
    print(f"✗ 禁用策略失败")

print()
print("=" * 70)
```

**使用前请将 `USER_INSTANCE_ID_HERE` 替换为用户实际输入的实例ID。**
