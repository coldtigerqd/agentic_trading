#!/usr/bin/env python3
"""
Agentic AlphaHive - 完整交易分析工具

执行 7 步交易分析流程：
1. 市场健康检查
2. 账户状态
3. 持仓风险检查
4. 蜂群分析
5. 信号过滤
6. 风险评估与仓位计算
7. 执行决策

使用方法：
    python runtime/trade_analyze.py --sector=tech --confidence=0.85
    python runtime/trade_analyze.py --help
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import argparse
from datetime import datetime
from typing import List, Dict, Optional
import json

# Import skills and MCP tools
from skills import (
    run_market_health_check,
    run_full_trading_analysis,
    run_position_risk_analysis,
    kelly_criterion
)


class Colors:
    """ANSI 颜色代码"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def print_header(text: str):
    """打印标题"""
    print(f"\n{Colors.BOLD}{Colors.OKBLUE}{'=' * 70}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.OKBLUE}{text}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.OKBLUE}{'=' * 70}{Colors.ENDC}\n")


def print_step(step: str):
    """打印步骤"""
    print(f"\n{Colors.BOLD}{Colors.OKCYAN}{step}{Colors.ENDC}")
    print(f"{Colors.OKCYAN}{'=' * 50}{Colors.ENDC}\n")


def print_success(text: str):
    """打印成功消息"""
    print(f"{Colors.OKGREEN}✓ {text}{Colors.ENDC}")


def print_warning(text: str):
    """打印警告消息"""
    print(f"{Colors.WARNING}⚠️  {text}{Colors.ENDC}")


def print_error(text: str):
    """打印错误消息"""
    print(f"{Colors.FAIL}✗ {text}{Colors.ENDC}")


def step1_market_health() -> Dict:
    """步骤 1: 市场健康检查"""
    print_step("步骤 1/7: 市场健康检查")

    result = run_market_health_check()

    print(f"市场状态: {result['session']}")
    print(f"市场开盘: {'✅ YES' if result['market_open'] else '❌ NO'}")
    print(f"数据质量: {result['data_quality']}")

    if result.get('spy_price'):
        print(f"SPY: ${result['spy_price']:.2f}")
    if result.get('qqq_price'):
        print(f"QQQ: ${result['qqq_price']:.2f}")

    if result.get('warnings'):
        print("\n警告:")
        for w in result['warnings']:
            print_warning(w)

    # 检查数据质量
    if result['data_quality'] == 'CRITICAL':
        print_error("\n数据质量为 CRITICAL，无法进行可靠分析")
        print_warning("建议: 使用 python runtime/data_sync_daemon.py --once 同步数据")
        return {'should_continue': False, 'reason': 'CRITICAL data quality'}

    # 检查市场状态
    if not result['market_open']:
        print_warning(f"\n市场当前关闭 ({result['session']})")
        response = input("\n是否继续分析并准备下一交易日的订单？(y/n): ")
        if response.lower() != 'y':
            return {'should_continue': False, 'reason': 'Market closed, user declined'}

    return {
        'should_continue': True,
        'market_open': result['market_open'],
        'session': result['session'],
        'data_quality': result['data_quality']
    }


def step2_account_status() -> Optional[Dict]:
    """步骤 2: 账户状态"""
    print_step("步骤 2/7: 账户状态")

    try:
        # 导入 IBKR MCP 工具（动态导入以处理可能的导入错误）
        import importlib
        mcp_module = importlib.import_module('mcp-client')

        # 这里应该调用 MCP 工具，但为了避免复杂的动态调用
        # 我们直接返回一个提示
        print_warning("需要 IBKR 连接才能获取账户信息")
        print("请确保 TWS/Gateway 正在运行")

        # 模拟账户数据（实际应该调用 mcp__ibkr__get_account）
        print("\n提示: 此步骤需要通过 Claude Code 的 MCP 接口调用")
        print("在实际环境中会自动获取账户信息")

        return None

    except Exception as e:
        print_error(f"获取账户信息失败: {e}")
        return None


