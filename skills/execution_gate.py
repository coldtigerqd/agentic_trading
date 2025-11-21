"""
通过安全层执行经过验证的订单。

所有订单必须通过此模块。不允许绕过。
"""

import sys
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime

# 将 mcp-servers 添加到路径以导入 safety 模块
sys.path.append(str(Path(__file__).parent.parent / "mcp-servers" / "ibkr"))

from safety import SafetyValidator, create_safety_validator
from data_lake.db_helpers import log_trade, log_safety_event


@dataclass
class OrderResult:
    """订单执行尝试的结果"""
    success: bool
    trade_id: Optional[int] = None
    order_id: Optional[int] = None
    error: Optional[str] = None
    message: str = ""


# 全局安全验证器实例
_safety_validator: Optional[SafetyValidator] = None


def get_safety_validator() -> SafetyValidator:
    """获取或创建安全验证器实例"""
    global _safety_validator
    if _safety_validator is None:
        _safety_validator = create_safety_validator()
    return _safety_validator


def place_order_with_guard(
    symbol: str,
    strategy: str,
    legs: List[Dict],
    max_risk: float,
    capital_required: float,
    metadata: Optional[Dict] = None
) -> OrderResult:
    """
    通过安全验证下单

    安全层强制执行：
    - 所有订单都通过 SafetyValidator
    - 拒绝超出限制的订单
    - 记录所有尝试（批准 + 拒绝）
    - 不允许绕过

    Args:
        symbol: 标的代码（例如 "AAPL"）
        strategy: 策略名称（例如 "PUT_SPREAD", "IRON_CONDOR"）
        legs: 订单 leg 列表，结构如下：
            [
                {
                    "action": "SELL",
                    "strike": 180,
                    "expiry": "20251128",
                    "quantity": 1,
                    "price": 2.50,
                    "contract_type": "PUT"  # 或 "CALL"
                },
                ...
            ]
        max_risk: 此交易的最大风险（美元）
        capital_required: 需要部署的资金（美元）
        metadata: 可选上下文（推理、置信度、信号源等）

    Returns:
        OrderResult，包含状态、trade_id、order_id（如果成功）或错误信息

    Example:
        >>> result = place_order_with_guard(
        ...     symbol="AAPL",
        ...     strategy="PUT_SPREAD",
        ...     legs=[
        ...         {"action": "SELL", "strike": 180, "expiry": "20251128",
        ...          "quantity": 1, "price": 2.50, "contract_type": "PUT"},
        ...         {"action": "BUY", "strike": 175, "expiry": "20251128",
        ...          "quantity": 1, "price": 1.50, "contract_type": "PUT"}
        ...     ],
        ...     max_risk=100,
        ...     capital_required=500,
        ...     metadata={"confidence": 0.85, "signal_source": "tech_aggressive"}
        ... )
        >>> print(result.success)
        True
    """
    # 提取元数据字段
    if metadata is None:
        metadata = {}

    signal_source = metadata.get("signal_source")
    confidence = metadata.get("confidence")
    reasoning = metadata.get("reasoning")

    # 构建订单字典用于安全验证
    order_dict = {
        "symbol": symbol,
        "strategy": strategy,
        "legs": legs,
        "max_risk": max_risk,
        "capital_required": capital_required
    }

    # 关键：安全验证（不能绕过）
    safety_validator = get_safety_validator()
    is_valid, error_msg = safety_validator.validate_order(order_dict)

    if not is_valid:
        # 记录被拒绝的订单
        trade_id = log_trade(
            symbol=symbol,
            strategy=strategy,
            legs=legs,
            max_risk=max_risk,
            capital_required=capital_required,
            status="REJECTED",
            signal_source=signal_source,
            confidence=confidence,
            reasoning=reasoning,
            metadata=metadata
        )

        # 记录安全事件
        log_safety_event(
            event_type="ORDER_REJECTED",
            details={
                "trade_id": trade_id,
                "symbol": symbol,
                "strategy": strategy,
                "max_risk": max_risk,
                "capital_required": capital_required,
                "rejection_reason": error_msg
            },
            action_taken="order_blocked"
        )

        return OrderResult(
            success=False,
            trade_id=trade_id,
            error=error_msg,
            message=f"订单被安全层拒绝 (ORDER_REJECTED): {error_msg}"
        )

    # 订单通过安全验证
    # 在 IBKR 提交之前记录为 PENDING
    trade_id = log_trade(
        symbol=symbol,
        strategy=strategy,
        legs=legs,
        max_risk=max_risk,
        capital_required=capital_required,
        status="PENDING",
        signal_source=signal_source,
        confidence=confidence,
        reasoning=reasoning,
        metadata=metadata
    )

    # TODO: 在实际实现中，通过 MCP 提交到 IBKR
    # 目前，模拟成功提交
    # 生产环境：
    # try:
    #     ibkr_order = build_ibkr_order(symbol, legs, strategy)
    #     result = ibkr_mcp.place_order(
    #         symbol=symbol,
    #         strategy=strategy,
    #         legs=legs,
    #         max_risk=max_risk,
    #         capital_required=capital_required,
    #         metadata=metadata
    #     )
    #     order_id = result['order_id']
    #     update_trade_status(trade_id, 'SUBMITTED', order_id=order_id)
    # except Exception as e:
    #     update_trade_status(trade_id, 'FAILED')
    #     return OrderResult(success=False, trade_id=trade_id, error=str(e))

    return OrderResult(
        success=True,
        trade_id=trade_id,
        order_id=None,  # 生产环境中将是 IBKR order ID
        message=f"订单已验证并记录（trade_id={trade_id}）。等待 IBKR 提交。"
    )


