"""
高级工作流技能 - 封装完整的交易分析流程。

这些技能是 Commander 的主要接口，每个技能代表一个完整的业务流程。
旨在替代大量内联Python代码，减少prompt消耗并提高稳定性。

🔒 架构锁定原则：禁止嵌入式脚本实现
- 所有命令必须使用这些预定义技能，绝不允许使用嵌入式大脚本
- 防止 f-string 嵌套、字符串拼接地狱、语法错误陷阱
- 确保稳定性、可维护性和调试友好性
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
import time
from datetime import datetime


def validate_architecture_compliance(operation_name: str = "unknown") -> Dict[str, Any]:
    """
    🔒 架构合规性验证函数

    强制确保所有操作都遵循技能层架构，防止嵌入式脚本错误。

    Args:
        operation_name: 操作名称，用于错误报告

    Returns:
        验证结果字典

    Raises:
        RuntimeError: 如果检测到架构违规
    """
    import inspect
    import traceback

    # 获取调用栈
    stack = inspect.stack()

    # 检查最近3个调用层
    for i, frame_info in enumerate(stack[1:4], 1):
        frame = frame_info.frame
        code = frame.f_code

        # 检查文件名和行号
        filename = frame_info.filename
        line_no = frame_info.lineno

        # 获取源代码行
        try:
            lines = inspect.getsourcelines(code)
            for j, line in enumerate(lines[0], 1):
                # 检查危险的架构模式
                if "python3 -c" in line:
                    raise RuntimeError(
                        f"🚫 架构违规：检测到嵌入式脚本执行在 {filename}:{line_no + j}\n"
                        f"禁止使用 'python3 -c' 模式，必须使用预定义技能函数\n"
                        f"违规代码: {line.strip()}\n"
                        f"操作: {operation_name}\n"
                        f"请立即停止并使用 run_market_health_check()、run_full_trading_analysis() 等技能函数"
                    )

                # 检查大字符串拼接（潜在的脚本嵌入）
                if "f'''" in line or 'f"""' in line:
                    if len(line) > 100:  # 可能是大型脚本
                        raise RuntimeError(
                            f"🚫 架构违规：检测到大型f-string字符串在 {filename}:{line_no + j}\n"
                            f"禁止使用大型嵌入式字符串，请分解为多个技能函数调用\n"
                            f"违规代码: {line.strip()[:100]}...\n"
                            f"操作: {operation_name}"
                        )

                # 检查Bash执行模式
                if "bash(" in line and "python" in line:
                    raise RuntimeError(
                        f"🚫 架构违规：检测到Bash+Python组合执行在 {filename}:{line_no + j}\n"
                        f"禁止通过Bash执行Python代码，请直接使用技能函数\n"
                        f"违规代码: {line.strip()}\n"
                        f"操作: {operation_name}"
                    )

        except OSError:
            # 无法读取源代码，跳过检查
            pass

    return {
        "compliance": "PASS",
        "operation": operation_name,
        "validation_time": datetime.now().isoformat(),
        "message": "架构合规性检查通过"
    }

# 导入原子技能
from .market_calendar import get_market_session_info
from .data_sync import (
    sync_watchlist_incremental,
    get_data_freshness_report
)
from .market_data import (
    get_watchlist,
    get_latest_price,
    get_multi_timeframe_data
)
from .technical_indicators import (
    calculate_historical_volatility,
    detect_trend
)
from .swarm_core import consult_swarm
from .execution_gate import place_order_with_guard, OrderResult


