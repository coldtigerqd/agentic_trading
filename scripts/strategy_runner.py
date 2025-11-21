#!/usr/bin/env python3
"""
策略运行器命令的独立执行脚本

运行指定的策略实例，支持试运行和详细输出。

用法:
    python scripts/strategy_runner.py <策略名> [选项]

选项:
    --dry-run              仅分析不执行交易
    --verbose              显示详细执行过程
    --format <格式>        输出格式: json|table (默认: table)
    --help                 显示帮助信息
"""

import sys
import os
import argparse
import json
from datetime import datetime
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from skills.swarm_core import consult_swarm


def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description='Agentic AlphaHive 策略运行器',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s tech_aggressive          # 运行激进科技策略
  %(prog)s finance_conservative --dry-run  # 试运行保守金融策略
  %(prog)s tech_aggressive --format json  # JSON格式输出
        """)

    parser.add_argument('strategy_name',
                       nargs='?',
                       help='要运行的策略名称')

    parser.add_argument('--dry-run',
                       action='store_true',
                       help='仅分析不执行交易')
    parser.add_argument('--verbose',
                       action='store_true',
                       help='显示详细执行过程')
    parser.add_argument('--format',
                       choices=['json', 'table'],
                       default='table',
                       help='输出格式 (默认: table)')

    return parser.parse_args()


def get_available_strategies():
    """获取所有可用的策略列表"""
    try:
        from skills.swarm_core import load_instances
        instances = load_instances()
        return [instance['id'] for instance in instances]
    except Exception as e:
        print(f"❌ 获取策略列表失败: {e}")
        return []


def load_strategy_config(strategy_name):
    """加载指定策略的配置"""
    try:
        from skills.swarm_core import load_instances
        instances = load_instances()

        for instance in instances:
            if instance['id'] == strategy_name:
                return instance

        raise ValueError(f"策略 '{strategy_name}' 不存在")
    except Exception as e:
        print(f"❌ 加载策略配置失败: {e}")
        return None


def run_strategy(strategy_name, dry_run=False):
    """运行指定策略"""
    try:
        # 加载策略配置
        config = load_strategy_config(strategy_name)
        if not config:
            return None

        # 获取策略参数
        sector = config.get('sector', 'ALL')
        parameters = config.get('parameters', {})

        # 构建模拟市场数据
        market_data = {
            "timestamp": datetime.now().isoformat(),
            "snapshot": {},
            "context": {
                "spy_trend": "UNKNOWN",
                "market_volatility": "MODERATE"
            }
        }

        # 执行策略
        if dry_run:
            print(f"🧪 试运行模式: {strategy_name}")
            print("   不会执行实际交易")

        signals = consult_swarm(
            sector=sector,
            market_data=market_data
        )

        return {
            "strategy_name": strategy_name,
            "sector": sector,
            "parameters": parameters,
            "signals": signals,
            "execution_time": datetime.now().isoformat(),
            "dry_run": dry_run
        }

    except Exception as e:
        print(f"❌ 策略执行失败: {e}")
        return None


def format_output_table(result):
    """格式化为表格输出"""
    print('🚀 Agentic AlphaHive 策略运行器')
    print('=' * 50)

    if not result:
        print('❌ 策略执行失败，无结果返回')
        return

    print(f'📋 策略名称: {result["strategy_name"]}')
    print(f'📂 目标板块: {result["sector"]}')
    print(f'⚡ 执行时间: {result["execution_time"]}')
    print(f'🧪 试运行模式: {"是" if result["dry_run"] else "否"}')
    print()

    print('🎯 生成信号:')
    print('-' * 30)

    signals = result.get('signals', [])
    if signals:
        for i, signal in enumerate(signals, 1):
            target = signal.get('target', '未知')
            signal_type = signal.get('signal', '未知')
            confidence = signal.get('confidence', 0)
            reasoning = signal.get('reasoning', '无推理')

            print(f'{i}. 📌 {target}')
            print(f'   策略: {signal_type}')
            print(f'   置信度: {confidence:.1%}')
            print(f'   推理: {reasoning}')
            print()
    else:
        print('❌ 未生成任何交易信号')
        print()

    # 策略参数摘要
    params = result.get('parameters', {})
    if params:
        print('⚙️ 策略参数:')
        for key, value in params.items():
            if key in ['symbol_pool', 'symbol_pool_size']:
                if isinstance(value, list):
                    display_symbols = value[:5]
                    suffix = ' ...' if len(value) > 5 else ''
                    symbols_str = '", "'.join(display_symbols)
                    print(f'   {key}: [{symbols_str}{suffix}]')
                else:
                    print(f'   {key}: {value}')
            else:
                print(f'   {key}: {value}')
        print()

    print('📊 执行完成')


def format_output_json(result):
    """格式化为JSON输出"""
    if not result:
        output = {
            "error": "策略执行失败",
            "timestamp": datetime.now().isoformat()
        }
    else:
        output = {
            "timestamp": datetime.now().isoformat(),
            "strategy": result["strategy_name"],
            "sector": result["sector"],
            "execution": {
                "time": result["execution_time"],
                "dry_run": result["dry_run"]
            },
            "signals": result.get("signals", []),
            "parameters": result.get("parameters", {}),
            "signal_count": len(result.get("signals", []))
        }

    print(json.dumps(output, indent=2, ensure_ascii=False))


def list_available_strategies():
    """列出所有可用策略"""
    strategies = get_available_strategies()

    print('📋 可用策略列表:')
    print('=' * 30)

    if strategies:
        for i, strategy in enumerate(strategies, 1):
            print(f'{i:2d}. {strategy}')
        print(f'\n总计: {len(strategies)} 个策略')
    else:
        print('❌ 没有找到可用策略')

    print('\n使用方法:')
    print('python scripts/strategy_runner.py <策略名> [选项]')


def main():
    """主执行函数"""
    try:
        # 解析参数
        args = parse_arguments()

        # 如果没有提供策略名称，显示可用策略列表
        if not args.strategy_name:
            list_available_strategies()
            return 0

        # 显示详细模式信息
        if args.verbose:
            print(f'🔧 详细模式已启用')
            print(f'   策略名称: {args.strategy_name}')
            print(f'   试运行模式: {args.dry_run}')
            print(f'   输出格式: {args.format}')
            print()

        # 检查策略是否存在
        available_strategies = get_available_strategies()
        if args.strategy_name not in available_strategies:
            print(f'❌ 策略 "{args.strategy_name}" 不存在')
            print()
            print('可用策略:')
            for strategy in available_strategies:
                print(f'  • {strategy}')
            return 1

        # 运行策略
        result = run_strategy(args.strategy_name, args.dry_run)

        # 根据格式输出结果
        if args.format == 'json':
            format_output_json(result)
        else:
            format_output_table(result)

        return 0

    except KeyboardInterrupt:
        print('\n⚠️ 用户中断执行')
        return 1
    except Exception as e:
        print(f'❌ 执行失败: {str(e)}')
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())