def step3_position_risk(positions: List[Dict]) -> Optional[Dict]:
    """步骤 3: 持仓风险检查"""
    print_step("步骤 3/7: 持仓风险检查")

    if not positions:
        print("当前无持仓")
        return {'risk_score': 0, 'should_continue': True}

    result = run_position_risk_analysis(positions)

    print(f"持仓数量: {result.total_positions}")
    print(f"总风险敞口: ${result.total_exposure:,.2f}")
    print(f"风险评分: {result.risk_score}/100")

    if result.risk_score > 70:
        risk_level = "高"
    elif result.risk_score > 40:
        risk_level = "中"
    else:
        risk_level = "低"
    print(f"风险等级: {risk_level}")

    if result.positions_at_risk:
        print("\n⚠️  高风险持仓:")
        for pos in result.positions_at_risk:
            print(f"  - {pos['symbol']}: {pos['reason']} (建议: {pos['action']})")

    if result.recommendations:
        print("\n建议:")
        for rec in result.recommendations:
            print(f"  • {rec}")

    if result.risk_score > 70:
        print_warning("\n当前持仓风险较高")
        response = input("是否继续分析新交易信号？(y/n): ")
        if response.lower() != 'y':
            return {'should_continue': False, 'reason': 'High position risk'}

    return {
        'should_continue': True,
        'risk_score': result.risk_score
    }


def step4_swarm_analysis() -> Dict:
    """步骤 4: 蜂群分析"""
    print_step("步骤 4/7: 蜂群分析")

    print("正在启动蜂群智能单元...")

    result = run_full_trading_analysis()

    print(f"市场状态: {result.market_session}")
    print(f"数据状态: {result.fresh_symbols}/{result.total_symbols} 新鲜")

    if result.warnings:
        print("\n警告:")
        for w in result.warnings:
            print_warning(w)

    if result.errors:
        print("\n错误:")
        for e in result.errors:
            print_error(e)

    print(f"\n执行时间: {result.execution_time:.2f}秒")
    print(f"原始信号: {len(result.signals)}")
    print(f"高置信信号: {len(result.high_confidence_signals)}")

    return {
        'signals': result.signals,
        'high_confidence_signals': result.high_confidence_signals,
        'warnings': result.warnings,
        'errors': result.errors
    }


def step5_filter_signals(
    signals: List,
    min_confidence: float,
    max_signals: int
) -> List:
    """步骤 5: 信号过滤"""
    print_step("步骤 5/7: 信号过滤")

    print(f"过滤条件:")
    print(f"  - 最低置信度: {min_confidence:.2f}")
    print(f"  - 最多信号数: {max_signals}")

    # 过滤并排序
    filtered = [s for s in signals if s.confidence >= min_confidence]
    filtered = sorted(filtered, key=lambda x: x.confidence, reverse=True)
    filtered = filtered[:max_signals]

    print(f"\n过滤结果: {len(filtered)} 个信号")

    if not filtered:
        print_warning("未找到符合条件的信号")
        print("建议: 降低置信度阈值或分析其他板块")
        return []

    print("\n高置信信号:")
    print("-" * 70)
    print(f"{'#':<3} {'标的':<6} {'策略':<15} {'置信度':<8} {'预期收益':<10} {'最大风险':<10}")
    print("-" * 70)

    for i, sig in enumerate(filtered, 1):
        print(f"{i:<3} {sig.symbol:<6} {sig.strategy:<15} {sig.confidence:<8.2f} "
              f"${sig.expected_return:<9.0f} ${sig.max_risk:<9.0f}")

    return filtered


