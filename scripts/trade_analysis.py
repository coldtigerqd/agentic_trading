#!/usr/bin/env python3
"""
交易分析命令的独立执行脚本

替代不稳定的 bash -c "大段代码" 方式，使用独立脚本确保稳定性和可维护性。

用法:
    python scripts/trade_analysis.py [选项]

选项:
    --sectors <板块>       要分析的板块，用逗号分隔 (默认: ALL)
    --min-confidence <数值>  最低信号置信度 (默认: 0.75)
    --max-orders <数量>     每次运行最大执行订单数 (默认: 2)
    --skip-sync            跳过数据同步
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

from skills.workflow_skills import run_full_trading_analysis
from skills import run_market_health_check


def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description='Agentic AlphaHive 交易分析系统',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s                              # 默认分析
  %(prog)s --sectors TECH,FINANCE     # 分析特定板块
  %(prog)s --min-confidence 0.80       # 提高置信度要求
  %(prog)s --dry-run                   # 仅分析不执行
  %(prog)s --format json               # JSON格式输出
        """)

    # 基本参数
    parser.add_argument('--sectors',
                       default='ALL',
                       help='要分析的板块，用逗号分隔 (默认: ALL)')
    parser.add_argument('--min-confidence',
                       type=float,
                       default=0.75,
                       help='最低信号置信度 (0.0-1.0, 默认: 0.75)')
    parser.add_argument('--max-orders',
                       type=int,
                       default=2,
                       help='每次运行最大执行订单数 (默认: 2)')

    # 执行控制
    parser.add_argument('--skip-sync',
                       action='store_true',
                       help='跳过数据同步')
    parser.add_argument('--dry-run',
                       action='store_true',
                       help='仅分析不执行交易')
    parser.add_argument('--verbose',
                       action='store_true',
                       help='显示详细执行过程')

    # 输出控制
    parser.add_argument('--format',
                       choices=['json', 'table'],
                       default='table',
                       help='输出格式 (默认: table)')

    return parser.parse_args()


def format_output_table(result):
    """格式化为表格输出"""
    print('🚀 Agentic AlphaHive 交易分析系统')
    print('=' * 50)

    # 市场状态
    market_status = '🟢 开盘' if result.market_open else '🔴 关盘'
    print(f'📊 市场状态: {market_status} ({result.market_session})')

    # 数据质量
    if result.stale_symbols == 0:
        data_status = '✅ 数据新鲜'
    elif result.stale_symbols < result.total_symbols * 0.5:
        data_status = '⚠️ 部分过期'
    else:
        data_status = '❌ 大部分过期'

    print(f'📈 数据质量: {data_status} ({result.fresh_symbols}/{result.total_symbols} 新鲜)')
    print(f'⏱️ 执行时间: {result.execution_time:.2f}秒')

    print()
    print('🎯 交易信号分析:')
    print('-' * 30)

    if result.high_confidence_signals:
        for i, signal in enumerate(result.high_confidence_signals, 1):
            target = signal.get('target', '未知标的')
            signal_type = signal.get('signal', '未知策略')
            confidence = signal.get('confidence', 0)
            reasoning = signal.get('reasoning', '无推理说明')
            max_risk = signal.get('max_risk', 0)

            print(f'{i}. 📌 {target}')
            print(f'   策略: {signal_type}')
            print(f'   置信度: {confidence:.1%}')
            print(f'   推理: {reasoning}')
            if max_risk > 0:
                print(f'   风险: ${max_risk:,.0f}')
            print()
    else:
        print('❌ 当前无高置信度交易信号 (≥75%)')
        if result.signals:
            print(f'📊 总共分析了 {len(result.signals)} 个信号')
        print()

    # 系统消息
    if result.warnings:
        print('⚠️ 系统提醒:')
        for warning in result.warnings:
            print(f'   • {warning}')
        print()

    if result.errors:
        print('🚨 错误信息:')
        for error in result.errors:
            print(f'   • {error}')
        print()

    # 投资建议
    print('💡 投资建议:')
    if result.stale_symbols > result.total_symbols * 0.7:
        print('   • 数据质量问题严重，建议等待数据刷新后再交易')
    elif not result.high_confidence_signals:
        print('   • 当前无符合条件的高置信度信号')
        print('   • 建议继续监控市场，等待更好机会')
    else:
        print('   • 发现高置信度信号，建议谨慎执行')

    print()
    print('📋 分析完成')


def format_output_json(result):
    """格式化为JSON输出"""
    output = {
        "timestamp": datetime.now().isoformat(),
        "market_status": {
            "session": result.market_session,
            "open": result.market_open
        },
        "data_quality": {
            "total_symbols": result.total_symbols,
            "fresh_symbols": result.fresh_symbols,
            "stale_symbols": result.stale_symbols
        },
        "execution": {
            "time_seconds": result.execution_time,
            "signals_generated": len(result.signals),
            "high_confidence_signals": len(result.high_confidence_signals)
        },
        "signals": result.high_confidence_signals,
        "warnings": result.warnings,
        "errors": result.errors
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
            print(f'   板块: {args.sectors}')
            print(f'   置信度阈值: {args.min_confidence}')
            print(f'   最大订单数: {args.max_orders}')
            print(f'   跳过同步: {args.skip_sync}')
            print(f'   试运行模式: {args.dry_run}')
            print(f'   输出格式: {args.format}')
            print()

        # 执行交易分析
        sectors = [s.strip() for s in args.sectors.split(',') if s.strip()] if args.sectors != 'ALL' else ['ALL']

        result = run_full_trading_analysis(
            sectors=sectors,
            min_confidence=args.min_confidence,
            max_orders_per_run=args.max_orders,
            skip_sync_if_market_closed=args.skip_sync
        )

        # 根据格式输出结果
        if args.format == 'json':
            format_output_json(result)
        else:
            format_output_table(result)

        return 0

    except KeyboardInterrupt:
        print('\n⚠️ 用户中断分析')
        return 1
    except Exception as e:
        print(f'❌ 执行失败: {str(e)}')
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())