@dataclass
class TradingAnalysisResult:
    """交易分析结果结构"""

    # 市场状态
    market_session: str
    market_open: bool

    # 账户信息（需要通过MCP获取，这里是占位符）
    account_value: Optional[float] = None
    buying_power: Optional[float] = None

    # 数据质量
    total_symbols: int = 0
    stale_symbols: int = 0
    fresh_symbols: int = 0

    # 市场背景
    market_trend: Optional[str] = None
    market_volatility: Optional[float] = None

    # 蜂群信号
    signals: List[Dict] = None
    high_confidence_signals: List[Dict] = None

    # 执行结果
    orders_submitted: List[OrderResult] = None
    orders_rejected: List[OrderResult] = None

    # 元数据
    execution_time: float = 0.0
    errors: List[str] = None
    warnings: List[str] = None

    def __post_init__(self):
        """初始化列表字段"""
        if self.signals is None:
            self.signals = []
        if self.high_confidence_signals is None:
            self.high_confidence_signals = []
        if self.orders_submitted is None:
            self.orders_submitted = []
        if self.orders_rejected is None:
            self.orders_rejected = []
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []

    def to_dict(self) -> Dict:
        """转换为字典（用于JSON序列化）"""
        result = asdict(self)
        # 转换OrderResult对象为字典
        result['orders_submitted'] = [
            asdict(order) if hasattr(order, '__dataclass_fields__') else order
            for order in self.orders_submitted
        ]
        result['orders_rejected'] = [
            asdict(order) if hasattr(order, '__dataclass_fields__') else order
            for order in self.orders_rejected
        ]
        return result


