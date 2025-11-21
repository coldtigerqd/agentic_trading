#!/usr/bin/env python3
"""
市场健康检查命令的独立执行脚本

快速检查市场状态和数据质量，为交易决策提供基础信息。

用法:
    python scripts/market_health.py [选项]

选项:
    --format <格式>        输出格式: json|table (默认: table)
    --verbose              显示详细信息
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

from skills import run_market_health_check


def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description='Agentic AlphaHive 市场健康检查',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s                              # 基础检查
  %(prog)s --format json               # JSON格式输出
  %(prog)s --verbose                  # 显示详细信息
        """)

    parser.add_argument('--format',
                       choices=['json', 'table'],
                       default='table',
                       help='输出格式 (默认: table)')
    parser.add_argument('--verbose',
                       action='store_true',
                       help='显示详细信息')

    return parser.parse_args()


def format_output_table(health):
    """格式化为表格输出"""
    print('🏥 Agentic AlphaHive 市场健康检查')
    print('=' * 50)

    # 基础状态
    print('📊 市场状态:')
    market_status = '🟢 开盘' if health.get('market_open') else '🔴 关盘'
    session = health.get("session", "未知")
    timestamp = health.get("timestamp", "未知")
    print(f'   交易时段: {session}')
    print(f'   市场状态: {market_status}')
    print(f'   检查时间: {timestamp}')
    print()

    # 数据质量
    print('📈 数据质量:')
    data_quality = health.get('data_quality', 'UNKNOWN')

    if data_quality == 'GOOD':
        quality_status = '✅ 良好'
        quality_desc = '所有数据都处于最新状态'
    elif data_quality == 'STALE':
        quality_status = '⚠️ 部分过期'
        quality_desc = '部分数据需要更新'
    elif data_quality == 'CRITICAL':
        quality_status = '❌ 严重问题'
        quality_desc = '大部分数据已过期，建议等待刷新'
    else:
        quality_status = '❓ 未知'
        quality_desc = '无法确定数据质量状态'

    print(f'   整体状态: {quality_status}')
    print(f'   详细描述: {quality_desc}')
    print()

    # 指数价格
    print('💰 关键指数:')
    if health.get('spy_price'):
        spy_age = health.get('spy_age_minutes', 0)
        spy_status = '✅ 实时' if spy_age < 1 else f'⚠️ {spy_age:.1f}分钟延迟'
        spy_price = health.get("spy_price", 0)
        print(f'   SPY: ${spy_price:.2f} ({spy_status})')
    else:
        print('   SPY: 📛 数据不可用')

    if health.get('qqq_price'):
        qqq_age = health.get('qqq_age_minutes', 0)
        qqq_status = '✅ 实时' if qqq_age < 1 else f'⚠️ {qqq_age:.1f}分钟延迟'
        qqq_price = health.get("qqq_price", 0)
        print(f'   QQQ: ${qqq_price:.2f} ({qqq_status})')
    else:
        print('   QQQ: 📛 数据不可用')
    print()

    # 系统警告
    warnings = health.get('warnings', [])
    if warnings:
        print('⚠️ 系统提醒:')
        for warning in warnings:
            print(f'   • {warning}')
        print()

    # 状态总结
    print('📋 检查总结:')
    if health.get('market_open') and data_quality in ['GOOD', 'STALE']:
        print('   ✅ 市场状态适合交易')
    elif health.get('market_open') and data_quality == 'CRITICAL':
        print('   ⚠️ 市场开放但数据质量差，建议谨慎交易')
    else:
        print('   🛌 市场关闭，不适合交易')

    last_update = health.get("timestamp", "未知")
    print(f'   最后更新: {last_update}')


def format_output_json(health):
    """格式化为JSON输出"""
    output = {
        "timestamp": datetime.now().isoformat(),
        "health_status": {
            "market_open": health.get('market_open', False),
            "session": health.get('session', 'UNKNOWN'),
            "data_quality": health.get('data_quality', 'UNKNOWN')
        },
        "market_indices": {
            "spy": {
                "price": health.get('spy_price'),
                "age_minutes": health.get('spy_age_minutes')
            },
            "qqq": {
                "price": health.get('qqq_price'),
                "age_minutes": health.get('qqq_age_minutes')
            }
        },
        "system_info": {
            "warnings": health.get('warnings', []),
            "last_update": health.get('timestamp')
        }
    }

    print(json.dumps(output, indent=2, ensure_ascii=False))


def main():
    """主执行函数"""
    try:
        # 解析参数
        args = parse_arguments()

        # 显示详细模式信息
        if args.verbose:
            print(f'🔧 详细模式已启用')
            print(f'   输出格式: {args.format}')
            print()

        # 执行市场健康检查
        health = run_market_health_check()

        # 根据格式输出结果
        if args.format == 'json':
            format_output_json(health)
        else:
            format_output_table(health)

        return 0

    except KeyboardInterrupt:
        print('\n⚠️ 用户中断检查')
        return 1
    except Exception as e:
        print(f'❌ 检查失败: {str(e)}')
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())