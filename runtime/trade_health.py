#!/usr/bin/env python3
"""
Agentic AlphaHive - 市场健康检查工具

快速检查市场状态和数据质量。

使用方法：
    python runtime/trade_health.py
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from skills import run_market_health_check
from datetime import datetime


def main():
    """主函数"""
    print("=" * 70)
    print("市场健康检查")
    print("=" * 70)
    print(f"检查时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    result = run_market_health_check()

    # 市场状态
    print(f"市场状态: {result['session']}")
    print(f"市场开盘: {'✅ YES' if result['market_open'] else '❌ NO'}")
    print(f"数据质量: {result['data_quality']}")

    # 价格信息
    print()
    if result.get('spy_price'):
        age_h = (result.get('spy_age_minutes') or 0) // 60
        age_m = (result.get('spy_age_minutes') or 0) % 60
        print(f"SPY: ${result['spy_price']:.2f} (数据年龄: {age_h}h {age_m}m)")
    else:
        print("SPY: 无数据")

    if result.get('qqq_price'):
        age_h = (result.get('qqq_age_minutes') or 0) // 60
        age_m = (result.get('qqq_age_minutes') or 0) % 60
        print(f"QQQ: ${result['qqq_price']:.2f} (数据年龄: {age_h}h {age_m}m)")
    else:
        print("QQQ: 无数据")

    # 警告和建议
    if result.get('warnings'):
        print("\n⚠️  警告:")
        for w in result['warnings']:
            print(f"  - {w}")

    # 数据质量建议
    print("\n建议:")
    if result['data_quality'] == 'CRITICAL':
        print("  🔴 数据质量 CRITICAL - 建议同步数据")
        print("     python runtime/data_sync_daemon.py --once")
    elif result['data_quality'] == 'STALE':
        print("  🟡 数据质量 STALE - 可以交易但建议提高置信度要求")
    else:
        print("  🟢 数据质量 GOOD - 可以正常交易")

    if not result['market_open']:
        print(f"  ⏰ 市场关闭 - 下次开盘请使用实时分析")

    print("\n" + "=" * 70)

    # 返回状态码
    if result['data_quality'] == 'CRITICAL':
        sys.exit(2)  # 数据质量严重问题
    elif not result['market_open']:
        sys.exit(1)  # 市场关闭
    else:
        sys.exit(0)  # 正常


if __name__ == '__main__':
    main()
