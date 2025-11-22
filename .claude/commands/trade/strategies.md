---
description: "策略列表 - 显示所有蜂群智能策略实例"
---

# Trade Strategies Command

列出所有蜂群智能策略实例及其配置。

请运行以下 Python 代码：

```python
import sys
from pathlib import Path

# 添加项目根目录到路径
PROJECT_ROOT = Path.cwd()
sys.path.insert(0, str(PROJECT_ROOT))

from skills.strategy_manager import list_active_strategies

# 获取所有策略实例
strategies = list_active_strategies()

print("=" * 100)
print("蜂群智能策略实例")
print("=" * 100)
print()

if not strategies:
    print("未找到策略实例")
    print()
    print("提示：策略实例存储在 swarm_intelligence/active_instances/")
    print("      可以从 templates/ 目录复制模板创建新实例")
else:
    # 表头
    print(f"{'实例ID':<30} {'模板':<20} {'板块':<12} {'状态':<8} {'标的数':>8}  {'关键参数':<30}")
    print("-" * 100)

    enabled_count = 0
    disabled_count = 0

    for strategy in strategies:
        # 状态图标
        status_icon = "✓" if strategy['enabled'] else "○"
        status_text = "启用" if strategy['enabled'] else "禁用"

        # 统计
        if strategy['enabled']:
            enabled_count += 1
        else:
            disabled_count += 1

        # 提取关键参数（最多显示2个）
        params = strategy.get('parameters', {})
        param_strs = []
        for key, value in list(params.items())[:2]:
            if isinstance(value, float):
                param_strs.append(f"{key}={value:.2f}")
            else:
                param_strs.append(f"{key}={value}")

        param_display = ", ".join(param_strs) if param_strs else "N/A"

        # 打印行
        print(f"{strategy['instance_id']:<30} "
              f"{strategy['template_name']:<20} "
              f"{strategy['sector']:<12} "
              f"{status_icon} {status_text:<6} "
              f"{strategy['symbol_pool']:>8}  "
              f"{param_display:<30}")

    print("-" * 100)
    print(f"总计: {len(strategies)} 个实例 | 启用: {enabled_count} | 禁用: {disabled_count}")

print()
print("命令：")
print("  启用策略: /trade:strategy-enable INSTANCE_ID")
print("  禁用策略: /trade:strategy-disable INSTANCE_ID")
print("  分析标的: /trade:analyze-symbol SYMBOL INSTANCE_ID")
print()
print("=" * 100)
```

运行完成后，向用户汇报策略实例列表。
