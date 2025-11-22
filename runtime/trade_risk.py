#!/usr/bin/env python3
"""
Agentic AlphaHive - 持仓风险分析工具

分析当前持仓的风险状况。

使用方法：
    python runtime/trade_risk.py [--threshold=70]
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import argparse
from datetime import datetime
from skills import run_position_risk_analysis


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='持仓风险分析工具'
    )

    parser.add_argument(
        '--threshold',
        type=int,
        default=70,
        help='风险警告阈值 0-100 (默认: 70)'
    )

    args = parser.parse_args()

    print("=" * 70)
    print("持仓风险分析")
    print("=" * 70)
    print(f"分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"风险阈值: {args.threshold}/100\n")

    # 获取持仓（实际应从 MCP 获取）
    # 这里需要通过 Claude Code 的 MCP 接口调用
    print("⚠️  此脚本需要通过 Claude Code 环境运行以访问 IBKR 持仓数据")
    print("直接运行将使用模拟数据\n")

    # 模拟持仓
    positions = []

    if not positions:
        print("✅ 当前无持仓")
        print("\n建议:")
        print("  - 可以开始新的交易分析")
        print("  - 使用 python runtime/trade_analyze.py 查找交易机会")
        sys.exit(0)

    # 分析风险
    result = run_position_risk_analysis(positions)

    print(f"持仓数量: {result.total_positions}")
    print(f"总风险敞口: ${result.total_exposure:,.2f}")
    print(f"风险评分: {result.risk_score}/100")

    # 风险等级
    if result.risk_score > 70:
        risk_level = "🔴 高风险"
        risk_color = "高"
    elif result.risk_score > 40:
        risk_level = "🟡 中等风险"
        risk_color = "中"
    else:
        risk_level = "🟢 低风险"
        risk_color = "低"

    print(f"风险等级: {risk_level}")

    # 高风险持仓
    if result.positions_at_risk:
        print("\n⚠️  需要关注的持仓:")
        print("-" * 70)
        for pos in result.positions_at_risk:
            print(f"  {pos['symbol']}")
            print(f"    原因: {pos['reason']}")
            print(f"    建议: {pos['action']}")
            print(f"    紧急度: {pos['urgency']}")
            print()

    # 建议
    if result.recommendations:
        print("建议:")
        for rec in result.recommendations:
            print(f"  • {rec}")

    # 风险警告
    print()
    if result.risk_score > args.threshold:
        print(f"⚠️  风险评分 ({result.risk_score}) 超过阈值 ({args.threshold})")
        print("   建议:")
        print("   1. 优先处理高风险持仓")
        print("   2. 暂停新交易，专注风险管理")
        print("   3. 考虑对冲或减仓")
        sys.exit(1)
    else:
        print(f"✅ 风险评分 ({result.risk_score}) 在可控范围内")
        print("   可以继续正常交易")
        sys.exit(0)


if __name__ == '__main__':
    main()
