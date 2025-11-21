"""
信号增强 - Swarm 信号的后处理器。

将简化的信号（仅包含执行价格）转换为完全可执行的订单，
包含期权腿、定价和风险计算。
"""

from typing import Dict, List, Optional, Any
from datetime import datetime


def enrich_signal(signal: Dict[str, Any], market_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    使用可执行订单详情增强 swarm 信号。

    如果信号已经包含完整的 'legs'，则直接返回。
    否则，将执行价格转换为完整的期权腿结构。
    同时为现有期权腿添加缺失的价格。

    Args:
        signal: 来自 swarm 的原始信号
        market_data: 用于定价的市场数据

    Returns:
        包含完整 params.legs 的增强信号
    """
    params = signal.get("params", {})
    target = signal.get("target", "")

    # 如果期权腿已存在，检查是否需要价格增强
    if "legs" in params and params["legs"]:
        legs = params["legs"]
        needs_pricing = any("price" not in leg for leg in legs)

        if needs_pricing and target:
            # 为现有期权腿添加价格
            quote = market_data.get("quotes", {}).get(target, {})
            underlying_price = quote.get("last", 0)

            if underlying_price:
                for leg in legs:
                    if "price" not in leg:
                        # 根据 strike 和标的资产估算价格
                        contract = leg.get("contract", {})
                        strike = contract.get("strike", 0)
                        right = contract.get("right", "P")

                        if strike:
                            moneyness = strike / underlying_price
                            if right == "P":
                                # PUT 定价
                                leg["price"] = round(max(0.5, (1 - moneyness) * underlying_price * 0.05), 2)
                            else:
                                # CALL 定价
                                leg["price"] = round(max(0.5, (moneyness - 1) * underlying_price * 0.05), 2)

        return signal

    # 否则，将执行价格转换为期权腿
    strategy = signal.get("signal", "")
    target = signal.get("target", "")

    if strategy == "NO_TRADE" or not target:
        return signal

    # 分派到策略特定的增强函数
    if strategy == "SHORT_PUT_SPREAD":
        return enrich_short_put_spread(signal, market_data)
    elif strategy == "SHORT_CALL_SPREAD":
        return enrich_short_call_spread(signal, market_data)
    elif strategy == "IRON_CONDOR":
        return enrich_iron_condor(signal, market_data)
    else:
        # 未知策略，直接返回
        return signal


def enrich_short_put_spread(signal: Dict[str, Any], market_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    为 SHORT_PUT_SPREAD 信号增强期权腿。

    Args:
        signal: 包含 strike_short, strike_long, expiry 的信号
        market_data: 用于定价的市场数据

    Returns:
        添加了 params.legs 的信号
    """
    params = signal["params"]
    target = signal["target"]

    strike_short = params.get("strike_short")
    strike_long = params.get("strike_long")
    expiry_compact = params.get("expiry")  # 格式: YYYYMMDD

    if not all([strike_short, strike_long, expiry_compact]):
        # 缺少必需字段
        return signal

    # 转换到期日格式: YYYYMMDD -> YYYY-MM-DD
    expiry = f"{expiry_compact[:4]}-{expiry_compact[4:6]}-{expiry_compact[6:8]}"

    # 估算期权价格（简化版 - 生产环境应使用真实市场数据）
    quote = market_data.get("quotes", {}).get(target, {})
    underlying_price = quote.get("last", 0)

    if not underlying_price:
        # 没有标的资产价格无法定价
        return signal

    # 基于价值度的粗略期权定价
    # 这是占位符 - 生产环境应使用真实期权链数据
    short_moneyness = strike_short / underlying_price
    long_moneyness = strike_long / underlying_price

    # 估算权利金（非常粗略的近似）
    # OTM PUT: 更高的 strike = 更高的权利金
    short_price = max(1.0, (1 - short_moneyness) * underlying_price * 0.05)
    long_price = max(0.5, (1 - long_moneyness) * underlying_price * 0.04)

    # 创建期权腿
    legs = [
        {
            "action": "SELL",
            "contract": {
                "symbol": target,
                "expiry": expiry,
                "strike": int(strike_short),
                "right": "P"
            },
            "quantity": 1,
            "price": round(short_price, 2)
        },
        {
            "action": "BUY",
            "contract": {
                "symbol": target,
                "expiry": expiry,
                "strike": int(strike_long),
                "right": "P"
            },
            "quantity": 1,
            "price": round(long_price, 2)
        }
    ]

    # 计算风险
    net_credit = (short_price - long_price) * 100
    max_risk = ((strike_short - strike_long) * 100) - net_credit
    capital_required = max_risk * 1.2  # 增加 20% 缓冲

    # 更新参数
    params["legs"] = legs
    params["max_risk"] = int(max_risk)
    params["capital_required"] = int(capital_required)

    return signal


def enrich_short_call_spread(signal: Dict[str, Any], market_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    为 SHORT_CALL_SPREAD 信号增强期权腿。

    Args:
        signal: 包含 call_strike_short, call_strike_long, expiry 的信号
        market_data: 用于定价的市场数据

    Returns:
        添加了 params.legs 的信号
    """
    params = signal["params"]
    target = signal["target"]

    strike_short = params.get("call_strike_short")
    strike_long = params.get("call_strike_long")
    expiry_compact = params.get("expiry")

    if not all([strike_short, strike_long, expiry_compact]):
        return signal

    expiry = f"{expiry_compact[:4]}-{expiry_compact[4:6]}-{expiry_compact[6:8]}"

    quote = market_data.get("quotes", {}).get(target, {})
    underlying_price = quote.get("last", 0)

    if not underlying_price:
        return signal

    # 估算 CALL 权利金
    short_moneyness = strike_short / underlying_price
    long_moneyness = strike_long / underlying_price

    short_price = max(1.0, (short_moneyness - 1) * underlying_price * 0.05)
    long_price = max(0.5, (long_moneyness - 1) * underlying_price * 0.04)

    legs = [
        {
            "action": "SELL",
            "contract": {
                "symbol": target,
                "expiry": expiry,
                "strike": int(strike_short),
                "right": "C"
            },
            "quantity": 1,
            "price": round(short_price, 2)
        },
        {
            "action": "BUY",
            "contract": {
                "symbol": target,
                "expiry": expiry,
                "strike": int(strike_long),
                "right": "C"
            },
            "quantity": 1,
            "price": round(long_price, 2)
        }
    ]

    net_credit = (short_price - long_price) * 100
    max_risk = ((strike_long - strike_short) * 100) - net_credit
    capital_required = max_risk * 1.2

    params["legs"] = legs
    params["max_risk"] = int(max_risk)
    params["capital_required"] = int(capital_required)

    return signal


def enrich_iron_condor(signal: Dict[str, Any], market_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    为 IRON_CONDOR 信号增强期权腿。

    Args:
        signal: 包含 PUT 和 CALL strike 的信号
        market_data: 用于定价的市场数据

    Returns:
        添加了 params.legs 的信号（共 4 条腿）
    """
    params = signal["params"]
    target = signal["target"]

    put_strike_short = params.get("strike_short")
    put_strike_long = params.get("strike_long")
    call_strike_short = params.get("call_strike_short")
    call_strike_long = params.get("call_strike_long")
    expiry_compact = params.get("expiry")

    if not all([put_strike_short, put_strike_long, call_strike_short, call_strike_long, expiry_compact]):
        return signal

    expiry = f"{expiry_compact[:4]}-{expiry_compact[4:6]}-{expiry_compact[6:8]}"

    quote = market_data.get("quotes", {}).get(target, {})
    underlying_price = quote.get("last", 0)

    if not underlying_price:
        return signal

    # 估算所有 4 条腿的价格
    put_short_price = max(1.0, (1 - put_strike_short / underlying_price) * underlying_price * 0.05)
    put_long_price = max(0.5, (1 - put_strike_long / underlying_price) * underlying_price * 0.04)
    call_short_price = max(1.0, (call_strike_short / underlying_price - 1) * underlying_price * 0.05)
    call_long_price = max(0.5, (call_strike_long / underlying_price - 1) * underlying_price * 0.04)

    legs = [
        # PUT SPREAD
        {
            "action": "SELL",
            "contract": {"symbol": target, "expiry": expiry, "strike": int(put_strike_short), "right": "P"},
            "quantity": 1,
            "price": round(put_short_price, 2)
        },
        {
            "action": "BUY",
            "contract": {"symbol": target, "expiry": expiry, "strike": int(put_strike_long), "right": "P"},
            "quantity": 1,
            "price": round(put_long_price, 2)
        },
        # CALL SPREAD
        {
            "action": "SELL",
            "contract": {"symbol": target, "expiry": expiry, "strike": int(call_strike_short), "right": "C"},
            "quantity": 1,
            "price": round(call_short_price, 2)
        },
        {
            "action": "BUY",
            "contract": {"symbol": target, "expiry": expiry, "strike": int(call_strike_long), "right": "C"},
            "quantity": 1,
            "price": round(call_long_price, 2)
        }
    ]

    put_net_credit = (put_short_price - put_long_price) * 100
    call_net_credit = (call_short_price - call_long_price) * 100
    total_credit = put_net_credit + call_net_credit

    put_max_risk = ((put_strike_short - put_strike_long) * 100) - put_net_credit
    call_max_risk = ((call_strike_long - call_strike_short) * 100) - call_net_credit
    max_risk = max(put_max_risk, call_max_risk)
    capital_required = max_risk * 1.2

    params["legs"] = legs
    params["max_risk"] = int(max_risk)
    params["capital_required"] = int(capital_required)

    return signal


def validate_enriched_signal(signal: Dict[str, Any]) -> bool:
    """
    验证增强后的信号是否包含所有必需字段。

    Args:
        signal: 增强后的信号

    Returns:
        如果有效返回 True，否则返回 False
    """
    if signal.get("signal") == "NO_TRADE":
        return True

    params = signal.get("params", {})
    legs = params.get("legs", [])

    if not legs:
        return False

    # 检查所有期权腿是否包含必需字段
    for leg in legs:
        if not all(k in leg for k in ["action", "contract", "quantity", "price"]):
            return False

        contract = leg["contract"]
        if not all(k in contract for k in ["symbol", "expiry", "strike", "right"]):
            return False

    # 检查风险计算是否存在
    if "max_risk" not in params or "capital_required" not in params:
        return False

    return True