def run_full_trading_analysis(
    sectors: List[str] = None,
    min_confidence: float = 0.75,
    max_orders_per_run: int = 2,
    skip_sync_if_market_closed: bool = True
) -> TradingAnalysisResult:
    """
    执行完整的交易分析流程。

    🔒 架构锁定：此函数是/trading:trade-analysis命令的唯一正确实现方式
    禁止任何形式的嵌入式脚本或绕过此函数的行为

    这是 Commander 的主要入口点，封装了完整的交易决策流程：
    1. 架构合规性验证
    2. 检查市场状态
    3. 同步数据（如果需要）
    4. 评估市场背景
    5. 咨询蜂群智能
    6. 过滤和执行信号

    参数:
        sectors: 要分析的板块列表（默认["ALL"]）
        min_confidence: 最低信号置信度阈值（默认0.75）
        max_orders_per_run: 每次运行最多执行的订单数（默认2）
        skip_sync_if_market_closed: 市场关闭时跳过数据同步（默认True）

    返回:
        TradingAnalysisResult: 包含完整分析结果的结构化对象

    示例:
        ```python
        from skills import run_full_trading_analysis

        # Commander 只需一行调用
        result = run_full_trading_analysis(
            sectors=["TECH", "FINANCE"],
            min_confidence=0.80,
            max_orders_per_run=3
        )

        # 访问结果
        print(f"市场状态: {result.market_session}")
        print(f"获得信号: {len(result.signals)}")
        print(f"提交订单: {len(result.orders_submitted)}")
        print(f"执行时间: {result.execution_time:.2f}秒")
        ```

    注意:
        - 此技能包含完整的错误处理和降级逻辑
        - 如果市场关闭且数据过期，将跳过蜂群咨询
        - 所有订单都通过 place_order_with_guard() 安全验证
    """
    if sectors is None:
        sectors = ["ALL"]

    # 🔒 架构合规性验证 - 防止嵌入式脚本执行
    compliance = validate_architecture_compliance("run_full_trading_analysis")
    if compliance["compliance"] != "PASS":
        result = TradingAnalysisResult(
            market_session="ERROR",
            market_open=False,
            execution_error=f"架构违规: {compliance.get('message', 'Unknown violation')}",
            execution_time=0.0
        )
        return result

    start_time = time.time()
    result = TradingAnalysisResult(
        market_session="UNKNOWN",
        market_open=False
    )

    try:
        # ============================================================
        # 步骤 1: 市场状态检查
        # ============================================================
        session_info = get_market_session_info()
        result.market_session = session_info['session']
        result.market_open = session_info['market_open']

        if not result.market_open:
            result.warnings.append(
                f"市场已关闭 ({result.market_session})"
            )

        # ============================================================
        # 步骤 2: 数据新鲜度检查
        # ============================================================
        freshness_report = get_data_freshness_report()
        result.total_symbols = len(freshness_report['symbols'])
        result.stale_symbols = sum(
            1 for s in freshness_report['symbols'] if s['is_stale']
        )
        result.fresh_symbols = result.total_symbols - result.stale_symbols

        if result.stale_symbols == result.total_symbols and result.total_symbols > 0:
            result.warnings.append(
                f"所有 {result.total_symbols} 个标的数据过期"
            )

        # ============================================================
        # 步骤 3: 数据同步（可选）
        # ============================================================
        try:
            sync_info = sync_watchlist_incremental(
                skip_if_market_closed=skip_sync_if_market_closed
            )

            if not sync_info['success']:
                # 同步失败，添加错误信息
                for error in sync_info.get('errors', []):
                    result.warnings.append(f"数据同步错误: {error}")
            elif sync_info['synced_count'] == 0:
                # 没有同步任何数据
                result.warnings.append(
                    f"数据同步完成，但未更新数据 ({sync_info['total_symbols']} 个标的)"
                )
            else:
                # 同步成功
                result.warnings.append(
                    f"数据同步成功: {sync_info['synced_count']}/{sync_info['total_symbols']} 个标的"
                )
        except Exception as e:
            result.warnings.append(f"数据同步失败: {str(e)}")

        # ============================================================
        # 步骤 4: 市场背景分析（SPY）
        # ============================================================
        try:
            spy_mtf = get_multi_timeframe_data(
                symbol="SPY",
                intervals=["daily"],
                lookback_days=30
            )

            if spy_mtf['success']:
                daily_bars = spy_mtf['timeframes']['daily']['bars']

                if len(daily_bars) >= 20:
                    # 检测趋势
                    result.market_trend = detect_trend(daily_bars[-30:] if len(daily_bars) >= 30 else daily_bars)

                    # 计算波动率
                    closes = [bar['close'] for bar in daily_bars[-21:]]
                    if len(closes) >= 21:
                        result.market_volatility = calculate_historical_volatility(closes)

        except Exception as e:
            result.warnings.append(f"市场背景分析失败: {str(e)}")

        # ============================================================
        # 步骤 5: 蜂群智能咨询
        # ============================================================
        # 只在数据相对新鲜时咨询蜂群
        if result.fresh_symbols > 0 or not skip_sync_if_market_closed:
            try:
                # 构建市场快照
                market_snapshot = {}
                watchlist = get_watchlist()

                # 限制前10个标的，避免过度查询
                symbols_to_query = watchlist['symbols'][:10] if watchlist['symbols'] else []

                for sym_info in symbols_to_query:
                    symbol = sym_info['symbol']
                    try:
                        latest = get_latest_price(symbol)

                        if latest['success']:
                            market_snapshot[symbol] = {
                                'price': latest['price'],
                                'age_seconds': latest['age_seconds'],
                                'is_stale': latest['is_stale']
                            }
                    except Exception as e:
                        # 单个标的失败不影响整体
                        result.warnings.append(f"获取{symbol}价格失败: {str(e)}")

                # 咨询蜂群（每个板块）
                for sector in sectors:
                    try:
                        signals = consult_swarm(
                            sector=sector,
                            market_data={
                                "snapshot": market_snapshot,
                                "context": {
                                    "spy_trend": result.market_trend,
                                    "market_volatility": result.market_volatility
                                }
                            }
                        )
                        result.signals.extend(signals)
                    except Exception as e:
                        result.errors.append(f"蜂群咨询失败 ({sector}): {str(e)}")

            except Exception as e:
                result.errors.append(f"蜂群咨询流程失败: {str(e)}")
        else:
            result.warnings.append(
                "所有数据过期，跳过蜂群咨询以避免使用过期数据"
            )

        # ============================================================
        # 步骤 6: 信号过滤
        # ============================================================
        result.high_confidence_signals = [
            s for s in result.signals
            if s.get('confidence', 0) >= min_confidence
        ]

        # ============================================================
        # 步骤 7: 订单执行（占位符 - 实际执行需要Commander通过MCP获取账户）
        # ============================================================
        # 注意: 这里只是示例框架，实际订单执行应该由Commander在获取
        # 账户信息后调用 place_order_with_guard()

        # 为每个高置信度信号准备订单（但不实际执行）
        for i, signal in enumerate(result.high_confidence_signals[:max_orders_per_run]):
            # 这里只是标记信号，实际执行由Commander决定
            result.warnings.append(
                f"高置信信号 {i+1}: {signal.get('target')} - "
                f"策略={signal.get('signal')}, "
                f"置信度={signal.get('confidence', 0):.2f}"
            )

    except Exception as e:
        result.errors.append(f"致命错误: {str(e)}")

    finally:
        result.execution_time = time.time() - start_time

    return result


