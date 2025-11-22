---
description: "删除策略 - 删除策略实例（保留备份）"
---

# Trade Strategy Delete Command

删除策略实例（会自动创建备份）。

**用法**:
```
/trade:strategy-delete INSTANCE_ID [--force]
```

**参数**:
- `INSTANCE_ID`: 要删除的策略实例ID
- `--force`: 强制删除（即使策略已启用）

**安全机制**:
- 删除前会检查策略是否启用
- 如果策略已启用，需要使用 `--force` 参数或先禁用策略
- 删除的策略会自动备份到 `.deleted/` 目录
- 备份文件名包含时间戳，可随时恢复

**示例**:
```
# 删除禁用的策略（安全模式）
/trade:strategy-delete my_old_strategy

# 强制删除启用的策略
/trade:strategy-delete active_strategy --force

# 删除多个策略
/trade:strategy-delete test1
/trade:strategy-delete test2 --force
```

**恢复已删除策略**:
如需恢复，手动复制备份文件：
```bash
cp swarm_intelligence/active_instances/.deleted/策略名_时间戳.json swarm_intelligence/active_instances/策略名.json
```

---

请根据用户提供的参数，运行以下 Python 代码删除策略：

```python
import sys
from pathlib import Path

# 添加项目根目录到路径
PROJECT_ROOT = Path.cwd()
sys.path.insert(0, str(PROJECT_ROOT))

from skills.strategy_manager import delete_strategy, get_strategy_config

# 从用户输入获取参数
user_input = """USER_INPUT_HERE"""  # 替换为用户实际输入

parts = user_input.strip().split()

if len(parts) < 1:
    print("错误：请提供策略实例ID")
    print()
    print("用法: /trade:strategy-delete INSTANCE_ID [--force]")
    print("示例: /trade:strategy-delete my_old_strategy")
    print()
    print("查看可用策略: /trade:strategies")
    exit(1)

instance_id = parts[0]

# 检查是否有 --force 参数
force = '--force' in parts or 'force' in [p.lower() for p in parts]

print("=" * 70)
print(f"删除策略实例: {instance_id}")
print("=" * 70)
print()

# 获取策略配置（用于显示信息）
config = get_strategy_config(instance_id)

if not config:
    print(f"✗ 错误: 策略实例 '{instance_id}' 不存在")
    print()
    print("使用 /trade:strategies 查看可用的策略实例")
    print("=" * 70)
    exit(1)

# 显示策略信息
print(f"模板: {config.get('template', 'N/A')}")
print(f"描述: {config.get('description', 'N/A')}")
print(f"标的池: {len(config.get('parameters', {}).get('symbol_pool', []))} 个标的")
print(f"启用状态: {'启用' if config.get('enabled', False) else '禁用'}")

if config.get('enabled', False):
    print()
    if force:
        print("⚠ 警告: 该策略当前处于启用状态，但将被强制删除")
    else:
        print("⚠ 警告: 该策略当前处于启用状态")
        print("  建议先禁用: /trade:strategy-disable", instance_id)
        print("  或使用 --force 强制删除")

print()
print("确认删除操作...")
print()

# 执行删除
success = delete_strategy(instance_id, force=force)

if success:
    print()
    print("策略实例已删除！")
    print()
    print("提示：")
    print("  - 策略备份保存在 swarm_intelligence/active_instances/.deleted/")
    print("  - 如需恢复，手动复制备份文件回 active_instances/ 目录")
    print("  - 查看剩余策略: /trade:strategies")
else:
    print()
    print("删除失败！请检查错误信息并重试。")

print()
print("=" * 70)
```

**使用前请将 `USER_INPUT_HERE` 替换为用户实际输入的参数。**

**注意**: 删除操作不可撤销（除非从备份恢复），请谨慎操作。
