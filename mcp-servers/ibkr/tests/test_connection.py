"""
Unit tests for IBKR Connection Manager.

Tests the connection manager's ability to:
- Connect to IBKR TWS/Gateway
- Handle disconnections and reconnections
- Monitor connection health
- Manage account and portfolio data retrieval
"""

import pytest
import asyncio
from unittest.mock import Mock, MagicMock, patch, AsyncMock
from datetime import datetime

from connection import (
    IBKRConnectionManager,
    ConnectionMode,
    get_connection_manager
)


# ==========================================
# Connection Tests
# ==========================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_connection_manager_singleton():
    """Test that connection manager is a singleton."""
    manager1 = IBKRConnectionManager()
    manager2 = IBKRConnectionManager()
    assert manager1 is manager2


@pytest.mark.unit
@pytest.mark.asyncio
async def test_connect_paper_tws(connection_manager, mock_ib):
    """Test connection to paper trading TWS."""
    mock_ib.connectAsync = AsyncMock(return_value=None)
    mock_ib.isConnected.return_value = True

    result = await connection_manager.connect(mode=ConnectionMode.PAPER_TWS)

    assert result is True
    assert connection_manager.is_connected is True
    assert connection_manager.mode == ConnectionMode.PAPER_TWS
    assert connection_manager.reconnect_attempts == 0


@pytest.mark.unit
@pytest.mark.asyncio
async def test_connect_failure(connection_manager, mock_ib):
    """Test connection failure handling."""
    mock_ib.connectAsync = AsyncMock(side_effect=ConnectionError("Connection refused"))

    with pytest.raises(ConnectionError, match="Connection refused"):
        await connection_manager.connect(mode=ConnectionMode.PAPER_TWS)

    assert connection_manager.is_connected is False


@pytest.mark.unit
@pytest.mark.asyncio
async def test_disconnect(connection_manager, mock_ib):
    """Test disconnection."""
    mock_ib.isConnected.return_value = True
    connection_manager.is_connected = True

    await connection_manager.disconnect()

    mock_ib.disconnect.assert_called_once()
    assert connection_manager.is_connected is False


@pytest.mark.unit
@pytest.mark.asyncio
async def test_ensure_connected_when_disconnected(connection_manager, mock_ib):
    """Test ensure_connected reconnects when disconnected."""
    mock_ib.isConnected.return_value = False
    mock_ib.connectAsync = AsyncMock(return_value=None)
    connection_manager.is_connected = False
    connection_manager.mode = ConnectionMode.PAPER_TWS

    await connection_manager.ensure_connected()

    mock_ib.connectAsync.assert_called_once()
    assert connection_manager.reconnect_attempts == 1


@pytest.mark.unit
@pytest.mark.asyncio
async def test_ensure_connected_max_retries(connection_manager, mock_ib):
    """Test ensure_connected fails after max retries."""
    mock_ib.isConnected.return_value = False
    connection_manager.is_connected = False
    connection_manager.mode = ConnectionMode.PAPER_TWS
    connection_manager.reconnect_attempts = 5  # Already at max

    with pytest.raises(ConnectionError, match="Max reconnection attempts"):
        await connection_manager.ensure_connected()


# ==========================================
# Health Check Tests
# ==========================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_health_check_healthy(connection_manager, mock_ib, mock_account_values):
    """Test health check when connection is healthy."""
    mock_ib.isConnected.return_value = True
    mock_ib.accountValues.return_value = mock_account_values
    connection_manager.is_connected = True
    connection_manager.mode = ConnectionMode.PAPER_TWS
    connection_manager.last_connection_time = datetime.now()

    health = await connection_manager.health_check()

    assert health["is_connected"] is True
    assert health["status"] == "healthy"
    assert health["mode"] == "Paper Trading (TWS)"
    assert health["account_values_count"] == len(mock_account_values)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_health_check_disconnected(connection_manager, mock_ib):
    """Test health check when disconnected."""
    mock_ib.isConnected.return_value = False
    connection_manager.is_connected = False

    health = await connection_manager.health_check()

    assert health["is_connected"] is False
    assert health["status"] == "disconnected"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_health_check_unhealthy(connection_manager, mock_ib):
    """Test health check when connection exists but API calls fail."""
    mock_ib.isConnected.return_value = True
    mock_ib.accountValues.side_effect = Exception("API error")
    connection_manager.is_connected = True

    health = await connection_manager.health_check()

    assert health["is_connected"] is True
    assert health["status"] == "unhealthy"
    assert "error" in health


