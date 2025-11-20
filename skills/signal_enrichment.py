"""
Signal Enrichment - Post-processor for swarm signals.

Converts simplified signals (just strikes) into fully executable orders
with legs, pricing, and risk calculations.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime


def enrich_signal(signal: Dict[str, Any], market_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enrich a swarm signal with executable order details.

    If the signal already has complete 'legs', return as-is.
    Otherwise, convert strikes into full leg structures.
    Also adds missing prices to existing legs.

    Args:
        signal: Raw signal from swarm
        market_data: Market data for pricing

    Returns:
        Enriched signal with complete params.legs
    """
    params = signal.get("params", {})
    target = signal.get("target", "")

    # If legs already exist, check if they need price enrichment
    if "legs" in params and params["legs"]:
        legs = params["legs"]
        needs_pricing = any("price" not in leg for leg in legs)

        if needs_pricing and target:
            # Add prices to existing legs
            quote = market_data.get("quotes", {}).get(target, {})
            underlying_price = quote.get("last", 0)

            if underlying_price:
                for leg in legs:
                    if "price" not in leg:
                        # Estimate price based on strike and underlying
                        contract = leg.get("contract", {})
                        strike = contract.get("strike", 0)
                        right = contract.get("right", "P")

                        if strike:
                            moneyness = strike / underlying_price
                            if right == "P":
                                # Put pricing
                                leg["price"] = round(max(0.5, (1 - moneyness) * underlying_price * 0.05), 2)
                            else:
                                # Call pricing
                                leg["price"] = round(max(0.5, (moneyness - 1) * underlying_price * 0.05), 2)

        return signal

    # Otherwise, convert strikes to legs
    strategy = signal.get("signal", "")
    target = signal.get("target", "")

    if strategy == "NO_TRADE" or not target:
        return signal

    # Dispatch to strategy-specific enrichment
    if strategy == "SHORT_PUT_SPREAD":
        return enrich_short_put_spread(signal, market_data)
    elif strategy == "SHORT_CALL_SPREAD":
        return enrich_short_call_spread(signal, market_data)
    elif strategy == "IRON_CONDOR":
        return enrich_iron_condor(signal, market_data)
    else:
        # Unknown strategy, return as-is
        return signal


def enrich_short_put_spread(signal: Dict[str, Any], market_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enrich SHORT_PUT_SPREAD signal with legs.

    Args:
        signal: Signal with strike_short, strike_long, expiry
        market_data: Market data for pricing

    Returns:
        Signal with params.legs added
    """
    params = signal["params"]
    target = signal["target"]

    strike_short = params.get("strike_short")
    strike_long = params.get("strike_long")
    expiry_compact = params.get("expiry")  # Format: YYYYMMDD

    if not all([strike_short, strike_long, expiry_compact]):
        # Missing required fields
        return signal

    # Convert expiry format: YYYYMMDD -> YYYY-MM-DD
    expiry = f"{expiry_compact[:4]}-{expiry_compact[4:6]}-{expiry_compact[6:8]}"

    # Estimate option prices (simplified - would use real market data in production)
    quote = market_data.get("quotes", {}).get(target, {})
    underlying_price = quote.get("last", 0)

    if not underlying_price:
        # Can't price without underlying
        return signal

    # Rough option pricing based on moneyness
    # This is a placeholder - in production, use real option chain data
    short_moneyness = strike_short / underlying_price
    long_moneyness = strike_long / underlying_price

    # Estimate premiums (very rough approximation)
    # OTM puts: higher strike = higher premium
    short_price = max(1.0, (1 - short_moneyness) * underlying_price * 0.05)
    long_price = max(0.5, (1 - long_moneyness) * underlying_price * 0.04)

    # Create legs
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

    # Calculate risk
    net_credit = (short_price - long_price) * 100
    max_risk = ((strike_short - strike_long) * 100) - net_credit
    capital_required = max_risk * 1.2  # Add 20% buffer

    # Update params
    params["legs"] = legs
    params["max_risk"] = int(max_risk)
    params["capital_required"] = int(capital_required)

    return signal


def enrich_short_call_spread(signal: Dict[str, Any], market_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enrich SHORT_CALL_SPREAD signal with legs.

    Args:
        signal: Signal with call_strike_short, call_strike_long, expiry
        market_data: Market data for pricing

    Returns:
        Signal with params.legs added
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

    # Estimate call premiums
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
    Enrich IRON_CONDOR signal with legs.

    Args:
        signal: Signal with put and call strikes
        market_data: Market data for pricing

    Returns:
        Signal with params.legs added (4 legs total)
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

    # Estimate prices for all 4 legs
    put_short_price = max(1.0, (1 - put_strike_short / underlying_price) * underlying_price * 0.05)
    put_long_price = max(0.5, (1 - put_strike_long / underlying_price) * underlying_price * 0.04)
    call_short_price = max(1.0, (call_strike_short / underlying_price - 1) * underlying_price * 0.05)
    call_long_price = max(0.5, (call_strike_long / underlying_price - 1) * underlying_price * 0.04)

    legs = [
        # Put spread
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
        # Call spread
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
    Validate that an enriched signal has all required fields.

    Args:
        signal: Enriched signal

    Returns:
        True if valid, False otherwise
    """
    if signal.get("signal") == "NO_TRADE":
        return True

    params = signal.get("params", {})
    legs = params.get("legs", [])

    if not legs:
        return False

    # Check all legs have required fields
    for leg in legs:
        if not all(k in leg for k in ["action", "contract", "quantity", "price"]):
            return False

        contract = leg["contract"]
        if not all(k in contract for k in ["symbol", "expiry", "strike", "right"]):
            return False

    # Check risk calculations exist
    if "max_risk" not in params or "capital_required" not in params:
        return False

    return True
