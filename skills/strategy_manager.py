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


def create_strategy(
    instance_id: str,
    template_name: str,
    symbol_pool: List[str],
    parameters: Optional[Dict] = None,
    description: str = "",
    priority: int = 5,
    enabled: bool = True
) -> bool:
    """
    创建新的策略实例

    Args:
        instance_id: 策略实例ID（唯一标识符，将作为文件名）
        template_name: 策略模板名称（对应 templates/ 目录下的 .md 文件）
        symbol_pool: 标的池列表
        parameters: 策略参数字典（可选，会合并到配置中）
        description: 策略描述（可选）
        priority: 优先级 1-10（默认5）
        enabled: 是否启用（默认True）

    Returns:
        成功返回True，失败返回False
    """
    # 验证实例ID格式（只允许字母、数字、下划线、连字符）
    import re
    if not re.match(r'^[a-zA-Z0-9_-]+$', instance_id):
        print(f"错误: 实例ID '{instance_id}' 格式无效（只允许字母、数字、下划线、连字符）")
        return False

    # 检查实例是否已存在
    json_path = INSTANCES_DIR / f"{instance_id}.json"
    if json_path.exists():
        print(f"错误: 策略实例 '{instance_id}' 已存在")
        return False

    # 验证模板文件是否存在
    templates_dir = Path(__file__).parent.parent / "swarm_intelligence" / "templates"
    template_path = templates_dir / template_name
    if not template_path.exists():
        # 尝试自动添加 .md 扩展名
        if not template_name.endswith('.md'):
            template_path = templates_dir / f"{template_name}.md"

        if not template_path.exists():
            print(f"错误: 策略模板 '{template_name}' 不存在")
            print(f"可用模板: {[f.stem for f in templates_dir.glob('*.md')]}")
            return False

    # 验证优先级范围
    if not 1 <= priority <= 10:
        print(f"错误: 优先级必须在 1-10 之间（当前值: {priority}）")
        return False

    # 验证标的池不为空
    if not symbol_pool or len(symbol_pool) == 0:
        print(f"错误: 标的池不能为空")
        return False

    # 验证标的格式
    for symbol in symbol_pool:
        if not re.match(r'^[A-Z]{2,5}$', symbol):
            print(f"错误: 标的 '{symbol}' 格式无效（必须是2-5个大写字母）")
            return False

    # 构建配置
    config = {
        "id": instance_id,
        "template": template_path.name,
        "description": description,
        "priority": priority,
        "enabled": enabled,
        "parameters": {
            "symbol_pool": symbol_pool
        },
        "created_at": datetime.now().isoformat(),
        "notes": ""
    }

    # 合并额外的参数
    if parameters:
        config["parameters"].update(parameters)

    # 确保目录存在
    INSTANCES_DIR.mkdir(parents=True, exist_ok=True)

    # 写入配置文件（原子操作）
    temp_path = INSTANCES_DIR / f"{instance_id}.json.tmp"

    try:
        # 写入临时文件
        with open(temp_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)

        # 验证临时文件是否有效的JSON
        with open(temp_path, 'r', encoding='utf-8') as f:
            json.load(f)

        # 原子地重命名
        os.replace(temp_path, json_path)

        print(f"✓ 成功创建策略实例: {instance_id}")
        return True

    except Exception as e:
        print(f"错误: 创建策略实例失败 - {e}")
        # 清理临时文件
        if temp_path.exists():
            temp_path.unlink()
        return False


def delete_strategy(instance_id: str, force: bool = False) -> bool:
    """
    删除策略实例

    Args:
        instance_id: 策略实例ID
        force: 是否强制删除（即使策略已启用）

    Returns:
        成功返回True，失败返回False
    """
    json_path = INSTANCES_DIR / f"{instance_id}.json"

    if not json_path.exists():
        print(f"错误: 策略实例 '{instance_id}' 不存在")
        return False

    try:
        # 读取配置检查是否启用
        with open(json_path, 'r', encoding='utf-8') as f:
            config = json.load(f)

        if config.get('enabled', False) and not force:
            print(f"⚠ 策略实例 '{instance_id}' 当前处于启用状态")
            print(f"  如需删除，请先禁用或使用 --force 参数强制删除")
            return False

        # 创建备份（可选）
        backup_dir = INSTANCES_DIR / ".deleted"
        backup_dir.mkdir(exist_ok=True)

        backup_path = backup_dir / f"{instance_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        # 复制到备份目录
        import shutil
        shutil.copy2(json_path, backup_path)

        # 删除原文件
        json_path.unlink()

        print(f"✓ 成功删除策略实例: {instance_id}")
        print(f"  备份已保存至: {backup_path}")
        return True

    except json.JSONDecodeError as e:
        print(f"错误: JSON格式无效 - {e}")
        return False

    except Exception as e:
        print(f"错误: 删除策略实例失败 - {e}")
        return False


