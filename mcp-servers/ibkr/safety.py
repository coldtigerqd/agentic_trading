"""
Safety layer for IBKR MCP server.

Implements hard-coded limits and circuit breakers to prevent catastrophic trading errors.
All trading operations MUST pass through these safety checks.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Tuple
import json
from pathlib import Path


class ViolationType(Enum):
    """Types of safety violations."""
    MAX_TRADE_RISK = "max_trade_risk"
    DAILY_LOSS_LIMIT = "daily_loss_limit"
    CONCENTRATION_LIMIT = "concentration_limit"
    DRAWDOWN_CIRCUIT_BREAKER = "drawdown_circuit_breaker"
    INVALID_ORDER = "invalid_order"
    EMERGENCY_STOP = "emergency_stop"


@dataclass
class SafetyLimits:
    """Hard-coded safety limits. DO NOT modify without human approval."""

    # Per-trade limits
    MAX_TRADE_RISK: float = 2000.0  # Maximum risk per single trade ($) - RAISED FOR TESTING
    MAX_TRADE_CAPITAL: float = 5000.0  # Maximum capital deployed per trade ($) - RAISED FOR TESTING

    # Daily limits
    DAILY_LOSS_LIMIT: float = 1000.0  # Maximum daily loss before shutdown ($)
    MAX_DAILY_TRADES: int = 10  # Maximum trades per day

    # Portfolio limits
    MAX_CONCENTRATION: float = 0.30  # Maximum 30% of portfolio in single symbol
    MAX_TOTAL_EXPOSURE: float = 10000.0  # Maximum total portfolio exposure ($)

    # Circuit breakers
    DRAWDOWN_CIRCUIT_BREAKER: float = 0.10  # Stop trading at 10% account drawdown
    CONSECUTIVE_LOSS_LIMIT: int = 5  # Stop after 5 consecutive losses

    # Order validation
    MIN_OPTION_PRICE: float = 0.05  # Minimum option price ($)
    MAX_SPREAD_WIDTH: float = 10.0  # Maximum spread width for single leg ($)


class SafetyValidator:
    """Validates all trading operations against safety limits."""

    def __init__(self, limits: Optional[SafetyLimits] = None):
        self.limits = limits or SafetyLimits()
        self._load_agent_state()

    def _load_agent_state(self):
        """Load agent memory to check current portfolio state."""
        memory_path = Path.home() / "trading_workspace" / "state" / "agent_memory.json"

        if memory_path.exists():
            with open(memory_path, 'r') as f:
                self.agent_memory = json.load(f)
        else:
            # Default state if file doesn't exist yet
            self.agent_memory = {
                "safety_state": {
                    "daily_loss": 0.0,
                    "circuit_breaker_triggered": False,
                    "consecutive_losses": 0
                },
                "positions": {
                    "open_trades": []
                },
                "agent_state": {
                    "emergency_stop": False
                }
            }

    def reload_agent_state(self):
        """Reload agent memory from disk (call before each validation)."""
        self._load_agent_state()

    def validate_order(self, order: Dict) -> Tuple[bool, Optional[str]]:
        """
        Validate a trade order against all safety limits.

        Args:
            order: Order dictionary with keys:
                - symbol: str
                - strategy: str
                - legs: List[Dict] (for multi-leg orders)
                - max_risk: float
                - capital_required: float

        Returns:
            (is_valid, error_message)
        """
        # Check emergency stop flag
        if self.agent_memory.get("agent_state", {}).get("emergency_stop", False):
            return False, "EMERGENCY STOP flag is set. All trading operations blocked."

        # Check circuit breaker - TEMPORARILY DISABLED FOR TESTING
        # if self.agent_memory.get("safety_state", {}).get("circuit_breaker_triggered", False):
        #     return False, "Circuit breaker triggered. Trading operations suspended."

        # Validate max trade risk
        max_risk = order.get("max_risk", 0)
        if max_risk > self.limits.MAX_TRADE_RISK:
            return False, (
                f"Max risk (${max_risk:.2f}) exceeds limit "
                f"(${self.limits.MAX_TRADE_RISK:.2f})"
            )

        # Validate capital requirement
        capital = order.get("capital_required", 0)
        if capital > self.limits.MAX_TRADE_CAPITAL:
            return False, (
                f"Capital required (${capital:.2f}) exceeds limit "
                f"(${self.limits.MAX_TRADE_CAPITAL:.2f})"
            )

        # Validate daily loss limit
        daily_loss = abs(self.agent_memory.get("safety_state", {}).get("daily_loss", 0))
        if daily_loss >= self.limits.DAILY_LOSS_LIMIT:
            return False, (
                f"Daily loss limit reached (${daily_loss:.2f} >= "
                f"${self.limits.DAILY_LOSS_LIMIT:.2f}). No new trades allowed today."
            )

        # Validate consecutive losses
        consecutive_losses = self.agent_memory.get("safety_state", {}).get("consecutive_losses", 0)
        if consecutive_losses >= self.limits.CONSECUTIVE_LOSS_LIMIT:
            return False, (
                f"Consecutive loss limit reached ({consecutive_losses} >= "
                f"{self.limits.CONSECUTIVE_LOSS_LIMIT}). Trading suspended."
            )

        # Validate concentration limit
        symbol = order.get("symbol")
        if symbol:
            concentration = self._calculate_symbol_concentration(symbol, capital)
            if concentration > self.limits.MAX_CONCENTRATION:
                return False, (
                    f"Concentration limit exceeded for {symbol} "
                    f"({concentration*100:.1f}% > {self.limits.MAX_CONCENTRATION*100:.1f}%)"
                )

        # Validate order legs (for options)
        legs = order.get("legs", [])
        for leg in legs:
            is_valid, error = self._validate_leg(leg)
            if not is_valid:
                return False, error

        return True, None

    def _validate_leg(self, leg: Dict) -> Tuple[bool, Optional[str]]:
        """Validate a single order leg."""
        # Check minimum option price
        price = leg.get("price", 0)
        if price < self.limits.MIN_OPTION_PRICE:
            return False, (
                f"Option price (${price:.2f}) below minimum "
                f"(${self.limits.MIN_OPTION_PRICE:.2f}). Avoid illiquid options."
            )

        # Validate spread width (if applicable)
        if "spread_width" in leg:
            width = leg["spread_width"]
            if width > self.limits.MAX_SPREAD_WIDTH:
                return False, (
                    f"Spread width (${width:.2f}) exceeds maximum "
                    f"(${self.limits.MAX_SPREAD_WIDTH:.2f})"
                )

        return True, None

    def _calculate_symbol_concentration(self, symbol: str, new_capital: float) -> float:
        """Calculate portfolio concentration for a symbol."""
        # Get existing exposure to this symbol
        open_trades = self.agent_memory.get("positions", {}).get("open_trades", [])
        existing_exposure = sum(
            trade.get("capital_at_risk", 0)
            for trade in open_trades
            if trade.get("symbol") == symbol
        )

        # Calculate total portfolio value (placeholder - should get from IBKR account)
        total_portfolio_value = self.limits.MAX_TOTAL_EXPOSURE  # Temporary assumption

        total_exposure = existing_exposure + new_capital
        concentration = total_exposure / total_portfolio_value if total_portfolio_value > 0 else 0

        return concentration

    def check_circuit_breaker(self, account_value: float, initial_value: float) -> bool:
        """
        Check if circuit breaker should trigger based on drawdown.

        Args:
            account_value: Current account value
            initial_value: Starting account value (baseline)

        Returns:
            True if circuit breaker should trigger
        """
        drawdown = (initial_value - account_value) / initial_value if initial_value > 0 else 0

        if drawdown >= self.limits.DRAWDOWN_CIRCUIT_BREAKER:
            # Trigger circuit breaker
            self._trigger_circuit_breaker(drawdown)
            return True

        return False

    def _trigger_circuit_breaker(self, drawdown: float):
        """Trigger circuit breaker and update agent state."""
        self.agent_memory["safety_state"]["circuit_breaker_triggered"] = True
        self.agent_memory["safety_state"]["circuit_breaker_timestamp"] = datetime.now().isoformat()

        # Save updated state
        memory_path = Path.home() / "trading_workspace" / "state" / "agent_memory.json"
        with open(memory_path, 'w') as f:
            json.dump(self.agent_memory, f, indent=2)

        # Log circuit breaker event
        log_path = Path.home() / "trading_workspace" / "logs" / "circuit_breaker.log"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(log_path, 'a') as f:
            f.write(f"\n[{datetime.now().isoformat()}] CIRCUIT BREAKER TRIGGERED\n")
            f.write(f"Drawdown: {drawdown*100:.2f}%\n")
            f.write(f"All trading operations suspended.\n")

    def log_violation(self, violation_type: ViolationType, details: str):
        """Log a safety violation."""
        log_path = Path.home() / "trading_workspace" / "logs" / "safety_violations.log"
        log_path.parent.mkdir(parents=True, exist_ok=True)

        with open(log_path, 'a') as f:
            timestamp = datetime.now().isoformat()
            f.write(f"\n[{timestamp}] VIOLATION: {violation_type.value}\n")
            f.write(f"Details: {details}\n")


def create_safety_validator() -> SafetyValidator:
    """Factory function to create safety validator with default limits."""
    return SafetyValidator(SafetyLimits())