def build_ibkr_order(
    symbol: str,
    legs: List[Dict],
    strategy: str
) -> Dict:
    """
    构建 IBKR 兼容的订单结构

    此函数将构建 IBKR API 所需的实际订单格式。
    目前，它返回一个占位符结构。

    Args:
        symbol: 标的代码
        legs: 订单 legs
        strategy: 策略名称

    Returns:
        IBKR 订单字典
    """
    # IBKR 订单构建的占位符
    # 在生产环境中，这将使用 ib_insync 构建适当的 Order 和 Contract 对象
    return {
        "symbol": symbol,
        "strategy": strategy,
        "legs": legs,
        "order_type": "LIMIT",
        "tif": "DAY"
    }


def validate_order_format(legs: List[Dict]) -> tuple[bool, Optional[str]]:
    """
    验证订单 leg 格式

    Args:
        legs: 要验证的订单 legs

    Returns:
        (is_valid, error_message)
    """
    if not legs:
        return False, "订单必须至少有一个 leg (INVALID_LEGS)"

    required_fields = ["action", "strike", "expiry", "quantity", "price", "contract_type"]

    for i, leg in enumerate(legs):
        for field in required_fields:
            if field not in leg:
                return False, f"Leg {i+1} 缺少必需字段 (MISSING_FIELD): {field}"

        # 验证 action
        if leg["action"] not in ["BUY", "SELL"]:
            return False, f"Leg {i+1} 的 action 无效 (INVALID_ACTION): {leg['action']}"

        # 验证 contract type
        if leg["contract_type"] not in ["CALL", "PUT"]:
            return False, f"Leg {i+1} 的 contract_type 无效 (INVALID_CONTRACT_TYPE): {leg['contract_type']}"

        # 验证数量为正数
        if leg["quantity"] <= 0:
            return False, f"Leg {i+1} 的数量无效 (INVALID_QUANTITY): {leg['quantity']}"

        # 验证价格为正数
        if leg["price"] < 0:
            return False, f"Leg {i+1} 的价格无效 (INVALID_PRICE): {leg['price']}"

    return True, None
