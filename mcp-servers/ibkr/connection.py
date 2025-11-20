"""
IBKR Connection Manager

Handles connection to Interactive Brokers TWS/Gateway with automatic reconnection,
connection pooling, and health monitoring.

This module provides a singleton connection manager that:
- Connects to IBKR TWS (port 7497) or Gateway (port 4001)
- Automatically reconnects on disconnection
- Monitors connection health
- Provides async-safe access to IBKR API via ib_insync

Configuration:
    - Paper Trading: localhost:7497 (TWS) or localhost:4002 (Gateway)
    - Live Trading: localhost:7496 (TWS) or localhost:4001 (Gateway)
"""

import asyncio
import logging
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum

from ib_insync import IB, AccountValue, PortfolioItem, Contract, Order, Trade
from ib_insync import Stock, Option, Future, MarketOrder, LimitOrder
from ib_insync import util
from ib_insync.util import logToConsole


class ConnectionMode(Enum):
    """IBKR connection mode."""
    PAPER_TWS = ("localhost", 7497, "Paper Trading (TWS)")
    PAPER_GATEWAY = ("localhost", 4002, "Paper Trading (Gateway)")
    LIVE_TWS = ("localhost", 7496, "Live Trading (TWS)")
    LIVE_GATEWAY = ("localhost", 4001, "Live Trading (Gateway)")

    def __init__(self, host: str, port: int, description: str):
        self.host = host
        self.port = port
        self.description = description


