"""
策略实例管理模块

提供蜂群智能策略实例的管理功能：
- 列出所有策略实例
- 启用/禁用策略实例
- 使用特定策略分析特定标的
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

# 策略实例目录
INSTANCES_DIR = Path(__file__).parent.parent / "swarm_intelligence" / "active_instances"


def list_active_strategies() -> List[Dict]:
    """
    列出所有策略实例

    Returns:
        策略实例列表，每个实例包含:
        - instance_id: 实例ID（文件名不含扩展名）
        - template_name: 策略模板名称
        - sector: 板块（tech, energy, all等）
        - enabled: 是否启用
        - symbol_pool: 标的池大小
        - parameters: 关键参数
        - file_path: JSON文件路径
    """
    if not INSTANCES_DIR.exists():
        return []

    strategies = []

    for json_file in INSTANCES_DIR.glob("*.json"):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                config = json.load(f)

            instance_id = json_file.stem

            strategies.append({
                'instance_id': instance_id,
                'template_name': config.get('template_name', 'Unknown'),
                'sector': config.get('sector', 'N/A'),
                'enabled': config.get('enabled', False),
                'symbol_pool': len(config.get('symbol_pool', [])),
                'parameters': config.get('parameters', {}),
                'file_path': str(json_file)
            })

        except json.JSONDecodeError:
            # 跳过无效的JSON文件
            print(f"警告: 跳过无效的JSON文件 '{json_file.name}'")
            continue
        except Exception as e:
            print(f"警告: 处理文件 '{json_file.name}' 时出错: {e}")
            continue

    # 按启用状态排序（启用的在前），然后按实例ID排序
    strategies.sort(key=lambda x: (not x['enabled'], x['instance_id']))

    return strategies


def get_strategy_config(instance_id: str) -> Optional[Dict]:
    """
    获取策略实例配置

    Args:
        instance_id: 策略实例ID

    Returns:
        策略配置字典，如果不存在则返回None
    """
    json_path = INSTANCES_DIR / f"{instance_id}.json"

    if not json_path.exists():
        return None

    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"错误: 无法读取策略配置 '{instance_id}': {e}")
        return None


def enable_strategy(instance_id: str) -> bool:
    """
    启用策略实例（使用原子文件操作）

    Args:
        instance_id: 策略实例ID

    Returns:
        成功返回True，失败返回False
    """
    return _set_strategy_enabled(instance_id, True)


def disable_strategy(instance_id: str) -> bool:
    """
    禁用策略实例（使用原子文件操作）

    Args:
        instance_id: 策略实例ID

    Returns:
        成功返回True，失败返回False
    """
    return _set_strategy_enabled(instance_id, False)


def _set_strategy_enabled(instance_id: str, enabled: bool) -> bool:
    """
    设置策略启用/禁用状态（原子操作）

    使用 write-to-temp-then-rename 模式确保原子性：
    1. 写入临时文件
    2. 验证JSON格式
    3. 原子地重命名临时文件

    Args:
        instance_id: 策略实例ID
        enabled: True启用，False禁用

    Returns:
        成功返回True，失败返回False
    """
    json_path = INSTANCES_DIR / f"{instance_id}.json"
    temp_path = INSTANCES_DIR / f"{instance_id}.json.tmp"

    if not json_path.exists():
        print(f"错误: 策略实例 '{instance_id}' 不存在")
        return False

    try:
        # 1. 读取当前配置
        with open(json_path, 'r', encoding='utf-8') as f:
            config = json.load(f)

        # 检查是否已经是目标状态
        if config.get('enabled') == enabled:
            status = "启用" if enabled else "禁用"
            print(f"ℹ 策略 '{instance_id}' 已经{status}（无需修改）")
            return True

        # 2. 修改配置
        config['enabled'] = enabled

        # 3. 写入临时文件
        with open(temp_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)

        # 4. 验证临时文件是否有效的JSON
        with open(temp_path, 'r', encoding='utf-8') as f:
            json.load(f)  # 如果JSON无效会抛出异常

        # 5. 原子地重命名（POSIX保证原子性）
        os.replace(temp_path, json_path)

        return True

    except json.JSONDecodeError as e:
        print(f"错误: JSON格式无效 - {e}")
        # 清理临时文件
        if temp_path.exists():
            temp_path.unlink()
        return False

    except PermissionError:
        print(f"错误: 文件被锁定，无法修改配置。请稍后重试。")
        return False

    except Exception as e:
        print(f"错误: 修改策略配置失败 - {e}")
        # 清理临时文件
        if temp_path.exists():
            temp_path.unlink()
        return False


def analyze_with_strategy(
    symbol: str,
    instance_id: str,
    market_data: Optional[object] = None
) -> Dict:
    """
    使用特定策略分析特定标的

    注意：这是一个简化的实现框架。完整实现需要：
    1. 加载策略模板代码
    2. 获取/验证市场数据
    3. 执行策略分析逻辑
    4. 返回结构化的分析结果

    Args:
        symbol: 标的符号
        instance_id: 策略实例ID
        market_data: 可选的市场数据（如果未提供，从缓存获取）

    Returns:
        分析结果字典:
        - signal: BUY/SELL/HOLD
        - confidence: 置信度 (0.0-1.0)
        - reasoning: 推理说明
        - metrics: 关键指标
        - suggested_trade: 建议的交易结构（如果可操作）
        - warnings: 警告列表
    """
    # 1. 加载策略配置
    config = get_strategy_config(instance_id)
    if not config:
        return {
            'signal': 'ERROR',
            'confidence': 0.0,
            'reasoning': f"错误: 策略实例 '{instance_id}' 不存在",
            'metrics': {},
            'suggested_trade': None,
            'warnings': []
        }

    # 2. 验证标的格式
    import re
    if not re.match(r'^[A-Z]{2,5}$', symbol):
        return {
            'signal': 'ERROR',
            'confidence': 0.0,
            'reasoning': f"错误: '{symbol}' 不是有效的标的格式",
            'metrics': {},
            'suggested_trade': None,
            'warnings': []
        }

    # 3. 占位符实现 - 实际实现需要导入并执行策略模板
    # TODO: 实现完整的策略执行逻辑
    #   - 从 swarm_intelligence/templates/ 导入策略模板
    #   - 获取市场数据（从缓存或ThetaData）
    #   - 执行策略的 analyze() 函数
    #   - 返回结构化结果

    return {
        'signal': 'HOLD',
        'confidence': 0.0,
        'reasoning': '功能尚未完全实现。此为占位符返回。',
        'metrics': {
            'template': config.get('template_name'),
            'sector': config.get('sector'),
            'symbol': symbol
        },
        'suggested_trade': None,
        'warnings': ['analyze_with_strategy() 功能尚未完全实现']
    }


# 导出所有公共函数
__all__ = [
    'list_active_strategies',
    'get_strategy_config',
    'enable_strategy',
    'disable_strategy',
    'analyze_with_strategy',
]
