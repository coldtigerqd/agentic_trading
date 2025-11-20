"""
Unit tests for IBKR MCP Tools.

Tests all MCP tools exposed to the agent:
- get_account()
- get_positions()
- place_order()
- close_position()
- get_order_status()
- health_check()
"""

import pytest
import asyncio
from unittest.mock import Mock, MagicMock, patch, AsyncMock
from pathlib import Path
import json

from tools import IBKRTools, TOOLS_METADATA
from connection import ConnectionMode


# ==========================================
# Tool Metadata Tests
# ==========================================

@pytest.mark.unit
def test_tools_metadata_structure():
    """Test that all tools have proper metadata."""
    assert len(TOOLS_METADATA) == 6  # 6 tools total

    tool_names = [tool["name"] for tool in TOOLS_METADATA]
    assert "get_account" in tool_names
    assert "get_positions" in tool_names
    assert "place_order" in tool_names
    assert "close_position" in tool_names
    assert "get_order_status" in tool_names
    assert "health_check" in tool_names

    # Verify each tool has required fields
    for tool in TOOLS_METADATA:
        assert "name" in tool
        assert "description" in tool
        assert "inputSchema" in tool
        assert "type" in tool["inputSchema"]
        assert "properties" in tool["inputSchema"]
        assert "required" in tool["inputSchema"]


# ==========================================
# get_account() Tests
# ==========================================

@pytest.mark.unit
def test_get_account_success(ibkr_tools, connection_manager, mock_account_values, mock_portfolio_items):
    """Test get_account returns account information."""
    connection_manager.ib.accountValues.return_value = mock_account_values
    connection_manager.ib.portfolio.return_value = mock_portfolio_items

    with patch('asyncio.run') as mock_run:
        # Mock asyncio.run to return our mock data
        def side_effect(coro):
            if 'get_account_values' in str(coro):
                return {av.tag: av for av in mock_account_values}
            elif 'get_portfolio_items' in str(coro):
                return mock_portfolio_items
            return None

        mock_run.side_effect = side_effect

        account = ibkr_tools.get_account()

    assert "account_id" in account
    assert "net_liquidation" in account
    assert "cash_balance" in account
    assert "buying_power" in account
    assert "total_positions_value" in account
    assert "unrealized_pnl" in account
    assert "realized_pnl" in account
    assert "timestamp" in account

    assert account["net_liquidation"] == 25000.00
    assert account["cash_balance"] == 15000.00


@pytest.mark.unit
def test_get_account_connection_error(ibkr_tools, connection_manager):
    """Test get_account handles connection errors."""
    connection_manager.ib.isConnected.return_value = False

    with patch.object(ibkr_tools, '_ensure_connected', side_effect=ConnectionError("Not connected")):
        with pytest.raises(ConnectionError):
            ibkr_tools.get_account()


# ==========================================
# get_positions() Tests
# ==========================================

@pytest.mark.unit
def test_get_positions_all(ibkr_tools, connection_manager, mock_portfolio_items):
    """Test get_positions returns all positions."""
    with patch('asyncio.run', return_value=mock_portfolio_items):
        positions = ibkr_tools.get_positions()

    assert len(positions) == 2
    assert positions[0]["symbol"] == "AAPL"
    assert positions[0]["contract_type"] == "OPT"
    assert positions[0]["strike"] == 175.0
    assert positions[0]["right"] == "P"
    assert positions[0]["quantity"] == -1


@pytest.mark.unit
def test_get_positions_filtered_by_symbol(ibkr_tools, connection_manager, mock_portfolio_items):
    """Test get_positions with symbol filter."""
    with patch('asyncio.run', return_value=mock_portfolio_items):
        positions = ibkr_tools.get_positions(symbol="AAPL")

    assert len(positions) == 2
    assert all(pos["symbol"] == "AAPL" for pos in positions)


@pytest.mark.unit
def test_get_positions_no_positions(ibkr_tools, connection_manager):
    """Test get_positions when no positions exist."""
    with patch('asyncio.run', return_value=[]):
        positions = ibkr_tools.get_positions()

    assert positions == []


# ==========================================
# place_order() Tests
# ==========================================