def analyze_with_strategy(
    symbol: str,
    instance_id: str,
    market_data: Optional[object] = None
) -> Dict:
    """
    使用特定策略分析特定标的（LLM-based分析）

    工作流程：
    1. 加载策略配置和提示词模板
    2. 获取历史K线数据（15分钟周期，600条）
    3. 组合提示词模板和市场数据
    4. 执行LLM分析
    5. 解析并返回结构化结果

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
    import re
    import json
    from pathlib import Path
    import sys

    # 动态导入数据获取模块
    try:
        sys.path.insert(0, str(Path(__file__).parent))
        from market_data_fetcher import fetch_kline_data, format_kline_for_llm, get_kline_summary
    except ImportError as e:
        return {
            'signal': 'ERROR',
            'confidence': 0.0,
            'reasoning': f"错误: 无法导入数据获取模块 - {e}",
            'metrics': {},
            'suggested_trade': None,
            'warnings': ['market_data_fetcher模块缺失']
        }

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
    if not re.match(r'^[A-Z]{2,5}$', symbol):
        return {
            'signal': 'ERROR',
            'confidence': 0.0,
            'reasoning': f"错误: '{symbol}' 不是有效的标的格式",
            'metrics': {},
            'suggested_trade': None,
            'warnings': []
        }

    # 3. 加载策略模板
    templates_dir = Path(__file__).parent.parent / "swarm_intelligence" / "templates"
    template_path = templates_dir / config.get('template')

    if not template_path.exists():
        return {
            'signal': 'ERROR',
            'confidence': 0.0,
            'reasoning': f"错误: 策略模板 '{config.get('template')}' 不存在",
            'metrics': {},
            'suggested_trade': None,
            'warnings': []
        }

    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            strategy_prompt = f.read()
    except Exception as e:
        return {
            'signal': 'ERROR',
            'confidence': 0.0,
            'reasoning': f"错误: 无法读取策略模板 - {e}",
            'metrics': {},
            'suggested_trade': None,
            'warnings': []
        }

    # 4. 获取K线数据（15分钟周期，600条）
    print(f"正在获取 {symbol} 的历史K线数据...")
    kline_df = fetch_kline_data(symbol, interval="15min", limit=600)

    if kline_df is None or kline_df.empty:
        return {
            'signal': 'ERROR',
            'confidence': 0.0,
            'reasoning': f"错误: 无法获取 '{symbol}' 的历史数据。请确保数据已缓存。",
            'metrics': {},
            'suggested_trade': None,
            'warnings': ['数据缺失', '请运行 /trade:sync 同步数据']
        }

    # 5. 格式化数据为LLM友好格式
    kline_text = format_kline_for_llm(kline_df, max_rows=600)
    data_summary = get_kline_summary(kline_df)

    print(f"✓ 成功获取 {data_summary['total_bars']} 条K线数据")
    print(f"  时间范围: {data_summary['time_range']['start']} ~ {data_summary['time_range']['end']}")
    print(f"  当前价格: ${data_summary['price_range']['current']:.2f}")

    # 6. 组合完整提示词
    full_prompt = f"{strategy_prompt}\n\n{kline_text}\n\n---\n\n请根据以上K线数据进行缠论分析，并按JSON格式输出结果。"

    # 7. 执行LLM分析
    print(f"\n正在使用LLM分析 {symbol}...")

    # 将提示词保存到临时文件，供Task工具使用
    temp_dir = Path(__file__).parent.parent / "temp"
    temp_dir.mkdir(exist_ok=True)
    temp_prompt_path = temp_dir / f"chan_analysis_{symbol}_{instance_id}.txt"

    with open(temp_prompt_path, 'w', encoding='utf-8') as f:
        f.write(full_prompt)

    print(f"✓ 分析提示词已保存至: {temp_prompt_path}")

    # 返回指引信息
    return {
        'signal': 'PENDING',
        'confidence': 0.0,
        'reasoning': f"缠论分析提示词已生成。请手动执行LLM分析或集成LLM API。提示词文件: {temp_prompt_path}",
        'metrics': {
            'template': config.get('template'),
            'symbol': symbol,
            'data_bars': data_summary['total_bars'],
            'time_range': data_summary['time_range'],
            'current_price': data_summary['price_range']['current'],
            'prompt_file': str(temp_prompt_path)
        },
        'suggested_trade': None,
        'warnings': [
            'LLM分析需要手动执行',
            '未来版本将集成Claude API自动分析'
        ]
    }


# 导出所有公共函数
__all__ = [
    'list_active_strategies',
    'get_strategy_config',
    'enable_strategy',
    'disable_strategy',
    'create_strategy',
    'delete_strategy',
    'analyze_with_strategy',
]
