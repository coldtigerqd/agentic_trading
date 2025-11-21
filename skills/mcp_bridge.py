"""
MCP 桥接 - 帮助 Claude Code 将 MCP 工具与 skills 集成的辅助函数。

重要：这些函数设计为在 Commander 工作流期间由 Claude Code 调用。
它们在 Python skills 库和仅 Claude Code 可访问的 MCP 工具之间架起桥梁。
"""

from typing import Dict, List, Any, Optional
from .execution_gate import OrderResult
from data_lake.db_helpers import update_trade_status


def execute_order_with_ibkr(
    validated_order: OrderResult,
    legs: List[Dict],
    symbol: str,
    strategy: str,
    max_risk: float,
    capital_required: float,
    metadata: Optional[Dict] = None
) -> OrderResult:
    """
    通过 IBKR MCP 执行已验证的订单。

    此函数应在 place_order_with_guard() 验证订单后由 Claude Code 调用。

    工作流：
        1. Python：place_order_with_guard() 验证并记录订单
        2. Claude：调用此函数通过 IBKR MCP 执行
        3. Python：更新数据库中的交易状态

    Args:
        validated_order: 来自 place_order_with_guard() 的结果
        legs: IBKR 格式的订单 leg
        symbol: 标的代码
        strategy: 策略名称
        max_risk: 最大风险（美元）
        capital_required: 所需资金（美元）
        metadata: 额外元数据

    Returns:
        如果成功，包含 IBKR order_id 的 OrderResult

    Example:
        ```python
        # 步骤 1：验证订单
        from skills import place_order_with_guard
        result = place_order_with_guard(...)

        # 步骤 2：如果验证通过，通过 IBKR 执行
        if result.success:
            from skills.mcp_bridge import execute_order_with_ibkr

            # Claude Code 调用 IBKR MCP 工具
            ibkr_result = mcp__ibkr__place_order(
                symbol=symbol,
                strategy=strategy,
                legs=legs,
                max_risk=max_risk,
                capital_required=capital_required,
                metadata=metadata
            )

            # 用 IBKR 订单 ID 更新交易状态
            final_result = execute_order_with_ibkr(
                validated_order=result,
                legs=legs,
                symbol=symbol,
                strategy=strategy,
                max_risk=max_risk,
                capital_required=capital_required,
                metadata={"ibkr_result": ibkr_result}
            )
        ```
    """
    if not validated_order.success:
        return validated_order

    # 从元数据中提取 IBKR 订单 ID
    # Claude 应该已经调用了 mcp__ibkr__place_order() 并在此处传递结果
    ibkr_order_id = None
    if metadata and "ibkr_result" in metadata:
        ibkr_result = metadata["ibkr_result"]
        ibkr_order_id = ibkr_result.get("order_id")

    if ibkr_order_id:
        # 用 IBKR 订单 ID 将交易状态更新为 SUBMITTED
        update_trade_status(
            trade_id=validated_order.trade_id,
            status="SUBMITTED",
            order_id=ibkr_order_id
        )

        return OrderResult(
            success=True,
            trade_id=validated_order.trade_id,
            order_id=ibkr_order_id,
            message=f"订单已成功提交至 IBKR（order_id={ibkr_order_id}）"
        )
    else:
        # IBKR 提交失败或未返回订单 ID
        update_trade_status(
            trade_id=validated_order.trade_id,
            status="FAILED"
        )

        return OrderResult(
            success=False,
            trade_id=validated_order.trade_id,
            error="订单提交至 IBKR 失败 (IBKR_SUBMISSION_FAILED)",
            message="IBKR MCP 未返回 order_id"
        )


def fetch_market_data_for_symbols(symbols: List[str]) -> Dict[str, Any]:
    """
    通过 ThetaData MCP 获取给定标的的市场数据。

    这是一个辅助函数，Claude Code 应使用它来构建
    consult_swarm() 的 market_data 字典。

    Args:
        symbols: 股票代码列表

    Returns:
        适合 consult_swarm() 的市场数据字典

    Example:
        ```python
        # Claude Code 获取市场数据
        symbols = ["AAPL", "NVDA", "AMD", "TSLA"]

        # 通过 ThetaData MCP 获取股票报价
        quotes = mcp__ThetaData__stock_snapshot_quote(symbol=symbols)

        # 为高 IV 标的获取期权数据
        options_data = {}
        for symbol in symbols:
            options = mcp__ThetaData__option_list_expirations(symbol=[symbol])
            # 筛选 30-45 DTE 到期日
            target_expiry = find_target_expiration(options, dte_range=(30, 45))

            options_chain = mcp__ThetaData__option_snapshot_quote(
                symbol=symbol,
                expiration=target_expiry
            )
            options_data[symbol] = options_chain

        # 构建市场快照
        market_data = fetch_market_data_for_symbols(symbols)
        market_data["quotes"] = quotes
        market_data["options_chains"] = options_data

        # 现在传递给群体
        from skills import consult_swarm
        signals = consult_swarm(sector="TECH", market_data=market_data)
        ```
    """
    from datetime import datetime

    return {
        "timestamp": datetime.now().isoformat(),
        "symbols": symbols,
        "quotes": {},  # Claude 应从 mcp__ThetaData__stock_snapshot_quote() 填充
        "options_chains": {},  # Claude 应从 mcp__ThetaData__option_snapshot_quote() 填充
        "account": {},  # Claude 应从 mcp__ibkr__get_account() 填充
        "positions": []  # Claude 应从 mcp__ibkr__get_positions() 填充
    }


