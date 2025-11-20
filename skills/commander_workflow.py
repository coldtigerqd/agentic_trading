"""
Commander Workflow - Integration example for Claude Code.

This module demonstrates how Claude Code (the Commander) should use
MCP tools and skills library together to execute trading cycles.

IMPORTANT: This is meant to be executed BY Claude Code, not as a standalone script.
The functions here show the expected workflow when Claude is invoked by main_loop.py.
"""

from typing import Dict, List, Any
from datetime import datetime


def commander_workflow_example():
    """
    Example workflow showing how Commander (Claude Code) should integrate
    MCP tools and skills library.

    This is a REFERENCE IMPLEMENTATION for Claude Code to follow.

    Workflow:
        1. SENSE: Get account state and market data via MCP tools
        2. THINK: Consult swarm for trading signals
        3. DECIDE: Evaluate signals against risk parameters
        4. ACT: Execute validated orders via MCP tools
    """

    # === PHASE 1: SENSE ===
    # Use IBKR MCP to get account state
    # Example: account = mcp__ibkr__get_account()
    # Example: positions = mcp__ibkr__get_positions()

    # Use ThetaData MCP to get market data for symbol pool
    # Example: quotes = mcp__ThetaData__stock_snapshot_quote(symbol=["AAPL", "NVDA"])
    # Example: options = mcp__ThetaData__option_snapshot_quote(symbol="AAPL", expiration="20251128")

    # === PHASE 2: THINK ===
    # Consult swarm intelligence for trading signals
    from skills import consult_swarm

    # Build market data snapshot from MCP results
    market_data = {
        "timestamp": datetime.now().isoformat(),
        "symbols": ["AAPL", "NVDA", "AMD"],
        "quotes": {},  # Fill from ThetaData MCP
        "options_chains": {},  # Fill from ThetaData MCP
        "account": {},  # Fill from IBKR MCP
        "positions": []  # Fill from IBKR MCP
    }

    signals = consult_swarm(sector="TECH", market_data=market_data)

    # === PHASE 3: DECIDE ===
    # Evaluate each signal against risk parameters
    approved_trades = []

    for signal in signals:
        if signal["signal"] == "NO_TRADE":
            continue

        # Calculate risk for this signal
        # Use kelly_criterion and other math_core functions
        from skills import kelly_criterion

        # Validate against safety parameters
        # - Max $500 risk per trade
        # - Max $2000 capital per trade
        # - Check total portfolio delta exposure

        if meets_risk_criteria(signal):
            approved_trades.append(signal)

    # === PHASE 4: ACT ===
    # Execute approved trades via IBKR MCP
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
            # Order submitted successfully via IBKR MCP
            print(f"✅ Trade executed: {trade['target']} {trade['signal']}")
        else:
            # Order rejected by safety layer
            print(f"❌ Trade rejected: {result.error}")


def meets_risk_criteria(signal: Dict) -> bool:
    """
    Validate signal against risk parameters.

    Safety checks:
    - Max risk per trade: $500
    - Max capital per trade: $2000
    - Total portfolio delta exposure
    - No overlapping positions
    """
    # TODO: Implement full risk validation
    return True


def convert_signal_to_legs(signal: Dict) -> List[Dict]:
    """
    Convert swarm signal to IBKR order legs format.

    Example:
        Input: {"signal": "SHORT_PUT_SPREAD", "params": {"strike_short": 175, ...}}
        Output: [
            {"action": "SELL", "contract": {...}, "quantity": 1},
            {"action": "BUY", "contract": {...}, "quantity": 1}
        ]
    """
    # TODO: Implement signal-to-legs conversion
    return []


def calculate_max_risk(signal: Dict) -> float:
    """Calculate maximum risk for this trade."""
    # TODO: Implement risk calculation based on option spreads
    return 500.0


def calculate_capital(signal: Dict) -> float:
    """Calculate capital required for this trade."""
    # TODO: Implement capital calculation
    return 2000.0


# === INTEGRATION GUIDE FOR CLAUDE CODE ===
"""
When invoked by main_loop.py, Claude Code should:

1. **Read market data using MCP tools**:
   ```python
   # Get account status
   account = mcp__ibkr__get_account()
   positions = mcp__ibkr__get_positions()

   # Get market quotes
   tech_quotes = mcp__ThetaData__stock_snapshot_quote(
       symbol=["AAPL", "NVDA", "AMD", "TSLA"]
   )

   # Get options data for symbols with high IV
   for symbol in tech_quotes:
       if should_analyze_options(symbol):
           options = mcp__ThetaData__option_snapshot_quote(
               symbol=symbol,
               expiration="20251128"  # 30-45 DTE target
           )
   ```

2. **Consult swarm intelligence**:
   ```python
   from skills import consult_swarm

   # Pass real market data to swarm
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

3. **Evaluate signals**:
   ```python
   from skills import kelly_criterion, black_scholes_iv

   for signal in signals:
       # Calculate position size using Kelly Criterion
       position_size = kelly_criterion(
           win_prob=signal["confidence"],
           win_amount=500,
           loss_amount=200,
           bankroll=account["buying_power"],
           fraction=0.25
       )

       # Validate IV calculations
       iv = black_scholes_iv(...)

       # Check against safety limits
       if position_size > 2000:
           continue  # Reject - exceeds capital limit
   ```

4. **Execute orders via MCP**:
   ```python
   from skills import place_order_with_guard

   # place_order_with_guard internally calls IBKR MCP
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

5. **Monitor and log**:
   - All decisions are automatically logged to data_lake/snapshots/
   - All trades are logged to data_lake/trades.db
   - Watchdog monitors via heartbeat file
"""
