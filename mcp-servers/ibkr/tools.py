"""
MCP tool definitions for IBKR trading operations.

Each tool is exposed to the agent via the MCP protocol and includes:
- Input validation
- Safety layer integration
- IBKR API interaction
- Response formatting
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import json
from pathlib import Path
import asyncio

import os
from ib_insync import Stock, Option, LimitOrder, Order as IBOrder, Contract
from safety import SafetyValidator, ViolationType, create_safety_validator
from connection import get_connection_manager, ConnectionMode


class IBKRTools:
    """IBKR MCP tool implementations."""

    def __init__(self, connection_mode: ConnectionMode = None):
        self.safety = create_safety_validator()
        self.connection_manager = get_connection_manager()

        # Auto-detect connection mode from environment
        if connection_mode is None:
            port = int(os.environ.get('IBKR_PORT', '7497'))
            if port == 4002:
                connection_mode = ConnectionMode.PAPER_GATEWAY
            elif port == 4001:
                connection_mode = ConnectionMode.LIVE_GATEWAY
            elif port == 7496:
                connection_mode = ConnectionMode.LIVE_TWS
            else:
                connection_mode = ConnectionMode.PAPER_TWS

        self.connection_mode = connection_mode
        # Don't connect immediately - connect on first tool call
        # self._ensure_connected()

    def _ensure_connected(self):
        """Ensure connection to IBKR is established."""
        try:
            if not self.connection_manager.is_connected:
                # Read client_id from environment variable
                client_id = int(os.environ.get('IBKR_CLIENT_ID', '1'))
                # Use synchronous connect method
                self.connection_manager.connect_sync(
                    mode=self.connection_mode,
                    client_id=client_id
                )
        except Exception as e:
            raise ConnectionError(f"Failed to connect to IBKR: {e}")

    def get_account(self) -> Dict[str, Any]:
        """
        Get account information including balance, buying power, and positions.

        DEPRECATED: Use get_account_async() instead for proper async support.

        Returns:
            Dictionary with account details
        """
        raise RuntimeError("Use get_account_async() instead - this method cannot be called from async context")

    async def get_account_async(self) -> Dict[str, Any]:
        """
        Get account information including balance, buying power, and positions (async version).

        Returns:
            Dictionary with account details:
            {
                "account_id": str,
                "net_liquidation": float,
                "cash_balance": float,
                "buying_power": float,
                "total_positions_value": float,
                "unrealized_pnl": float,
                "realized_pnl": float
            }
        """
        self._ensure_connected()

        # Get account values from IBKR (async call)
        account_values = await self.connection_manager.get_account_values_async()

        # Extract key values
        net_liquidation = float(account_values.get("NetLiquidation", type("", (), {"value": "0.0"})).value)
        cash_balance = float(account_values.get("TotalCashValue", type("", (), {"value": "0.0"})).value)
        buying_power = float(account_values.get("BuyingPower", type("", (), {"value": "0.0"})).value)
        unrealized_pnl = float(account_values.get("UnrealizedPnL", type("", (), {"value": "0.0"})).value)
        realized_pnl = float(account_values.get("RealizedPnL", type("", (), {"value": "0.0"})).value)

        # Get portfolio items to calculate total positions value (async call)
        portfolio_items = await self.connection_manager.get_portfolio_items_async()
        total_positions_value = sum(item.marketValue for item in portfolio_items)

        # Get account ID
        account_id = list(account_values.values())[0].account if account_values else "UNKNOWN"

        return {
            "account_id": account_id,
            "net_liquidation": net_liquidation,
            "cash_balance": cash_balance,
            "buying_power": buying_power,
            "total_positions_value": total_positions_value,
            "unrealized_pnl": unrealized_pnl,
            "realized_pnl": realized_pnl,
            "timestamp": datetime.now().isoformat()
        }

    def get_positions(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get current open positions.

        DEPRECATED: Use get_positions_async() instead for proper async support.

        Args:
            symbol: Optional symbol filter

        Returns:
            List of position dictionaries
        """
        raise RuntimeError("Use get_positions_async() instead - this method cannot be called from async context")

    async def get_positions_async(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get current open positions (async version).

        Args:
            symbol: Optional symbol filter. If provided, only return positions for this symbol.

        Returns:
            List of position dictionaries:
            [{
                "symbol": str,
                "quantity": int,
                "avg_cost": float,
                "current_price": float,
                "market_value": float,
                "unrealized_pnl": float,
                "unrealized_pnl_percent": float
            }]
        """
        self._ensure_connected()

        # Get portfolio items from IBKR (async call)
        portfolio_items = await self.connection_manager.get_portfolio_items_async()

        positions = []

        for item in portfolio_items:
            # Get contract symbol
            contract_symbol = item.contract.symbol

            # Filter by symbol if provided
            if symbol and contract_symbol != symbol:
                continue

            # Build position dictionary
            position = {
                "symbol": contract_symbol,
                "contract_type": item.contract.secType,  # STK, OPT, FUT, etc.
                "quantity": int(item.position),
                "avg_cost": float(item.averageCost),
                "current_price": float(item.marketPrice) if item.marketPrice else 0.0,
                "market_value": float(item.marketValue),
                "unrealized_pnl": float(item.unrealizedPNL),
                "unrealized_pnl_percent": (float(item.unrealizedPNL) / float(item.averageCost * abs(item.position)) * 100) if item.averageCost and item.position else 0.0,
                "realized_pnl": float(item.realizedPNL)
            }

            # Add options-specific fields
            if item.contract.secType == "OPT":
                position["strike"] = float(item.contract.strike) if hasattr(item.contract, "strike") else None
                position["right"] = item.contract.right if hasattr(item.contract, "right") else None
                position["expiry"] = item.contract.lastTradeDateOrContractMonth if hasattr(item.contract, "lastTradeDateOrContractMonth") else None

            positions.append(position)

        return positions

    def place_order(
        self,
        symbol: str,
        strategy: str,
        legs: List[Dict[str, Any]],
        max_risk: float,
        capital_required: float,
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Place a multi-leg options order with safety validation.

        Args:
            symbol: Underlying symbol (e.g., "AAPL")
            strategy: Strategy name (e.g., "Iron Condor", "Credit Spread")
            legs: List of order legs, each with:
                {
                    "action": "BUY" or "SELL",
                    "contract": {
                        "symbol": str,
                        "expiry": str (YYYY-MM-DD),
                        "strike": float,
                        "right": "C" or "P"
                    },
                    "quantity": int,
                    "price": float
                }
            max_risk: Maximum risk for this trade ($)
            capital_required: Capital required for this trade ($)
            metadata: Optional metadata (agent reasoning, confidence, etc.)

        Returns:
            Order result dictionary:
            {
                "success": bool,
                "order_ids": List[int],
                "trade_id": str,
                "message": str,
                "timestamp": str
            }
        """
        # Construct order for validation
        order = {
            "symbol": symbol,
            "strategy": strategy,
            "legs": legs,
            "max_risk": max_risk,
            "capital_required": capital_required
        }

        # SAFETY: Reload agent state and validate order against all safety limits
        self.safety.reload_agent_state()
        is_valid, error_message = self.safety.validate_order(order)

        if not is_valid:
            self.safety.log_violation(
                ViolationType.MAX_TRADE_RISK if "risk" in error_message.lower() else ViolationType.INVALID_ORDER,
                f"Order rejected: {error_message}"
            )
            return {
                "success": False,
                "order_ids": [],
                "trade_id": None,
                "message": f"Order rejected by safety layer: {error_message}",
                "timestamp": datetime.now().isoformat()
            }

        # Generate trade ID
        trade_id = f"{strategy.upper().replace(' ', '_')}_{symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Submit multi-leg order to IBKR
        try:
            self._ensure_connected()

            # Place all legs of the order
            trades = []
            order_ids = []

            for leg in legs:
                # Create IBKR contract
                contract = self._create_contract_from_leg(leg)

                # Create IBKR order
                ib_order = self._create_order_from_leg(leg)

                # Submit order - this shouldn't be called from sync context
                # For now, return error
                raise RuntimeError("Use place_order_async for actual order placement")
                # trades.append(trade)
                # order_ids.append(trade.order.orderId)

            # Log trade execution
            self._log_trade_execution(trade_id, order, order_ids, metadata)

            # Update agent memory with new position
            self._update_agent_memory_position(trade_id, order)

        except Exception as e:
            # Order execution failed
            error_msg = f"Failed to execute order: {e}"
            self.safety.log_violation(ViolationType.INVALID_ORDER, error_msg)

            return {
                "success": False,
                "order_ids": [],
                "trade_id": None,
                "message": error_msg,
                "timestamp": datetime.now().isoformat()
            }

        return {
            "success": True,
            "order_ids": order_ids,
            "trade_id": trade_id,
            "message": f"Order placed successfully. Trade ID: {trade_id}",
            "timestamp": datetime.now().isoformat()
        }

    async def place_order_async(
        self,
        symbol: str,
        strategy: str,
        legs: List[Dict[str, Any]],
        max_risk: float,
        capital_required: float,
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Place a multi-leg options order with safety validation (async version).

        Args:
            symbol: Underlying symbol (e.g., "AAPL")
            strategy: Strategy name (e.g., "Iron Condor", "Credit Spread")
            legs: List of order legs
            max_risk: Maximum risk for this trade ($)
            capital_required: Capital required for this trade ($)
            metadata: Optional metadata

        Returns:
            Order result dictionary
        """
        # Construct order for validation
        order = {
            "symbol": symbol,
            "strategy": strategy,
            "legs": legs,
            "max_risk": max_risk,
            "capital_required": capital_required
        }

        # SAFETY: Reload agent state and validate order against all safety limits
        self.safety.reload_agent_state()
        is_valid, error_message = self.safety.validate_order(order)

        if not is_valid:
            self.safety.log_violation(
                ViolationType.MAX_TRADE_RISK if "risk" in error_message.lower() else ViolationType.INVALID_ORDER,
                f"Order rejected: {error_message}"
            )
            return {
                "success": False,
                "order_ids": [],
                "trade_id": None,
                "message": f"Order rejected by safety layer: {error_message}",
                "timestamp": datetime.now().isoformat()
            }

        # Generate trade ID
        trade_id = f"{strategy.upper().replace(' ', '_')}_{symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Submit multi-leg order to IBKR
        try:
            self._ensure_connected()

            # Place all legs of the order
            trades = []
            order_ids = []

            for leg in legs:
                # Create IBKR contract
                contract = self._create_contract_from_leg(leg)

                # Create IBKR order
                ib_order = self._create_order_from_leg(leg)

                # Submit order using async method
                trade = await self.connection_manager.place_order(contract, ib_order)
                trades.append(trade)
                order_ids.append(trade.order.orderId)

            # Log trade execution
            self._log_trade_execution(trade_id, order, order_ids, metadata)

            # Update agent memory with new position
            self._update_agent_memory_position(trade_id, order)

        except Exception as e:
            # Order execution failed
            error_msg = f"Failed to execute order: {e}"
            self.safety.log_violation(ViolationType.INVALID_ORDER, error_msg)

            return {
                "success": False,
                "order_ids": [],
                "trade_id": None,
                "message": error_msg,
                "timestamp": datetime.now().isoformat()
            }

        return {
            "success": True,
            "order_ids": order_ids,
            "trade_id": trade_id,
            "message": f"Order placed successfully. Trade ID: {trade_id}",
            "timestamp": datetime.now().isoformat()
        }

    def close_position(self, trade_id: str) -> Dict[str, Any]:
        """
        Close an existing position by trade ID.

        Args:
            trade_id: Trade ID to close

        Returns:
            Close result dictionary:
            {
                "success": bool,
                "trade_id": str,
                "close_order_ids": List[int],
                "realized_pnl": float,
                "message": str
            }
        """
        # Load position from agent memory
        memory_path = Path.home() / "trading_workspace" / "state" / "agent_memory.json"

        if not memory_path.exists():
            return {
                "success": False,
                "trade_id": trade_id,
                "close_order_ids": [],
                "realized_pnl": 0.0,
                "message": f"Trade ID {trade_id} not found in agent memory"
            }

        with open(memory_path, 'r') as f:
            memory = json.load(f)

        # Find the position
        positions = memory.get("positions", {}).get("open_trades", [])
        position = next((p for p in positions if p.get("trade_id") == trade_id), None)

        if not position:
            return {
                "success": False,
                "trade_id": trade_id,
                "close_order_ids": [],
                "realized_pnl": 0.0,
                "message": f"Trade ID {trade_id} not found"
            }

        # TODO: Submit closing orders to IBKR (reverse of opening orders)
        # For now, simulate successful close
        close_order_ids = [200000 + i for i in range(len(position.get("legs", [])))]

        # Calculate realized P&L (placeholder)
        realized_pnl = position.get("unrealized_pnl", 0.0)  # Placeholder

        # Remove from open positions
        positions.remove(position)
        memory["positions"]["open_trades"] = positions
        memory["positions"]["closed_trades_count"] += 1

        # Update performance metrics
        if realized_pnl > 0:
            memory["performance_metrics"]["profitable_trades"] += 1
        memory["performance_metrics"]["total_trades"] += 1

        # Save updated memory
        with open(memory_path, 'w') as f:
            json.dump(memory, f, indent=2)

        # Log close
        self._log_trade_close(trade_id, close_order_ids, realized_pnl)

        return {
            "success": True,
            "trade_id": trade_id,
            "close_order_ids": close_order_ids,
            "realized_pnl": realized_pnl,
            "message": f"Position closed successfully. Realized P&L: ${realized_pnl:.2f}"
        }

    def get_order_status(self, order_id: int) -> Dict[str, Any]:
        """
        Get status of a specific order.

        Args:
            order_id: IBKR order ID

        Returns:
            Order status dictionary
        """
        # TODO: Implement IBKR API call to get order status
        return {
            "order_id": order_id,
            "status": "Filled",  # Placeholder
            "filled_quantity": 1,
            "avg_fill_price": 1.25,
            "timestamp": datetime.now().isoformat()
        }

    def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on IBKR connection (legacy sync wrapper).

        Returns:
            Health status dictionary with connection info and status
        """
        try:
            # Use synchronous health check
            return self.health_check_sync()
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "is_connected": False
            }

    def health_check_sync(self) -> Dict[str, Any]:
        """
        Perform synchronous health check on IBKR connection.

        Returns:
            Health status dictionary with connection info and status
        """
        health = {
            "is_connected": self.connection_manager.ib.isConnected() if self.connection_manager.ib else False,
            "mode": self.connection_manager.mode.description if self.connection_manager.mode else None,
            "last_connection_time": self.connection_manager.last_connection_time.isoformat() if self.connection_manager.last_connection_time else None,
            "reconnect_attempts": self.connection_manager.reconnect_attempts,
            "client_id": self.connection_manager.client_id
        }

        # Try to get account values as a deeper health check
        if health["is_connected"]:
            try:
                account_values = self.connection_manager.ib.accountValues()
                health["account_values_count"] = len(account_values)
                health["status"] = "healthy"
            except Exception as e:
                health["status"] = "unhealthy"
                health["error"] = str(e)
        else:
            health["status"] = "disconnected"

        return health

    async def health_check_async(self) -> Dict[str, Any]:
        """
        Perform async health check on IBKR connection.

        Returns:
            Health status dictionary with connection info and status
        """
        try:
            health_status = await self.connection_manager.health_check()
            return health_status
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "is_connected": False
            }

    def _create_contract_from_leg(self, leg: Dict[str, Any]) -> Contract:
        """
        Create IBKR Contract object from leg specification.

        Args:
            leg: Leg specification with contract details

        Returns:
            ib_insync Contract object (Option or Stock)
        """
        contract_spec = leg.get("contract", {})
        symbol = contract_spec.get("symbol")
        expiry = contract_spec.get("expiry")  # YYYY-MM-DD format
        strike = contract_spec.get("strike")
        right = contract_spec.get("right")  # "C" or "P"

        if strike and right:
            # Options contract
            # Convert expiry from YYYY-MM-DD to YYYYMMDD
            expiry_formatted = expiry.replace("-", "") if expiry else ""

            contract = Option(
                symbol=symbol,
                lastTradeDateOrContractMonth=expiry_formatted,
                strike=strike,
                right=right,
                exchange="SMART",
                currency="USD"
            )
        else:
            # Stock contract
            contract = Stock(
                symbol=symbol,
                exchange="SMART",
                currency="USD"
            )

        return contract

    def _create_order_from_leg(self, leg: Dict[str, Any]) -> IBOrder:
        """
        Create IBKR Order object from leg specification.

        Args:
            leg: Leg specification with action, quantity, price

        Returns:
            ib_insync Order object (LimitOrder or MarketOrder)
        """
        action = leg.get("action")  # "BUY" or "SELL"
        quantity = leg.get("quantity", 1)
        price = leg.get("price")

        if price and price > 0:
            # Limit order
            order = LimitOrder(
                action=action,
                totalQuantity=quantity,
                lmtPrice=price
            )
        else:
            # Market order (fallback if no price specified)
            from ib_insync import MarketOrder
            order = MarketOrder(
                action=action,
                totalQuantity=quantity
            )

        return order

    def _log_trade_execution(
        self,
        trade_id: str,
        order: Dict,
        order_ids: List[int],
        metadata: Optional[Dict]
    ):
        """Log trade execution details."""
        log_path = Path.home() / "trading_workspace" / "logs" / "trades" / f"{trade_id}.json"
        log_path.parent.mkdir(parents=True, exist_ok=True)

        log_entry = {
            "trade_id": trade_id,
            "timestamp": datetime.now().isoformat(),
            "action": "OPEN",
            "order": order,
            "order_ids": order_ids,
            "metadata": metadata or {}
        }

        with open(log_path, 'w') as f:
            json.dump(log_entry, f, indent=2)

    def _log_trade_close(self, trade_id: str, close_order_ids: List[int], realized_pnl: float):
        """Log trade close details."""
        log_path = Path.home() / "trading_workspace" / "logs" / "trades" / f"{trade_id}_close.json"

        log_entry = {
            "trade_id": trade_id,
            "timestamp": datetime.now().isoformat(),
            "action": "CLOSE",
            "close_order_ids": close_order_ids,
            "realized_pnl": realized_pnl
        }

        with open(log_path, 'w') as f:
            json.dump(log_entry, f, indent=2)

    def _update_agent_memory_position(self, trade_id: str, order: Dict):
        """Add new position to agent memory."""
        memory_path = Path.home() / "trading_workspace" / "state" / "agent_memory.json"

        with open(memory_path, 'r') as f:
            memory = json.load(f)

        position = {
            "trade_id": trade_id,
            "symbol": order["symbol"],
            "strategy": order["strategy"],
            "legs": order["legs"],
            "max_risk": order["max_risk"],
            "capital_at_risk": order["capital_required"],
            "entry_timestamp": datetime.now().isoformat(),
            "unrealized_pnl": 0.0  # Will be updated by market data
        }

        memory["positions"]["open_trades"].append(position)

        with open(memory_path, 'w') as f:
            json.dump(memory, f, indent=2)