class IBKRConnectionManager:
    """
    Singleton connection manager for IBKR TWS/Gateway.

    Usage:
        >>> manager = IBKRConnectionManager()
        >>> await manager.connect(mode=ConnectionMode.PAPER_TWS)
        >>> account_summary = await manager.get_account_summary()
        >>> await manager.disconnect()

    Features:
        - Automatic reconnection on disconnection
        - Connection health monitoring
        - Thread-safe singleton pattern
        - Async/await support via ib_insync
    """

    _instance: Optional['IBKRConnectionManager'] = None

    def __new__(cls):
        """Singleton pattern - only one connection manager instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize connection manager (called only once)."""
        if not hasattr(self, '_initialized'):
            self.ib: Optional[IB] = None  # Delay IB creation until first connect
            self.mode: Optional[ConnectionMode] = None
            self.client_id: int = 1
            self.is_connected: bool = False
            self.last_connection_time: Optional[datetime] = None
            self.reconnect_attempts: int = 0
            self.max_reconnect_attempts: int = 5

            # Set up logging
            self.logger = logging.getLogger(__name__)

            # Enable ib_insync logging (optional - can be disabled for production)
            # logToConsole(logging.WARNING)

            self._initialized = True

    def _ensure_ib_instance(self):
        """Ensure IB instance is created and callbacks are set up."""
        if self.ib is None:
            # Start the event loop for ib_insync to work with existing asyncio loop
            # This is needed when ib_insync is used within an async context
            try:
                util.startLoop()
            except RuntimeError:
                # Loop already started, which is fine
                pass

            self.ib = IB()
            # Connection callbacks
            self.ib.connectedEvent += self._on_connected
            self.ib.disconnectedEvent += self._on_disconnected
            self.ib.errorEvent += self._on_error

    def connect_sync(
        self,
        mode: ConnectionMode = ConnectionMode.PAPER_TWS,
        client_id: int = 1,
        timeout: int = 10,
        readonly: bool = False
    ) -> bool:
        """
        Connect to IBKR TWS or Gateway (synchronous version).

        Args:
            mode: Connection mode (paper/live, TWS/Gateway)
            client_id: Client ID for connection (default 1)
            timeout: Connection timeout in seconds
            readonly: If True, connect in read-only mode

        Returns:
            True if connection successful, False otherwise

        Raises:
            ConnectionError: If connection fails after retries
        """
        self._ensure_ib_instance()
        self.mode = mode
        self.client_id = client_id

        self.logger.info(f"Connecting to IBKR: {mode.description} ({mode.host}:{mode.port})")

        try:
            # Use synchronous connect method
            self.ib.connect(
                host=mode.host,
                port=mode.port,
                clientId=client_id,
                timeout=timeout,
                readonly=readonly
            )

            self.is_connected = True
            self.last_connection_time = datetime.now()
            self.reconnect_attempts = 0

            self.logger.info(f"Successfully connected to IBKR (Client ID: {client_id})")
            return True

        except Exception as e:
            self.logger.error(f"Failed to connect to IBKR: {e}")
            self.is_connected = False
            raise ConnectionError(f"Could not connect to IBKR {mode.description}: {e}")

    async def connect(
        self,
        mode: ConnectionMode = ConnectionMode.PAPER_TWS,
        client_id: int = 1,
        timeout: int = 10,
        readonly: bool = False
    ) -> bool:
        """
        Connect to IBKR TWS or Gateway (async version).

        Args:
            mode: Connection mode (paper/live, TWS/Gateway)
            client_id: Client ID for connection (default 1)
            timeout: Connection timeout in seconds
            readonly: If True, connect in read-only mode

        Returns:
            True if connection successful, False otherwise

        Raises:
            ConnectionError: If connection fails after retries
        """
        self._ensure_ib_instance()
        self.mode = mode
        self.client_id = client_id

        self.logger.info(f"Connecting to IBKR: {mode.description} ({mode.host}:{mode.port})")

        try:
            await self.ib.connectAsync(
                host=mode.host,
                port=mode.port,
                clientId=client_id,
                timeout=timeout,
                readonly=readonly
            )

            self.is_connected = True
            self.last_connection_time = datetime.now()
            self.reconnect_attempts = 0

            self.logger.info(f"Successfully connected to IBKR (Client ID: {client_id})")
            return True

        except Exception as e:
            self.logger.error(f"Failed to connect to IBKR: {e}")
            self.is_connected = False
            raise ConnectionError(f"Could not connect to IBKR {mode.description}: {e}")

    async def disconnect(self) -> None:
        """Disconnect from IBKR."""
        if self.ib and self.ib.isConnected():
            self.logger.info("Disconnecting from IBKR...")
            self.ib.disconnect()
            self.is_connected = False
            self.logger.info("Disconnected from IBKR")

    async def ensure_connected(self) -> None:
        """
        Ensure connection is alive, reconnect if necessary.

        Raises:
            ConnectionError: If reconnection fails
        """
        self._ensure_ib_instance()
        if not self.ib.isConnected():
            if self.reconnect_attempts >= self.max_reconnect_attempts:
                raise ConnectionError(
                    f"Max reconnection attempts ({self.max_reconnect_attempts}) reached"
                )

            self.logger.warning("Connection lost, attempting to reconnect...")
            self.reconnect_attempts += 1

            if self.mode:
                await self.connect(
                    mode=self.mode,
                    client_id=self.client_id
                )
            else:
                raise ConnectionError("Cannot reconnect: No previous connection mode set")

    def get_ib(self) -> IB:
        """
        Get the underlying IB instance.

        Returns:
            ib_insync IB instance

        Raises:
            ConnectionError: If not connected
        """
        self._ensure_ib_instance()
        if not self.ib.isConnected():
            raise ConnectionError("Not connected to IBKR. Call connect() first.")
        return self.ib

    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on IBKR connection.

        Returns:
            Health status dictionary
        """
        self._ensure_ib_instance()
        health = {
            "is_connected": self.ib.isConnected() if self.ib else False,
            "mode": self.mode.description if self.mode else None,
            "last_connection_time": self.last_connection_time.isoformat() if self.last_connection_time else None,
            "reconnect_attempts": self.reconnect_attempts,
            "client_id": self.client_id
        }

        # Try to get account values as a deeper health check
        if health["is_connected"]:
            try:
                account_values = self.ib.accountValues()
                health["account_values_count"] = len(account_values)
                health["status"] = "healthy"
            except Exception as e:
                health["status"] = "unhealthy"
                health["error"] = str(e)
        else:
            health["status"] = "disconnected"

        return health

    # ==========================================
    # Event Handlers
    # ==========================================

    def _on_connected(self):
        """Called when connection is established."""
        self.logger.info(f"✅ Connected to IBKR {self.mode.description if self.mode else ''}")
        self.is_connected = True
        self.reconnect_attempts = 0

    def _on_disconnected(self):
        """Called when connection is lost."""
        self.logger.warning(f"⚠️  Disconnected from IBKR {self.mode.description if self.mode else ''}")
        self.is_connected = False

    def _on_error(self, reqId: int, errorCode: int, errorString: str, contract: Contract):
        """Called on IBKR API errors."""
        # Error code 2104 is "Market data farm connection is OK" - not an error
        # Error code 2106 is "HMDS data farm connection is OK" - not an error
        if errorCode in [2104, 2106, 2158]:
            self.logger.debug(f"IBKR Info [{errorCode}]: {errorString}")
        elif errorCode >= 2000:
            # Warnings (2000+)
            self.logger.warning(f"IBKR Warning [{errorCode}]: {errorString}")
        else:
            # Errors (< 2000)
            self.logger.error(f"IBKR Error [{errorCode}]: {errorString} (ReqId: {reqId})")

    # ==========================================
    # Account Operations
    # ==========================================

    def get_account_values(self, account: str = "") -> Dict[str, AccountValue]:
        """
        Get all account values (synchronous method).

        Args:
            account: Account ID (empty string for default account)

        Returns:
            Dictionary mapping tag names to AccountValue objects
        """
        self._ensure_ib_instance()
        if not self.ib.isConnected():
            raise ConnectionError("Not connected to IBKR")

        # Get account values directly (ib_insync handles this synchronously)
        account_values = self.ib.accountValues(account)

        # Convert list to dictionary for easier access
        values_dict = {av.tag: av for av in account_values}

        return values_dict

    async def get_account_values_async(self, account: str = "") -> Dict[str, AccountValue]:
        """
        Get all account values (async method).

        Args:
            account: Account ID (empty string for default account)

        Returns:
            Dictionary mapping tag names to AccountValue objects
        """
        await self.ensure_connected()

        # Get account values using async-safe method
        account_values = self.ib.accountValues(account)

        # Convert list to dictionary for easier access
        values_dict = {av.tag: av for av in account_values}

        return values_dict

    def get_portfolio_items(self, account: str = "") -> list[PortfolioItem]:
        """
        Get current portfolio positions (synchronous method).

        Args:
            account: Account ID (empty string for default account)

        Returns:
            List of PortfolioItem objects
        """
        self._ensure_ib_instance()
        if not self.ib.isConnected():
            raise ConnectionError("Not connected to IBKR")

        portfolio = self.ib.portfolio(account)
        return portfolio

    async def get_portfolio_items_async(self, account: str = "") -> list[PortfolioItem]:
        """
        Get current portfolio positions (async method).

        Args:
            account: Account ID (empty string for default account)

        Returns:
            List of PortfolioItem objects
        """
        await self.ensure_connected()

        portfolio = self.ib.portfolio(account)
        return portfolio

    # ==========================================
    # Order Operations
    # ==========================================

    async def place_order(self, contract: Contract, order: Order) -> Trade:
        """
        Place an order with IBKR.

        Args:
            contract: IBKR Contract object (Stock, Option, etc.)
            order: IBKR Order object (Market, Limit, etc.)

        Returns:
            Trade object representing the placed order

        Raises:
            ValueError: If order validation fails
        """
        await self.ensure_connected()

        # Qualify the contract (get full contract details from IBKR)
        # Use synchronous method - ib_insync handles async internally
        qualified = self.ib.qualifyContracts(contract)
        await asyncio.sleep(0)  # Yield to event loop to let qualification complete

        if not qualified:
            raise ValueError(f"Could not qualify contract: {contract}")

        contract = qualified[0]

        # Place the order
        trade = self.ib.placeOrder(contract, order)

        # Wait for order to be submitted
        await asyncio.sleep(0)  # Yield to event loop

        self.logger.info(f"Order placed: {trade.order.orderType} {trade.order.action} "
                        f"{trade.order.totalQuantity} {contract.symbol}")

        return trade

    async def cancel_order(self, order: Order) -> None:
        """
        Cancel an existing order.

        Args:
            order: Order to cancel
        """
        await self.ensure_connected()
        self.ib.cancelOrder(order)
        await asyncio.sleep(0)  # Yield to event loop
        self.logger.info(f"Order cancelled: {order.orderId}")

    async def get_open_trades(self) -> list[Trade]:
        """
        Get all open (active) trades.

        Returns:
            List of Trade objects for open orders
        """
        await self.ensure_connected()
        return self.ib.openTrades()

    # ==========================================
    # Market Data Operations
    # ==========================================

    async def get_current_price(self, contract: Contract) -> Optional[float]:
        """
        Get current market price for a contract.

        Args:
            contract: IBKR Contract object

        Returns:
            Current price or None if not available
        """
        await self.ensure_connected()

        # Qualify contract
        qualified = self.ib.qualifyContracts(contract)
        await asyncio.sleep(0)  # Yield to event loop to let qualification complete
        if not qualified:
            return None

        contract = qualified[0]

        # Request market data
        ticker = self.ib.reqMktData(contract)
        await asyncio.sleep(0)  # Yield to event loop

        # Get last price (or mid price if last not available)
        if ticker.last and ticker.last > 0:
            price = ticker.last
        elif ticker.bid and ticker.ask:
            price = (ticker.bid + ticker.ask) / 2
        else:
            price = None

        # Cancel market data subscription
        self.ib.cancelMktData(contract)

        return price


# ==========================================
# Global Singleton Instance
# ==========================================

# Global connection manager instance (singleton)
_manager: Optional[IBKRConnectionManager] = None


def get_connection_manager() -> IBKRConnectionManager:
    """
    Get the global IBKR connection manager instance.

    Returns:
        IBKRConnectionManager singleton instance
    """
    global _manager
    if _manager is None:
        _manager = IBKRConnectionManager()
    return _manager