# ==========================================
# Account Operations Tests
# ==========================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_account_values(connection_manager, mock_ib, mock_account_values):
    """Test retrieving account values."""
    mock_ib.isConnected.return_value = True
    mock_ib.accountValues.return_value = mock_account_values
    mock_ib.reqAccountSummary = Mock()
    mock_ib.waitUntilReadyAsync = AsyncMock()

    values = await connection_manager.get_account_values()

    assert "NetLiquidation" in values
    assert values["NetLiquidation"].value == "25000.00"
    assert "BuyingPower" in values
    assert values["BuyingPower"].value == "50000.00"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_portfolio_items(connection_manager, mock_ib, mock_portfolio_items):
    """Test retrieving portfolio items."""
    mock_ib.isConnected.return_value = True
    mock_ib.portfolio.return_value = mock_portfolio_items

    portfolio = await connection_manager.get_portfolio_items()

    assert len(portfolio) == 2
    assert portfolio[0].contract.symbol == "AAPL"
    assert portfolio[0].position == -1


# ==========================================
# Order Operations Tests
# ==========================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_place_order(connection_manager, mock_ib, mock_trade):
    """Test placing an order."""
    from ib_insync import Option, LimitOrder

    mock_ib.isConnected.return_value = True
    mock_ib.qualifyContractsAsync = AsyncMock(return_value=[Option("AAPL", "20251123", 175.0, "P")])
    mock_ib.placeOrder.return_value = mock_trade
    mock_ib.waitUntilReadyAsync = AsyncMock()

    contract = Option("AAPL", "20251123", 175.0, "P")
    order = LimitOrder("SELL", 1, 1.50)

    trade = await connection_manager.place_order(contract, order)

    assert trade.order.orderId == 100001
    mock_ib.placeOrder.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_place_order_invalid_contract(connection_manager, mock_ib):
    """Test placing order with invalid contract."""
    from ib_insync import Option, LimitOrder

    mock_ib.isConnected.return_value = True
    mock_ib.qualifyContractsAsync = AsyncMock(return_value=[])  # Contract not found

    contract = Option("INVALID", "20251123", 999.0, "P")
    order = LimitOrder("SELL", 1, 1.50)

    with pytest.raises(ValueError, match="Could not qualify contract"):
        await connection_manager.place_order(contract, order)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_cancel_order(connection_manager, mock_ib):
    """Test canceling an order."""
    from ib_insync import LimitOrder

    mock_ib.isConnected.return_value = True
    mock_ib.cancelOrder = Mock()
    mock_ib.waitUntilReadyAsync = AsyncMock()

    order = LimitOrder("SELL", 1, 1.50)
    order.orderId = 100001

    await connection_manager.cancel_order(order)

    mock_ib.cancelOrder.assert_called_once_with(order)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_open_trades(connection_manager, mock_ib, mock_trade):
    """Test retrieving open trades."""
    mock_ib.isConnected.return_value = True
    mock_ib.openTrades.return_value = [mock_trade]

    trades = await connection_manager.get_open_trades()

    assert len(trades) == 1
    assert trades[0].order.orderId == 100001


