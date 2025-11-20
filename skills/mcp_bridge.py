"""
MCP Bridge - Helper functions for Claude Code to integrate MCP tools with skills.

IMPORTANT: These functions are designed to be called BY Claude Code during
the Commander workflow. They bridge the gap between Python skills library
and MCP tools that are only accessible to Claude Code.
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
    Execute a validated order via IBKR MCP.

    This function should be called by Claude Code AFTER place_order_with_guard()
    has validated the order.

    Workflow:
        1. Python: place_order_with_guard() validates and logs order
        2. Claude: Calls this function to execute via IBKR MCP
        3. Python: Updates trade status in database

    Args:
        validated_order: Result from place_order_with_guard()
        legs: Order legs in IBKR format
        symbol: Underlying symbol
        strategy: Strategy name
        max_risk: Maximum risk ($)
        capital_required: Capital required ($)
        metadata: Additional metadata

    Returns:
        OrderResult with IBKR order_id if successful

    Example:
        ```python
        # Step 1: Validate order
        from skills import place_order_with_guard
        result = place_order_with_guard(...)

        # Step 2: If validation passed, execute via IBKR
        if result.success:
            from skills.mcp_bridge import execute_order_with_ibkr

            # Claude Code calls IBKR MCP tool
            ibkr_result = mcp__ibkr__place_order(
                symbol=symbol,
                strategy=strategy,
                legs=legs,
                max_risk=max_risk,
                capital_required=capital_required,
                metadata=metadata
            )

            # Update trade status with IBKR order ID
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

    # Extract IBKR order ID from metadata
    # Claude should have called mcp__ibkr__place_order() and passed result here
    ibkr_order_id = None
    if metadata and "ibkr_result" in metadata:
        ibkr_result = metadata["ibkr_result"]
        ibkr_order_id = ibkr_result.get("order_id")

    if ibkr_order_id:
        # Update trade status to SUBMITTED with IBKR order ID
        update_trade_status(
            trade_id=validated_order.trade_id,
            status="SUBMITTED",
            order_id=ibkr_order_id
        )

        return OrderResult(
            success=True,
            trade_id=validated_order.trade_id,
            order_id=ibkr_order_id,
            message=f"Order submitted to IBKR successfully (order_id={ibkr_order_id})"
        )
    else:
        # IBKR submission failed or no order ID returned
        update_trade_status(
            trade_id=validated_order.trade_id,
            status="FAILED"
        )

        return OrderResult(
            success=False,
            trade_id=validated_order.trade_id,
            error="Failed to submit order to IBKR",
            message="IBKR MCP did not return order_id"
        )


def fetch_market_data_for_symbols(symbols: List[str]) -> Dict[str, Any]:
    """
    Fetch market data for given symbols via ThetaData MCP.

    This is a helper that Claude Code should use to build market_data
    dictionaries for consult_swarm().

    Args:
        symbols: List of stock symbols

    Returns:
        Market data dictionary suitable for consult_swarm()

    Example:
        ```python
        # Claude Code fetches market data
        symbols = ["AAPL", "NVDA", "AMD", "TSLA"]

        # Get stock quotes via ThetaData MCP
        quotes = mcp__ThetaData__stock_snapshot_quote(symbol=symbols)

        # Get options data for high IV symbols
        options_data = {}
        for symbol in symbols:
            options = mcp__ThetaData__option_list_expirations(symbol=[symbol])
            # Filter for 30-45 DTE expiration
            target_expiry = find_target_expiration(options, dte_range=(30, 45))

            options_chain = mcp__ThetaData__option_snapshot_quote(
                symbol=symbol,
                expiration=target_expiry
            )
            options_data[symbol] = options_chain

        # Build market snapshot
        market_data = fetch_market_data_for_symbols(symbols)
        market_data["quotes"] = quotes
        market_data["options_chains"] = options_data

        # Now pass to swarm
        from skills import consult_swarm
        signals = consult_swarm(sector="TECH", market_data=market_data)
        ```
    """
    from datetime import datetime

    return {
        "timestamp": datetime.now().isoformat(),
        "symbols": symbols,
        "quotes": {},  # Claude should fill from mcp__ThetaData__stock_snapshot_quote()
        "options_chains": {},  # Claude should fill from mcp__ThetaData__option_snapshot_quote()
        "account": {},  # Claude should fill from mcp__ibkr__get_account()
        "positions": []  # Claude should fill from mcp__ibkr__get_positions()
    }


def find_target_expiration(expirations: List[str], dte_range: tuple = (30, 45)) -> Optional[str]:
    """
    Find the best expiration date within target DTE range.

    Args:
        expirations: List of expiration dates in YYYYMMDD format
        dte_range: Tuple of (min_dte, max_dte)

    Returns:
        Expiration date string or None
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

    # Return the expiration closest to middle of range
    target_dte = (min_dte + max_dte) // 2
    best_exp = min(target_expirations, key=lambda x: abs(x[0] - target_dte))
    return best_exp[1]


# === USAGE GUIDE FOR CLAUDE CODE ===
"""
When Claude Code acts as Commander, use this pattern:

```python
# === SENSE Phase ===
# Get account and positions via IBKR MCP
account = mcp__ibkr__get_account()
positions = mcp__ibkr__get_positions()

# Get market data via ThetaData MCP
symbols = ["AAPL", "NVDA", "AMD", "TSLA"]
quotes = mcp__ThetaData__stock_snapshot_quote(symbol=symbols)

# Get options data
from skills.mcp_bridge import find_target_expiration
expirations = mcp__ThetaData__option_list_expirations(symbol=["NVDA"])
target_exp = find_target_expiration(expirations["NVDA"], dte_range=(30, 45))

options = mcp__ThetaData__option_snapshot_quote(
    symbol="NVDA",
    expiration=target_exp
)

# === THINK Phase ===
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

# === DECIDE Phase ===
from skills import kelly_criterion

approved_trades = []
for signal in signals:
    if signal["signal"] == "NO_TRADE":
        continue

    # Calculate position size
    position_size = kelly_criterion(
        win_prob=signal["confidence"],
        win_amount=500,
        loss_amount=200,
        bankroll=account["net_liquidation"],
        fraction=0.25
    )

    # Apply safety limits
    if position_size <= 2000 and signal["params"]["max_risk"] <= 500:
        approved_trades.append(signal)

# === ACT Phase ===
from skills import place_order_with_guard
from skills.mcp_bridge import execute_order_with_ibkr

for trade in approved_trades:
    # Step 1: Validate with safety layer
    result = place_order_with_guard(
        symbol=trade["target"],
        strategy=trade["signal"],
        legs=trade["params"]["legs"],
        max_risk=trade["params"]["max_risk"],
        capital_required=trade["params"]["capital_required"],
        metadata={"signal_source": trade["instance_id"]}
    )

    if not result.success:
        print(f"❌ Trade rejected: {result.error}")
        continue

    # Step 2: Submit to IBKR via MCP
    try:
        ibkr_result = mcp__ibkr__place_order(
            symbol=trade["target"],
            strategy=trade["signal"],
            legs=trade["params"]["legs"],
            max_risk=trade["params"]["max_risk"],
            capital_required=trade["params"]["capital_required"]
        )

        # Step 3: Update trade status
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
            print(f"✅ Trade executed: {trade['target']} (order_id={final_result.order_id})")
        else:
            print(f"❌ IBKR submission failed: {final_result.error}")

    except Exception as e:
        print(f"❌ Error submitting to IBKR: {e}")
        update_trade_status(result.trade_id, "FAILED")
```
"""