@pytest.mark.unit
def test_place_order_iron_condor_success(ibkr_tools, sample_iron_condor_order, mock_trade):
    """Test placing Iron Condor order successfully."""
    # Mock safety validation to pass
    ibkr_tools.safety.validate_order = Mock(return_value=(True, ""))

    # Mock contract creation and order placement
    with patch('asyncio.run') as mock_run:
        mock_run.return_value = mock_trade

        result = ibkr_tools.place_order(
            symbol=sample_iron_condor_order["symbol"],
            strategy=sample_iron_condor_order["strategy"],
            legs=sample_iron_condor_order["legs"],
            max_risk=sample_iron_condor_order["max_risk"],
            capital_required=sample_iron_condor_order["capital_required"]
        )

    assert result["success"] is True
    assert len(result["order_ids"]) == 4  # 4 legs
    assert "trade_id" in result
    assert "IRON_CONDOR" in result["trade_id"]
    assert "AAPL" in result["trade_id"]


@pytest.mark.unit
def test_place_order_safety_rejection(ibkr_tools, sample_iron_condor_order):
    """Test place_order rejected by safety layer."""
    # Mock safety validation to fail
    ibkr_tools.safety.validate_order = Mock(return_value=(False, "Max risk ($600) exceeds limit ($500)"))

    result = ibkr_tools.place_order(
        symbol=sample_iron_condor_order["symbol"],
        strategy=sample_iron_condor_order["strategy"],
        legs=sample_iron_condor_order["legs"],
        max_risk=600.0,  # Exceeds limit
        capital_required=sample_iron_condor_order["capital_required"]
    )

    assert result["success"] is False
    assert result["order_ids"] == []
    assert result["trade_id"] is None
    assert "safety layer" in result["message"].lower()


@pytest.mark.unit
def test_place_order_execution_failure(ibkr_tools, sample_iron_condor_order):
    """Test place_order handles execution failures."""
    ibkr_tools.safety.validate_order = Mock(return_value=(True, ""))

    with patch('asyncio.run', side_effect=Exception("IBKR API error")):
        result = ibkr_tools.place_order(
            symbol=sample_iron_condor_order["symbol"],
            strategy=sample_iron_condor_order["strategy"],
            legs=sample_iron_condor_order["legs"],
            max_risk=sample_iron_condor_order["max_risk"],
            capital_required=sample_iron_condor_order["capital_required"]
        )

    assert result["success"] is False
    assert "Failed to execute order" in result["message"]


@pytest.mark.unit
def test_place_order_credit_spread(ibkr_tools, sample_credit_spread_order, mock_trade):
    """Test placing Credit Spread order."""
    ibkr_tools.safety.validate_order = Mock(return_value=(True, ""))

    with patch('asyncio.run', return_value=mock_trade):
        result = ibkr_tools.place_order(
            symbol=sample_credit_spread_order["symbol"],
            strategy=sample_credit_spread_order["strategy"],
            legs=sample_credit_spread_order["legs"],
            max_risk=sample_credit_spread_order["max_risk"],
            capital_required=sample_credit_spread_order["capital_required"]
        )

    assert result["success"] is True
    assert len(result["order_ids"]) == 2  # 2 legs for credit spread


# ==========================================
# Contract Creation Tests
# ==========================================

@pytest.mark.unit
def test_create_contract_from_leg_option(ibkr_tools):
    """Test creating option contract from leg specification."""
    leg = {
        "contract": {
            "symbol": "AAPL",
            "expiry": "2025-11-23",
            "strike": 175.0,
            "right": "P"
        }
    }

    contract = ibkr_tools._create_contract_from_leg(leg)

    assert contract.symbol == "AAPL"
    assert contract.lastTradeDateOrContractMonth == "20251123"
    assert contract.strike == 175.0
    assert contract.right == "P"
    assert contract.exchange == "SMART"


@pytest.mark.unit
def test_create_contract_from_leg_stock(ibkr_tools):
    """Test creating stock contract from leg specification."""
    leg = {
        "contract": {
            "symbol": "AAPL"
        }
    }

    contract = ibkr_tools._create_contract_from_leg(leg)

    assert contract.symbol == "AAPL"
    assert contract.exchange == "SMART"


@pytest.mark.unit
def test_create_order_from_leg_limit(ibkr_tools):
    """Test creating limit order from leg specification."""
    leg = {
        "action": "SELL",
        "quantity": 1,
        "price": 1.50
    }

    order = ibkr_tools._create_order_from_leg(leg)

    assert order.action == "SELL"
    assert order.totalQuantity == 1
    assert order.lmtPrice == 1.50