# ==========================================
# Market Data Tests
# ==========================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_current_price(connection_manager, mock_ib):
    """Test getting current price for a contract."""
    from ib_insync import Stock

    mock_ticker = Mock()
    mock_ticker.last = 180.50
    mock_ticker.bid = 180.45
    mock_ticker.ask = 180.55

    mock_ib.isConnected.return_value = True
    mock_ib.qualifyContractsAsync = AsyncMock(return_value=[Stock("AAPL", "SMART", "USD")])
    mock_ib.reqMktData.return_value = mock_ticker
    mock_ib.waitUntilReadyAsync = AsyncMock()
    mock_ib.cancelMktData = Mock()

    contract = Stock("AAPL", "SMART", "USD")
    price = await connection_manager.get_current_price(contract)

    assert price == 180.50
    mock_ib.cancelMktData.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_current_price_use_midpoint(connection_manager, mock_ib):
    """Test getting price using bid/ask midpoint when last is unavailable."""
    from ib_insync import Stock

    mock_ticker = Mock()
    mock_ticker.last = None
    mock_ticker.bid = 180.45
    mock_ticker.ask = 180.55

    mock_ib.isConnected.return_value = True
    mock_ib.qualifyContractsAsync = AsyncMock(return_value=[Stock("AAPL", "SMART", "USD")])
    mock_ib.reqMktData.return_value = mock_ticker
    mock_ib.waitUntilReadyAsync = AsyncMock()
    mock_ib.cancelMktData = Mock()

    contract = Stock("AAPL", "SMART", "USD")
    price = await connection_manager.get_current_price(contract)

    assert price == 180.50  # (180.45 + 180.55) / 2


# ==========================================
# Event Handler Tests
# ==========================================

@pytest.mark.unit
def test_on_connected_event(connection_manager):
    """Test _on_connected event handler."""
    connection_manager.mode = ConnectionMode.PAPER_TWS
    connection_manager.reconnect_attempts = 2

    connection_manager._on_connected()

    assert connection_manager.is_connected is True
    assert connection_manager.reconnect_attempts == 0


@pytest.mark.unit
def test_on_disconnected_event(connection_manager):
    """Test _on_disconnected event handler."""
    connection_manager.is_connected = True

    connection_manager._on_disconnected()

    assert connection_manager.is_connected is False


@pytest.mark.unit
def test_on_error_event_info(connection_manager):
    """Test _on_error with info message (code 2104)."""
    # Should log as debug, not error
    connection_manager._on_error(0, 2104, "Market data farm connection is OK", None)
    # No assertion needed - just verify it doesn't raise


@pytest.mark.unit
def test_on_error_event_warning(connection_manager):
    """Test _on_error with warning message (code >= 2000)."""
    connection_manager._on_error(0, 2110, "Connectivity between IB and TWS has been restored", None)
    # Should log as warning


@pytest.mark.unit
def test_on_error_event_error(connection_manager):
    """Test _on_error with actual error (code < 2000)."""
    connection_manager._on_error(100, 201, "Order rejected - insufficient margin", None)
    # Should log as error


# ==========================================
# Connection Mode Tests
# ==========================================

@pytest.mark.unit
def test_connection_modes():
    """Test all connection mode configurations."""
    assert ConnectionMode.PAPER_TWS.host == "localhost"
    assert ConnectionMode.PAPER_TWS.port == 7497
    assert ConnectionMode.PAPER_TWS.description == "Paper Trading (TWS)"

    assert ConnectionMode.PAPER_GATEWAY.port == 4002
    assert ConnectionMode.LIVE_TWS.port == 7496
    assert ConnectionMode.LIVE_GATEWAY.port == 4001


# ==========================================
# Singleton Tests
# ==========================================

@pytest.mark.unit
def test_get_connection_manager_singleton():
    """Test get_connection_manager returns singleton."""
    # Reset singleton
    from connection import _manager
    import connection as conn_module
    conn_module._manager = None

    manager1 = get_connection_manager()
    manager2 = get_connection_manager()

    assert manager1 is manager2
