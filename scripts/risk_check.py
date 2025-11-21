#!/usr/bin/env python3
"""
风险检查命令的独立执行脚本

分析当前持仓的风险状况，提供风险评估和建议。

用法:
    python scripts/risk_check.py [选项]

选项:
    --format <格式>        输出格式: json|table (default: table)
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

from skills.workflow_skills import run_position_risk_analysis


def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description='Agentic AlphaHive 风险检查系统',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s                              # 基础风险检查
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


def get_current_positions():
    """获取当前持仓信息"""
    try:
        # 尝试从MCP获取持仓
        from skills import mcp__ibkr_get_positions
        positions = mcp__ibkr_get_positions()
        return positions
    except Exception as e:
        print(f'⚠️ 无法获取持仓信息: {e}')
        return []


def format_output_table(risk_analysis):
    """格式化为表格输出"""
    print('🛡️ Agentic AlphaHive 风险检查系统')
    print('=' * 50)

    # 基础风险概览
    total_positions = risk_analysis.get('total_positions', 0)
    total_exposure = risk_analysis.get('total_exposure', 0)
    risk_score = risk_analysis.get('risk_score', 0)

    print('📊 风险概览:')
    print(f'   总持仓数: {total_positions}')
    print(f'   总敞口: ${total_exposure:,.2f}')

    # 风险评分显示
    if risk_score >= 70:
        risk_level = '🔴 高风险'
        recommendation = '需要立即采取行动'
    elif risk_score >= 40:
        risk_level = '🟡 中等风险'
        recommendation = '建议密切关注'
    else:
        risk_level = '🟢 低风险'
        recommendation = '风险可控'

    print(f'   风险评分: {risk_score}/100 ({risk_level})')
    print(f'   建议行动: {recommendation}')
    print()

    # 风险持仓详情
    positions_at_risk = risk_analysis.get('positions_at_risk', [])
    if positions_at_risk:
        print('⚠️ 风险持仓:')
        for i, position in enumerate(positions_at_risk, 1):
            symbol = position['symbol']
            reason = position['reason']
            action = position['action']
            urgency = position.get('urgency', 'MEDIUM')

            urgency_icon = '🔴' if urgency == 'HIGH' else '🟡'
            print(f'{i}. {urgency_icon} {symbol} - {reason}')
            print(f'   建议行动: {action}')
        print()
    else:
        print('✅ 当前无风险持仓')
        print()

    # 具体建议
    recommendations = risk_analysis.get('recommendations', [])
    if recommendations:
        print('💡 风险建议:')
        for i, recommendation in enumerate(recommendations, 1):
            print(f'{i}. {recommendation}')
        print()

    # 风险指标详情
    if risk_analysis.get('risk_score', 0) > 0:
        print('📈 风险指标分析:')
        score = risk_analysis['risk_score']

        if score >= 70:
            print('   🔴 紧急风险: 风险评分过高，建议减仓或平仓')
        if score >= 50:
            print('   🟡 注意风险: 持仓集中度过高或临近到期')
        if score >= 30:
            print('   🟡 需要关注: 部分持仓开始出现风险迹象')
        else:
            print('   🟢 风险较低: 持仓状况健康')
        print()

    # 执行建议
    print('🎯 执行建议:')
    if risk_score >= 70:
        print('   ⚠️ 立即行动:')
        print('   • 优先处理高风险持仓')
        print('   • 考虑减仓以降低整体风险')
        print('   • 设置严格的止损保护')
    elif risk_score >= 40:
        print('   • 密切监控:')
        print('   • 定期检查持仓状态')
        print('   • 关注市场波动对持仓的影响')
        print('   • 评估是否需要调整仓位')
    else:
        print('   • 维持现状:')
        print('   • 继续监控风险指标')
        print('   • 考虑适当分散化投资')
        print('   • 保持适当的风险敞口')


def format_output_json(risk_analysis):
    """格式化为JSON输出"""
    output = {
        "timestamp": datetime.now().isoformat(),
        "risk_overview": {
            "total_positions": risk_analysis.get('total_positions', 0),
            "total_exposure": risk_analysis.get('total_exposure', 0),
            "risk_score": risk_analysis.get('risk_score', 0),
            "risk_level": _get_risk_level(risk_analysis.get('risk_score', 0))
        },
        "positions_at_risk": risk_analysis.get('positions_at_risk', []),
        "recommendations": risk_analysis.get('recommendations', []),
        "risk_metrics": {
            "concentration_risk": _check_concentration_risk(risk_analysis),
            "expiry_risk": _check_expiry_risk(risk_analysis),
            "loss_risk": _check_loss_risk(risk_analysis),
            "overall_health": _get_overall_health(risk_analysis)
        },
        "last_update": datetime.now().isoformat()
    }

    print(json.dumps(output, indent=2, ensure_ascii=False))


def _get_risk_level(score):
    """根据风险评分获取风险等级"""
    if score >= 70:
        return "HIGH"
    elif score >= 40:
        return "MEDIUM"
    else:
        return "LOW"


def _check_concentration_risk(risk_analysis):
    """检查集中度风险"""
    # 这里可以添加更详细的集中度分析逻辑
    score = risk_analysis.get('risk_score', 0)
    if score >= 50:
        return {"level": "HIGH", "description": "持仓集中度过高"}
    elif score >= 30:
        return {"level": "MEDIUM", "description": "存在一定集中度风险"}
    else:
        return {"level": "LOW", "description": "集中度风险较低"}


def _check_expiry_risk(risk_analysis):
    """检查到期风险"""
    positions_at_risk = risk_analysis.get('positions_at_risk', [])
    expiry_count = len([p for p in positions_at_risk if '到期' in p.get('reason', '')])

    if expiry_count > 0:
        return {"level": "HIGH", "count": expiry_count}
    else:
        return {"level": "LOW", "count": 0}


def _check_loss_risk(risk_analysis):
    """检查亏损风险"""
    positions_at_risk = risk_analysis.get('positions_at_risk', [])
    loss_count = len([p for p in positions_at_risk if '亏损' in p.get('reason', '')])

    if loss_count > 0:
        return {"level": "HIGH", "count": loss_count}
    else:
        return {"level": "LOW", "count": 0}


def _get_overall_health(risk_analysis):
    """获取整体健康状态"""
    score = risk_analysis.get('risk_score', 0)
    if score < 30:
        return "EXCELLENT"
    elif score < 50:
        return "GOOD"
    elif score < 70:
        return "FAIR"
    else:
        return "POOR"


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

        # 获取当前持仓
        positions = get_current_positions()
        if not positions:
            print('📊 当前无持仓')
            print('   系统状态: 正常，无持仓风险')
            return 0

        # 执行风险分析
        risk_analysis = run_position_risk_analysis(positions)

        # 根据格式输出结果
        if args.format == 'json':
            format_output_json(risk_analysis)
        else:
            format_output_table(risk_analysis)

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