def run_market_health_check() -> Dict[str, Any]:
    """
    快速市场健康检查（轻量级）。

    检查：
    - 市场交易时段
    - 数据新鲜度
    - 关键指数状态（SPY, QQQ）

    返回:
        {
            "market_open": bool,
            "session": str,
            "data_quality": str,  # "GOOD", "STALE", "CRITICAL"
            "spy_price": float,
            "qqq_price": float,
            "spy_age_minutes": float,
            "qqq_age_minutes": float,
            "warnings": List[str],
            "timestamp": str
        }

    示例:
        ```python
        from skills import run_market_health_check

        health = run_market_health_check()

        if health['data_quality'] == 'CRITICAL':
            print("⚠️ 数据质量严重问题，建议延迟交易")
        elif health['market_open']:
            print("✅ 市场开盘，数据质量良好")
        ```
    """
    warnings = []

    # 市场状态
    try:
        session_info = get_market_session_info()
        market_open = session_info['market_open']
        session = session_info['session']
    except Exception as e:
        warnings.append(f"市场状态检查失败: {str(e)}")
        market_open = False
        session = "UNKNOWN"

    # 数据质量
    try:
        freshness = get_data_freshness_report()
        stale_count = sum(1 for s in freshness['symbols'] if s['is_stale'])
        total_count = len(freshness['symbols'])

        if total_count == 0:
            data_quality = "NO_DATA"
            warnings.append("没有监控标的数据")
        elif stale_count == 0:
            data_quality = "GOOD"
        elif stale_count < total_count * 0.3:
            data_quality = "STALE"
            warnings.append(f"{stale_count}/{total_count} 标的数据过期")
        else:
            data_quality = "CRITICAL"
            warnings.append(f"严重: {stale_count}/{total_count} 标的数据过期")
    except Exception as e:
        warnings.append(f"数据质量检查失败: {str(e)}")
        data_quality = "ERROR"

    # 关键指数价格
    spy_price = None
    spy_age_minutes = None
    qqq_price = None
    qqq_age_minutes = None

    try:
        spy_latest = get_latest_price("SPY")
        if spy_latest['success']:
            spy_price = spy_latest['price']
            spy_age_minutes = spy_latest['age_seconds'] / 60
    except Exception as e:
        warnings.append(f"SPY价格获取失败: {str(e)}")

    try:
        qqq_latest = get_latest_price("QQQ")
        if qqq_latest['success']:
            qqq_price = qqq_latest['price']
            qqq_age_minutes = qqq_latest['age_seconds'] / 60
    except Exception as e:
        warnings.append(f"QQQ价格获取失败: {str(e)}")

    return {
        "market_open": market_open,
        "session": session,
        "data_quality": data_quality,
        "spy_price": spy_price,
        "qqq_price": qqq_price,
        "spy_age_minutes": spy_age_minutes,
        "qqq_age_minutes": qqq_age_minutes,
        "warnings": warnings,
        "timestamp": datetime.now().isoformat()
    }


