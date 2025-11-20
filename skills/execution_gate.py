"""
Validated order execution through safety layer.

All orders MUST pass through this module. No bypasses allowed.
"""

import sys
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime

# Add mcp-servers to path to import safety module
sys.path.append(str(Path(__file__).parent.parent / "mcp-servers" / "ibkr"))

from safety import SafetyValidator, create_safety_validator
from data_lake.db_helpers import log_trade, log_safety_event


@dataclass
class OrderResult:
    """Result of order execution attempt."""
    success: bool
    trade_id: Optional[int] = None
    order_id: Optional[int] = None
    error: Optional[str] = None
    message: str = ""


# Global safety validator instance
_safety_validator: Optional[SafetyValidator] = None


def get_safety_validator() -> SafetyValidator:
    """Get or create safety validator instance."""
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
    Place order with safety validation.

    SAFETY LAYER ENFORCEMENT:
    - All orders pass through SafetyValidator
    - Rejects orders exceeding limits
    - Logs all attempts (approved + rejected)
    - No bypasses allowed

    Args:
        symbol: Underlying ticker (e.g., "AAPL")
        strategy: Strategy name (e.g., "PUT_SPREAD", "IRON_CONDOR")
        legs: List of order legs with structure:
            [
                {
                    "action": "SELL",
                    "strike": 180,
                    "expiry": "20251128",
                    "quantity": 1,
                    "price": 2.50,
                    "contract_type": "PUT"  # or "CALL"
                },
                ...
            ]
        max_risk: Maximum risk for this trade ($)
        capital_required: Capital to deploy ($)
        metadata: Optional context (reasoning, confidence, signal_source, etc.)

    Returns:
        OrderResult with status, trade_id, order_id (if successful), or error

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
    # Extract metadata fields
    if metadata is None:
        metadata = {}

    signal_source = metadata.get("signal_source")
    confidence = metadata.get("confidence")
    reasoning = metadata.get("reasoning")

    # Construct order dict for safety validation
    order_dict = {
        "symbol": symbol,
        "strategy": strategy,
        "legs": legs,
        "max_risk": max_risk,
        "capital_required": capital_required
    }

    # CRITICAL: Safety validation (CANNOT BE BYPASSED)
    safety_validator = get_safety_validator()
    is_valid, error_msg = safety_validator.validate_order(order_dict)

    if not is_valid:
        # Log rejected order
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

        # Log safety event
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
            message=f"Order rejected by safety layer: {error_msg}"
        )

    # Order passed safety validation
    # Log as PENDING before IBKR submission
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

    # TODO: In actual implementation, submit to IBKR via MCP
    # For now, simulate successful submission
    # In production:
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
        order_id=None,  # Would be IBKR order ID in production
        message=f"Order validated and logged (trade_id={trade_id}). IBKR submission pending."
    )


def build_ibkr_order(
    symbol: str,
    legs: List[Dict],
    strategy: str
) -> Dict:
    """
    Build IBKR-compatible order structure.

    This function would construct the actual order format required by IBKR API.
    For now, it returns a placeholder structure.

    Args:
        symbol: Underlying symbol
        legs: Order legs
        strategy: Strategy name

    Returns:
        IBKR order dictionary
    """
    # Placeholder for IBKR order construction
    # In production, this would use ib_insync to build proper Order and Contract objects
    return {
        "symbol": symbol,
        "strategy": strategy,
        "legs": legs,
        "order_type": "LIMIT",
        "tif": "DAY"
    }


def validate_order_format(legs: List[Dict]) -> tuple[bool, Optional[str]]:
    """
    Validate order leg format.

    Args:
        legs: Order legs to validate

    Returns:
        (is_valid, error_message)
    """
    if not legs:
        return False, "Order must have at least one leg"

    required_fields = ["action", "strike", "expiry", "quantity", "price", "contract_type"]

    for i, leg in enumerate(legs):
        for field in required_fields:
            if field not in leg:
                return False, f"Leg {i+1} missing required field: {field}"

        # Validate action
        if leg["action"] not in ["BUY", "SELL"]:
            return False, f"Leg {i+1} has invalid action: {leg['action']}"

        # Validate contract type
        if leg["contract_type"] not in ["CALL", "PUT"]:
            return False, f"Leg {i+1} has invalid contract_type: {leg['contract_type']}"

        # Validate quantities are positive
        if leg["quantity"] <= 0:
            return False, f"Leg {i+1} has invalid quantity: {leg['quantity']}"

        # Validate prices are positive
        if leg["price"] < 0:
            return False, f"Leg {i+1} has invalid price: {leg['price']}"

    return True, None