def find_target_expiration(expirations: List[str], dte_range: tuple = (30, 45)) -> Optional[str]:
    """
    在目标 DTE 范围内找到最佳到期日。

    Args:
        expirations: YYYYMMDD 格式的到期日列表
        dte_range: (min_dte, max_dte) 元组

    Returns:
        到期日字符串或 None
    """
    from datetime import datetime, timedelta

    today = datetime.now()
    min_dte, max_dte = dte_range

    target_expirations = []
    for exp_str in expirations:
        try:
            exp_date = datetime.strptime(exp_str, "%Y%m%d")
            dte = (exp_date - today).days

            if min_dte <= dte <= max_dte:
                target_expirations.append((dte, exp_str))
        except ValueError:
            continue

    if not target_expirations:
        return None

    # 返回最接近范围中点的到期日
    target_dte = (min_dte + max_dte) // 2
    best_exp = min(target_expirations, key=lambda x: abs(x[0] - target_dte))
    return best_exp[1]


# === Claude Code 使用指南 ===
"""
当 Claude Code 作为 Commander 时，使用此模式：

```python
# === 感知阶段 ===
# 通过 IBKR MCP 获取账户和持仓
account = mcp__ibkr__get_account()
positions = mcp__ibkr__get_positions()

# 通过 ThetaData MCP 获取市场数据
symbols = ["AAPL", "NVDA", "AMD", "TSLA"]
quotes = mcp__ThetaData__stock_snapshot_quote(symbol=symbols)

# 获取期权数据
from skills.mcp_bridge import find_target_expiration
expirations = mcp__ThetaData__option_list_expirations(symbol=["NVDA"])
target_exp = find_target_expiration(expirations["NVDA"], dte_range=(30, 45))

options = mcp__ThetaData__option_snapshot_quote(
    symbol="NVDA",
    expiration=target_exp
)

# === 思考阶段 ===
from skills import consult_swarm

market_data = {
    "timestamp": datetime.now().isoformat(),
    "symbols": symbols,
    "quotes": quotes,
    "options_chains": {"NVDA": options},
    "account": account,
    "positions": positions
}

signals = consult_swarm(sector="TECH", market_data=market_data)

# === 决策阶段 ===
from skills import kelly_criterion

approved_trades = []
for signal in signals:
    if signal["signal"] == "NO_TRADE":
        continue

    # 计算仓位大小
    position_size = kelly_criterion(
        win_prob=signal["confidence"],
        win_amount=500,
        loss_amount=200,
        bankroll=account["net_liquidation"],
        fraction=0.25
    )

    # 应用安全限制
    if position_size <= 2000 and signal["params"]["max_risk"] <= 500:
        approved_trades.append(signal)

# === 执行阶段 ===
from skills import place_order_with_guard
from skills.mcp_bridge import execute_order_with_ibkr

for trade in approved_trades:
    # 步骤 1：通过安全层验证
    result = place_order_with_guard(
        symbol=trade["target"],
        strategy=trade["signal"],
        legs=trade["params"]["legs"],
        max_risk=trade["params"]["max_risk"],
        capital_required=trade["params"]["capital_required"],
        metadata={"signal_source": trade["instance_id"]}
    )

    if not result.success:
        print(f"❌ 交易被拒绝：{result.error}")
        continue

    # 步骤 2：通过 MCP 提交至 IBKR
    try:
        ibkr_result = mcp__ibkr__place_order(
            symbol=trade["target"],
            strategy=trade["signal"],
            legs=trade["params"]["legs"],
            max_risk=trade["params"]["max_risk"],
            capital_required=trade["params"]["capital_required"]
        )

        # 步骤 3：更新交易状态
        final_result = execute_order_with_ibkr(
            validated_order=result,
            legs=trade["params"]["legs"],
            symbol=trade["target"],
            strategy=trade["signal"],
            max_risk=trade["params"]["max_risk"],
            capital_required=trade["params"]["capital_required"],
            metadata={"ibkr_result": ibkr_result}
        )

        if final_result.success:
            print(f"✅ 交易已执行：{trade['target']}（order_id={final_result.order_id}）")
        else:
            print(f"❌ IBKR 提交失败：{final_result.error}")

    except Exception as e:
        print(f"❌ 提交至 IBKR 时出错：{e}")
        update_trade_status(result.trade_id, "FAILED")
```
"""