def run_position_risk_analysis(positions: List[Dict]) -> Dict[str, Any]:
    """
    分析当前持仓的风险。

    参数:
        positions: 持仓列表（通过 MCP get_positions() 获取）
            每个持仓应包含字段: symbol, contract_type, expiry,
            unrealized_pnl_percent, market_value

    返回:
        {
            "total_positions": int,
            "total_exposure": float,
            "positions_at_risk": List[Dict],  # 临近到期、深度亏损等
            "recommendations": List[str],
            "risk_score": float  # 0-100，越高风险越大
        }

    示例:
        ```python
        from mcp__ibkr import get_positions
        from skills import run_position_risk_analysis

        positions = get_positions()
        risk_analysis = run_position_risk_analysis(positions)

        print(f"风险评分: {risk_analysis['risk_score']}/100")
        print(f"风险持仓: {len(risk_analysis['positions_at_risk'])}")
        for rec in risk_analysis['recommendations']:
            print(f"  • {rec}")
        ```
    """
    positions_at_risk = []
    recommendations = []
    total_exposure = 0
    risk_score = 0

    for pos in positions:
        # 兼容两种命名格式：snake_case (market_value) 和 camelCase (marketValue)
        position_value = abs(pos.get('market_value', pos.get('marketValue', 0)))
        total_exposure += position_value

        # 检查期权到期
        # 兼容两种命名格式：contract_type / secType
        is_option = pos.get('contract_type') == 'OPT' or pos.get('secType') == 'OPT'
        if is_option:
            # 兼容两种命名格式：expiry / lastTradeDateOrContractMonth
            expiry_str = pos.get('expiry', pos.get('lastTradeDateOrContractMonth'))
            if expiry_str:
                try:
                    expiry_date = datetime.strptime(expiry_str, "%Y%m%d")
                    days_to_expiry = (expiry_date - datetime.now()).days

                    # 临近到期（< 7天）
                    if days_to_expiry <= 7:
                        positions_at_risk.append({
                            'symbol': pos['symbol'],
                            'reason': f'临近到期（{days_to_expiry}天）',
                            'action': 'CLOSE_OR_ROLL',
                            'urgency': 'HIGH' if days_to_expiry <= 3 else 'MEDIUM'
                        })
                        recommendations.append(
                            f"{pos['symbol']}: 考虑平仓或滚动（{days_to_expiry}天到期）"
                        )
                        risk_score += 15 if days_to_expiry <= 3 else 10

                except (ValueError, TypeError) as e:
                    recommendations.append(
                        f"{pos.get('symbol', 'UNKNOWN')}: 到期日期格式错误"
                    )

        # 检查大额亏损（> 15%）
        # 兼容两种命名格式和计算方式
        unrealized_pnl_pct = pos.get('unrealized_pnl_percent')
        if unrealized_pnl_pct is None:
            # 尝试从 unrealizedPNL 和 marketValue 计算百分比
            unrealized_pnl = pos.get('unrealizedPNL', 0)
            market_value = pos.get('marketValue', pos.get('market_value', 0))
            if market_value != 0:
                unrealized_pnl_pct = (unrealized_pnl / abs(market_value)) * 100
            else:
                unrealized_pnl_pct = 0

        if unrealized_pnl_pct < -15:
            # 获取实际亏损金额用于显示
            unrealized_pnl = pos.get('unrealizedPNL', pos.get('unrealized_pnl', 0))
            reason = f"大额亏损（-${abs(unrealized_pnl):.2f}, {unrealized_pnl_pct:.2f}%）"

            positions_at_risk.append({
                'symbol': pos['symbol'],
                'reason': reason,
                'action': 'REVIEW_STOP_LOSS',
                'urgency': 'HIGH' if unrealized_pnl_pct < -25 else 'MEDIUM'
            })
            recommendations.append(
                f"{pos['symbol']}: 亏损 {unrealized_pnl_pct:.1f}%，考虑止损"
            )
            risk_score += min(abs(unrealized_pnl_pct), 30)  # 最多增加30分

    # 检查集中度风险
    if len(positions) > 0 and total_exposure > 0:
        # 使用兼容的字段获取器
        largest_position = max(positions, key=lambda p: abs(p.get('market_value', p.get('marketValue', 0))))
        largest_position_value = abs(largest_position.get('market_value', largest_position.get('marketValue', 0)))
        largest_position_pct = largest_position_value / total_exposure * 100

        if largest_position_pct > 40:
            recommendations.append(
                f"持仓集中度过高: {largest_position['symbol']} 占 {largest_position_pct:.1f}%"
            )
            risk_score += 20

    # 限制risk_score在0-100之间
    risk_score = min(100, max(0, risk_score))

    return {
        "total_positions": len(positions),
        "total_exposure": total_exposure,
        "positions_at_risk": positions_at_risk,
        "recommendations": recommendations,
        "risk_score": risk_score
    }
