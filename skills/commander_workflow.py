"""
Commander 工作流 - Claude Code 集成示例。

本模块演示 Claude Code (Commander) 应如何结合使用
MCP 工具和技能库(Claude Code Skills)来执行交易周期。

重要提示：此模块旨在由 Claude Code 执行，而非独立脚本运行。
此处的函数展示了当 Claude 被 main_loop.py 调用时的预期工作流。
"""

from typing import Dict, List, Any
from datetime import datetime


def commander_workflow_example():
    """
    示例工作流，展示 Commander (Claude Code) 应如何集成
    MCP 工具和技能库。

    这是供 Claude Code 遵循的参考实现。

    工作流:
        1. SENSE（感知）: 通过 MCP 工具获取账户状态和市场数据
        2. THINK（思考）: 咨询蜂群获取交易信号
        3. DECIDE（决策）: 根据风险参数评估信号
        4. ACT（执行）: 通过 MCP 工具执行经验证的订单
    """

    # === 阶段 1：感知 ===
    # 使用 IBKR MCP 获取账户状态
    # 示例: account = mcp__ibkr__get_account()
    # 示例: positions = mcp__ibkr__get_positions()

    # 使用 ThetaData MCP 获取标的池的市场数据
    # 示例: quotes = mcp__ThetaData__stock_snapshot_quote(symbol=["AAPL", "NVDA"])
    # 示例: options = mcp__ThetaData__option_snapshot_quote(symbol="AAPL", expiration="20251128")

    # === 阶段 2：思考 ===
    # 咨询蜂群智能获取交易信号
    from skills import consult_swarm

    # 从 MCP 结果构建市场数据快照
    market_data = {
        "timestamp": datetime.now().isoformat(),
        "symbols": ["AAPL", "NVDA", "AMD"],
        "quotes": {},  # 从 ThetaData MCP 填充
        "options_chains": {},  # 从 ThetaData MCP 填充
        "account": {},  # 从 IBKR MCP 填充
        "positions": []  # 从 IBKR MCP 填充
    }

    signals = consult_swarm(sector="TECH", market_data=market_data)

    # === 阶段 3：决策 ===
    # 根据风险参数评估每个信号
    approved_trades = []

    for signal in signals:
        if signal["signal"] == "NO_TRADE":
            continue

        # 计算此信号的风险
        # 使用 kelly_criterion 和其他 math_core 函数
        from skills import kelly_criterion

        # 根据安全参数验证
        # - 单笔交易最大风险 $500
        # - 单笔交易最大资金 $2000
        # - 检查投资组合总 delta 敞口

        if meets_risk_criteria(signal):
            approved_trades.append(signal)

    # === 阶段 4：执行 ===
    # 通过 IBKR MCP 执行批准的交易
    from skills import place_order_with_guard

    for trade in approved_trades:
        result = place_order_with_guard(
            symbol=trade["target"],
            strategy=trade["signal"],
            legs=convert_signal_to_legs(trade),
            max_risk=calculate_max_risk(trade),
            capital_required=calculate_capital(trade),
            metadata={"signal_source": trade["instance_id"]}
        )

        if result.success:
            # 订单已通过 IBKR MCP 成功提交
            print(f"✅ 交易已执行: {trade['target']} {trade['signal']}")
        else:
            # 订单被安全层拒绝
            print(f"❌ 交易被拒绝: {result.error}")


def meets_risk_criteria(signal: Dict) -> bool:
    """
    根据风险参数验证信号。

    安全检查:
    - 单笔交易最大风险：$500
    - 单笔交易最大资金：$2000
    - 投资组合总 delta 敞口
    - 无重叠持仓
    """
    # 待办：实现完整的风险验证
    return True


def convert_signal_to_legs(signal: Dict) -> List[Dict]:
    """
    将蜂群信号转换为 IBKR 订单腿格式。

    示例:
        输入: {"signal": "SHORT_PUT_SPREAD", "params": {"strike_short": 175, ...}}
        输出: [
            {"action": "SELL", "contract": {...}, "quantity": 1},
            {"action": "BUY", "contract": {...}, "quantity": 1}
        ]
    """
    # 待办：实现信号到订单腿的转换
    return []


def calculate_max_risk(signal: Dict) -> float:
    """计算此笔交易的最大风险。"""
    # 待办：基于期权价差实现风险计算
    return 500.0


def calculate_capital(signal: Dict) -> float:
    """计算此笔交易所需资金。"""
    # 待办：实现资金计算
    return 2000.0


# === Claude Code 集成指南 ===
"""
当被 main_loop.py 调用时，Claude Code 应该：

1. **使用 MCP 工具读取市场数据**：
   ```python
   # 获取账户状态
   account = mcp__ibkr__get_account()
   positions = mcp__ibkr__get_positions()

   # 获取市场报价
   tech_quotes = mcp__ThetaData__stock_snapshot_quote(
       symbol=["AAPL", "NVDA", "AMD", "TSLA"]
   )

   # 获取高隐含波动率标的的期权数据
   for symbol in tech_quotes:
       if should_analyze_options(symbol):
           options = mcp__ThetaData__option_snapshot_quote(
               symbol=symbol,
               expiration="20251128"  # 目标 30-45 天到期
           )
   ```

2. **咨询蜂群智能**：
   ```python
   from skills import consult_swarm

   # 向蜂群传递真实的市场数据
   signals = consult_swarm(
       sector="TECH",
       market_data={
           "timestamp": datetime.now().isoformat(),
           "quotes": tech_quotes,
           "options": options_data,
           "account": account,
           "positions": positions
       }
   )
   ```

3. **评估信号**：
   ```python
   from skills import kelly_criterion, black_scholes_iv

   for signal in signals:
       # 使用 Kelly Criterion 计算仓位大小
       position_size = kelly_criterion(
           win_prob=signal["confidence"],
           win_amount=500,
           loss_amount=200,
           bankroll=account["buying_power"],
           fraction=0.25
       )

       # 验证隐含波动率计算
       iv = black_scholes_iv(...)

       # 检查安全限制
       if position_size > 2000:
           continue  # 拒绝 - 超过资金限制
   ```

4. **通过 MCP 执行订单**：
   ```python
   from skills import place_order_with_guard

   # place_order_with_guard 内部调用 IBKR MCP
   result = place_order_with_guard(
       symbol="NVDA",
       strategy="SHORT_PUT_SPREAD",
       legs=[
           {"action": "SELL", "strike": 120, "quantity": 1},
           {"action": "BUY", "strike": 115, "quantity": 1}
       ],
       max_risk=500,
       capital_required=2000
   )
   ```

5. **监控和日志**：
   - 所有决策自动记录到 data_lake/snapshots/
   - 所有交易记录到 data_lake/trades.db
   - Watchdog 通过心跳文件监控
"""