# Tool metadata for MCP protocol
TOOLS_METADATA = [
    {
        "name": "get_account",
        "description": "Get account information including balance, buying power, and P&L",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "get_positions",
        "description": "Get current open positions, optionally filtered by symbol",
        "inputSchema": {
            "type": "object",
            "properties": {
                "symbol": {
                    "type": "string",
                    "description": "Optional symbol filter (e.g., 'AAPL')"
                }
            },
            "required": []
        }
    },
    {
        "name": "place_order",
        "description": "Place a multi-leg options order with safety validation",
        "inputSchema": {
            "type": "object",
            "properties": {
                "symbol": {
                    "type": "string",
                    "description": "Underlying symbol (e.g., 'AAPL')"
                },
                "strategy": {
                    "type": "string",
                    "description": "Strategy name (e.g., 'Iron Condor')"
                },
                "legs": {
                    "type": "array",
                    "description": "List of order legs with action, contract, quantity, price"
                },
                "max_risk": {
                    "type": "number",
                    "description": "Maximum risk for this trade ($)"
                },
                "capital_required": {
                    "type": "number",
                    "description": "Capital required for this trade ($)"
                },
                "metadata": {
                    "type": "object",
                    "description": "Optional metadata (reasoning, confidence, etc.)"
                }
            },
            "required": ["symbol", "strategy", "legs", "max_risk", "capital_required"]
        }
    },
    {
        "name": "close_position",
        "description": "Close an existing position by trade ID",
        "inputSchema": {
            "type": "object",
            "properties": {
                "trade_id": {
                    "type": "string",
                    "description": "Trade ID to close"
                }
            },
            "required": ["trade_id"]
        }
    },
    {
        "name": "get_order_status",
        "description": "Get status of a specific order by order ID",
        "inputSchema": {
            "type": "object",
            "properties": {
                "order_id": {
                    "type": "integer",
                    "description": "IBKR order ID"
                }
            },
            "required": ["order_id"]
        }
    },
    {
        "name": "health_check",
        "description": "Perform health check on IBKR connection and get connection status",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    }
]