@pytest.mark.unit
def test_create_order_from_leg_market(ibkr_tools):
    """Test creating market order when price is not specified."""
    leg = {
        "action": "BUY",
        "quantity": 1,
        "price": 0  # No price = market order
    }

    order = ibkr_tools._create_order_from_leg(leg)

    assert order.action == "BUY"
    assert order.totalQuantity == 1


# ==========================================
# close_position() Tests
# ==========================================

@pytest.mark.unit
def test_close_position_success(ibkr_tools, temp_agent_memory):
    """Test closing a position successfully."""
    # Add position to memory
    with open(temp_agent_memory, 'r') as f:
        memory = json.load(f)

    memory["positions"]["open_trades"].append({
        "trade_id": "TEST_TRADE_123",
        "symbol": "AAPL",
        "legs": [{}, {}],
        "unrealized_pnl": 50.0
    })

    with open(temp_agent_memory, 'w') as f:
        json.dump(memory, f)

    # Mock memory path
    with patch('pathlib.Path.home', return_value=temp_agent_memory.parent.parent):
        with patch.object(Path, 'exists', return_value=True):
            # Need to create the trading_workspace structure
            workspace = temp_agent_memory.parent.parent / "trading_workspace" / "state"
            workspace.mkdir(parents=True, exist_ok=True)
            memory_file = workspace / "agent_memory.json"

            with open(temp_agent_memory, 'r') as f:
                memory_data = json.load(f)
            with open(memory_file, 'w') as f:
                json.dump(memory_data, f)

            result = ibkr_tools.close_position("TEST_TRADE_123")

    assert result["success"] is True
    assert result["trade_id"] == "TEST_TRADE_123"
    assert result["realized_pnl"] == 50.0


@pytest.mark.unit
def test_close_position_not_found(ibkr_tools, temp_agent_memory):
    """Test closing a position that doesn't exist."""
    with patch('pathlib.Path.home', return_value=temp_agent_memory.parent.parent):
        workspace = temp_agent_memory.parent.parent / "trading_workspace" / "state"
        workspace.mkdir(parents=True, exist_ok=True)
        memory_file = workspace / "agent_memory.json"

        with open(temp_agent_memory, 'r') as f:
            memory_data = json.load(f)
        with open(memory_file, 'w') as f:
            json.dump(memory_data, f)

        result = ibkr_tools.close_position("NONEXISTENT_TRADE")

    assert result["success"] is False
    assert "not found" in result["message"]


# ==========================================
# get_order_status() Tests
# ==========================================

@pytest.mark.unit
def test_get_order_status(ibkr_tools):
    """Test getting order status (placeholder implementation)."""
    result = ibkr_tools.get_order_status(100001)

    assert "order_id" in result
    assert result["order_id"] == 100001
    assert "status" in result
    assert "timestamp" in result


# ==========================================
# health_check() Tests
# ==========================================

@pytest.mark.unit
def test_health_check_success(ibkr_tools, connection_manager):
    """Test health_check returns healthy status."""
    health_data = {
        "is_connected": True,
        "status": "healthy",
        "mode": "Paper Trading (TWS)"
    }

    with patch('asyncio.run', return_value=health_data):
        result = ibkr_tools.health_check()

    assert result["status"] == "healthy"
    assert result["is_connected"] is True


@pytest.mark.unit
def test_health_check_error(ibkr_tools):
    """Test health_check handles errors."""
    with patch('asyncio.run', side_effect=Exception("Connection error")):
        result = ibkr_tools.health_check()

    assert result["status"] == "error"
    assert result["is_connected"] is False
    assert "error" in result


# ==========================================
# Ensure Connected Tests
# ==========================================

@pytest.mark.unit
def test_ensure_connected_already_connected(ibkr_tools, connection_manager):
    """Test _ensure_connected when already connected."""
    connection_manager.is_connected = True

    # Should not raise
    ibkr_tools._ensure_connected()


@pytest.mark.unit
def test_ensure_connected_reconnects(ibkr_tools, connection_manager):
    """Test _ensure_connected triggers reconnection."""
    connection_manager.is_connected = False

    with patch('asyncio.run'):
        ibkr_tools._ensure_connected()
        # Should have called connect