def step6_risk_assessment(
    signals: List,
    account_value: float,
    current_positions: List
) -> List[Dict]:
    """步骤 6: 风险评估与仓位计算"""
    print_step("步骤 6/7: 风险评估与仓位计算")

    if not signals:
        print("无信号可评估")
        return []

    assessed_signals = []

    print("\n仓位计算 (Kelly Criterion, 1/4 Kelly):")
    print("-" * 70)
    print(f"{'标的':<6} {'建议仓位':<12} {'Kelly仓位':<12} {'最大风险':<12} {'状态':<10}")
    print("-" * 70)

    for sig in signals:
        # 计算 Kelly 仓位
        # 这里需要根据信号的胜率和盈亏比计算
        # 简化示例：假设胜率 = 置信度，盈亏比 = 预期收益/最大风险
        win_rate = sig.confidence
        profit_loss_ratio = sig.expected_return / sig.max_risk if sig.max_risk > 0 else 1.0

        kelly_result = kelly_criterion(
            win_rate=win_rate,
            profit_loss_ratio=profit_loss_ratio,
            capital=account_value,
            fraction=0.25  # 保守的 1/4 Kelly
        )

        kelly_position = kelly_result['position_size']

        # 应用限额
        max_position = min(kelly_position, 2000)  # 单笔最大 $2,000
        max_position = max(max_position, 0)  # 不能为负

        # 检查是否低于最小值
        if max_position < 100:
            status = "❌ 太小"
        elif max_position >= 2000:
            status = "⚠️  已限额"
        else:
            status = "✓ 通过"

        assessed_signals.append({
            'signal': sig,
            'kelly_position': kelly_position,
            'recommended_position': max_position,
            'max_risk': sig.max_risk,
            'expected_return': sig.expected_return,
            'status': status
        })

        print(f"{sig.symbol:<6} ${max_position:<11.0f} ${kelly_position:<11.0f} "
              f"${sig.max_risk:<11.0f} {status:<10}")

    # 过滤掉太小的仓位
    assessed_signals = [s for s in assessed_signals if s['recommended_position'] >= 100]

    if not assessed_signals:
        print_warning("\n所有信号的建议仓位都低于最小值 ($100)")
        return []

    # 投资组合检查
    print("\n投资组合检查:")
    total_capital = sum(s['recommended_position'] for s in assessed_signals)
    total_risk = sum(s['max_risk'] for s in assessed_signals)

    print(f"  总资金需求: ${total_capital:,.0f}")
    print(f"  总风险敞口: ${total_risk:,.0f}")

    if total_risk > 1000:
        print_warning(f"  ⚠️  总风险 (${total_risk:.0f}) 接近每日限额 ($1,000)")

    return assessed_signals


def step7_execution_decision(
    assessed_signals: List[Dict],
    prepare_mode: bool = True
) -> Dict:
    """步骤 7: 执行决策"""
    print_step("步骤 7/7: 执行决策")

    if not assessed_signals:
        print("无可执行的订单")
        return {'orders_prepared': 0, 'orders_submitted': 0}

    print(f"\n准备执行的订单 ({len(assessed_signals)} 个):\n")

    for i, item in enumerate(assessed_signals, 1):
        sig = item['signal']
        print(f"{i}. {sig.symbol} {sig.strategy}")
        print(f"   建议仓位: ${item['recommended_position']:.0f}")
        print(f"   最大风险: ${item['max_risk']:.0f}")
        print(f"   预期收益: ${item['expected_return']:.0f}")
        print(f"   置信度: {sig.confidence:.2f}")
        print()

    total_capital = sum(s['recommended_position'] for s in assessed_signals)
    total_risk = sum(s['max_risk'] for s in assessed_signals)
    total_return = sum(s['expected_return'] for s in assessed_signals)

    print("总计:")
    print(f"  订单数量: {len(assessed_signals)}")
    print(f"  总资金: ${total_capital:,.0f}")
    print(f"  总风险: ${total_risk:,.0f}")
    print(f"  预期收益: ${total_return:,.0f}")

    if prepare_mode:
        print_warning("\n准备模式: 订单已生成但未提交")
        print("等待市场开盘后可使用此清单执行交易")

        # 保存到文件
        output_file = f"orders_prepared_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        output_path = project_root / "logs" / output_file
        output_path.parent.mkdir(exist_ok=True)

        with open(output_path, 'w') as f:
            # 简化信号对象为字典
            simplified = []
            for item in assessed_signals:
                sig = item['signal']
                simplified.append({
                    'symbol': sig.symbol,
                    'strategy': sig.strategy,
                    'confidence': sig.confidence,
                    'recommended_position': item['recommended_position'],
                    'max_risk': item['max_risk'],
                    'expected_return': item['expected_return']
                })

            json.dump({
                'timestamp': datetime.now().isoformat(),
                'orders': simplified,
                'totals': {
                    'count': len(assessed_signals),
                    'capital': total_capital,
                    'risk': total_risk,
                    'expected_return': total_return
                }
            }, f, indent=2)

        print(f"\n订单清单已保存: {output_path}")

        return {
            'orders_prepared': len(assessed_signals),
            'orders_submitted': 0,
            'output_file': str(output_path)
        }

    else:
        print_warning("\n实时模式: 准备提交订单")
        response = input("\n确认执行这些订单？(yes/no): ")

        if response.lower() != 'yes':
            print("已取消订单执行")
            return {'orders_prepared': 0, 'orders_submitted': 0}

        print_error("\n订单执行功能需要通过 MCP 接口调用")
        print("请使用 Claude Code 环境执行此脚本")

        return {
            'orders_prepared': len(assessed_signals),
            'orders_submitted': 0
        }


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='Agentic AlphaHive 完整交易分析工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 分析科技板块，最低置信度 0.85
  python runtime/trade_analyze.py --sector=tech --confidence=0.85

  # 分析所有板块，返回最多 5 个信号
  python runtime/trade_analyze.py --sector=ALL --max-signals=5

  # 准备模式（默认，不执行订单）
  python runtime/trade_analyze.py --prepare

  # 实时模式（需要确认后执行）
  python runtime/trade_analyze.py --execute
        """
    )

    parser.add_argument(
        '--sector',
        default='ALL',
        choices=['tech', 'finance', 'healthcare', 'energy', 'ALL'],
        help='分析的板块 (默认: ALL)'
    )

    parser.add_argument(
        '--confidence',
        type=float,
        default=0.75,
        help='最低置信度阈值 0.0-1.0 (默认: 0.75)'
    )

    parser.add_argument(
        '--max-signals',
        type=int,
        default=10,
        help='最多返回的信号数 (默认: 10)'
    )

    parser.add_argument(
        '--prepare',
        action='store_true',
        default=True,
        help='准备模式：生成订单但不执行 (默认)'
    )

    parser.add_argument(
        '--execute',
        action='store_true',
        help='执行模式：提交订单到 IBKR'
    )

    args = parser.parse_args()

    # 验证参数
    if not 0.0 <= args.confidence <= 1.0:
        print_error(f"置信度必须在 0.0-1.0 范围内，当前: {args.confidence}")
        sys.exit(1)

    if args.max_signals < 1:
        print_error(f"最多信号数必须 >= 1，当前: {args.max_signals}")
        sys.exit(1)

    prepare_mode = not args.execute

    # 开始分析
    print_header("🚀 Agentic AlphaHive - 交易分析")

    print(f"参数设置:")
    print(f"  板块: {args.sector}")
    print(f"  最低置信度: {args.confidence}")
    print(f"  最多信号: {args.max_signals}")
    print(f"  模式: {'准备模式' if prepare_mode else '执行模式'}")

    # 步骤 1: 市场健康检查
    step1_result = step1_market_health()
    if not step1_result['should_continue']:
        print_error(f"\n分析终止: {step1_result['reason']}")
        sys.exit(1)

    # 步骤 2: 账户状态
    account = step2_account_status()

    # 使用模拟账户数据（实际应从 MCP 获取）
    account_value = 1000000  # $1M

    # 步骤 3: 持仓风险
    # 实际应从 MCP 获取
    positions = []
    step3_result = step3_position_risk(positions)

    if step3_result and not step3_result.get('should_continue', True):
        print_error(f"\n分析终止: {step3_result.get('reason', 'Unknown')}")
        sys.exit(1)

    # 步骤 4: 蜂群分析
    step4_result = step4_swarm_analysis()

    signals = step4_result['high_confidence_signals']

    if not signals:
        print_warning("\n蜂群分析未生成信号")
        print("可能原因:")
        for w in step4_result['warnings']:
            print(f"  - {w}")
        sys.exit(0)

    # 步骤 5: 信号过滤
    filtered_signals = step5_filter_signals(
        signals,
        args.confidence,
        args.max_signals
    )

    if not filtered_signals:
        print_error("\n无符合条件的信号")
        sys.exit(0)

    # 步骤 6: 风险评估
    assessed_signals = step6_risk_assessment(
        filtered_signals,
        account_value,
        positions
    )

    if not assessed_signals:
        print_error("\n风险评估后无可执行订单")
        sys.exit(0)

    # 步骤 7: 执行决策
    result = step7_execution_decision(assessed_signals, prepare_mode)

    # 总结
    print_header("📊 分析完成")

    print(f"准备订单: {result['orders_prepared']}")
    print(f"已提交订单: {result['orders_submitted']}")

    if result.get('output_file'):
        print(f"\n订单清单: {result['output_file']}")

    print_success("\n✅ 交易分析流程完成")


if __name__ == '__main__':
    main()
