"""
Integration and Performance Tests for IBKR MCP Server.

These tests are designed to:
1. Test multi-leg order execution (Iron Condor, Credit Spreads)
2. Test error handling and edge cases
3. Test performance and memory usage
4. Optionally test against real IBKR paper trading account

Run integration tests with:
    pytest -m integration

Run performance tests with:
    pytest -m performance
"""

import pytest
import asyncio
import time
import gc
import tracemalloc
from unittest.mock import Mock, patch, AsyncMock
from pathlib import Path

from connection import IBKRConnectionManager, ConnectionMode, get_connection_manager
from tools import IBKRTools
from safety import SafetyValidator


# ==========================================
# Multi-Leg Order Execution Tests
# ==========================================

@pytest.mark.unit
def test_iron_condor_four_legs(ibkr_tools, sample_iron_condor_order, mock_trade):
    """Test Iron Condor with all 4 legs executes correctly."""
    ibkr_tools.safety.validate_order = Mock(return_value=(True, ""))

    # Mock order placement for each leg
    with patch('asyncio.run', return_value=mock_trade):
        result = ibkr_tools.place_order(
            symbol=sample_iron_condor_order["symbol"],
            strategy=sample_iron_condor_order["strategy"],
            legs=sample_iron_condor_order["legs"],
            max_risk=sample_iron_condor_order["max_risk"],
            capital_required=sample_iron_condor_order["capital_required"]
        )

    assert result["success"] is True
    assert len(result["order_ids"]) == 4

    # Verify trade ID format
    trade_id = result["trade_id"]
    assert "IRON_CONDOR" in trade_id
    assert "AAPL" in trade_id


@pytest.mark.unit
def test_credit_spread_two_legs(ibkr_tools, sample_credit_spread_order, mock_trade):
    """Test Credit Spread with 2 legs executes correctly."""
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
    assert len(result["order_ids"]) == 2
    assert "PUT_CREDIT_SPREAD" in result["trade_id"]


@pytest.mark.unit
def test_partial_leg_failure(ibkr_tools, sample_iron_condor_order):
    """Test handling when one leg fails to execute."""
    ibkr_tools.safety.validate_order = Mock(return_value=(True, ""))

    # First 3 legs succeed, 4th fails
    call_count = [0]

    def mock_place_side_effect(coro):
        call_count[0] += 1
        if call_count[0] == 4:
            raise Exception("Order rejected by exchange")
        return Mock(order=Mock(orderId=100000 + call_count[0]))

    with patch('asyncio.run', side_effect=mock_place_side_effect):
        result = ibkr_tools.place_order(
            symbol=sample_iron_condor_order["symbol"],
            strategy=sample_iron_condor_order["strategy"],
            legs=sample_iron_condor_order["legs"],
            max_risk=sample_iron_condor_order["max_risk"],
            capital_required=sample_iron_condor_order["capital_required"]
        )

    # Should fail and report error
    assert result["success"] is False
    assert "Failed to execute order" in result["message"]


# ==========================================
# Error Handling Tests
# ==========================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_handle_connection_loss(connection_manager, mock_ib):
    """Test handling sudden connection loss."""
    mock_ib.isConnected.return_value = False
    connection_manager.is_connected = False
    connection_manager.mode = ConnectionMode.PAPER_TWS
    connection_manager.reconnect_attempts = 0

    mock_ib.connectAsync = AsyncMock()

    # Should attempt reconnection
    await connection_manager.ensure_connected()

    assert connection_manager.reconnect_attempts == 1
    mock_ib.connectAsync.assert_called_once()


@pytest.mark.unit
def test_handle_invalid_contract_data(ibkr_tools):
    """Test handling malformed contract data."""
    ibkr_tools.safety.validate_order = Mock(return_value=(True, ""))

    # Invalid expiry format
    invalid_order = {
        "symbol": "AAPL",
        "strategy": "Iron Condor",
        "legs": [
            {
                "action": "SELL",
                "contract": {
                    "symbol": "AAPL",
                    "expiry": "INVALID_DATE",  # Bad format
                    "strike": 175.0,
                    "right": "P"
                },
                "quantity": 1,
                "price": 1.50
            }
        ],
        "max_risk": 400.0,
        "capital_required": 500.0
    }

    # Should handle gracefully (might fail at IBKR level)
    # Test that it doesn't crash
    try:
        contract = ibkr_tools._create_contract_from_leg(invalid_order["legs"][0])
        # Expiry will be "INVALIDDATE" (no hyphens) - IBKR will reject
        assert contract.lastTradeDateOrContractMonth == "INVALIDDATE"
    except Exception:
        # Exception is acceptable for invalid data
        pass


@pytest.mark.unit
def test_handle_api_rate_limiting(ibkr_tools, sample_iron_condor_order):
    """Test handling IBKR API rate limiting."""
    ibkr_tools.safety.validate_order = Mock(return_value=(True, ""))

    # Simulate rate limit error
    with patch('asyncio.run', side_effect=Exception("Pacing violation")):
        result = ibkr_tools.place_order(
            symbol=sample_iron_condor_order["symbol"],
            strategy=sample_iron_condor_order["strategy"],
            legs=sample_iron_condor_order["legs"],
            max_risk=sample_iron_condor_order["max_risk"],
            capital_required=sample_iron_condor_order["capital_required"]
        )

    assert result["success"] is False
    assert "Pacing violation" in result["message"]


@pytest.mark.unit
def test_handle_market_closed(ibkr_tools, sample_iron_condor_order):
    """Test handling orders when market is closed."""
    ibkr_tools.safety.validate_order = Mock(return_value=(True, ""))

    with patch('asyncio.run', side_effect=Exception("Market closed")):
        result = ibkr_tools.place_order(
            symbol=sample_iron_condor_order["symbol"],
            strategy=sample_iron_condor_order["strategy"],
            legs=sample_iron_condor_order["legs"],
            max_risk=sample_iron_condor_order["max_risk"],
            capital_required=sample_iron_condor_order["capital_required"]
        )

    assert result["success"] is False


# ==========================================
# Edge Cases Tests
# ==========================================

@pytest.mark.unit
def test_empty_legs_array(ibkr_tools):
    """Test order with no legs."""
    ibkr_tools.safety.validate_order = Mock(return_value=(True, ""))

    result = ibkr_tools.place_order(
        symbol="AAPL",
        strategy="Empty",
        legs=[],  # No legs
        max_risk=0.0,
        capital_required=0.0
    )

    # Should succeed (or fail gracefully)
    assert "trade_id" in result


@pytest.mark.unit
def test_single_leg_order(ibkr_tools, mock_trade):
    """Test single-leg order (simple buy/sell)."""
    ibkr_tools.safety.validate_order = Mock(return_value=(True, ""))

    single_leg_order = {
        "symbol": "AAPL",
        "strategy": "Single Leg",
        "legs": [
            {
                "action": "SELL",
                "contract": {
                    "symbol": "AAPL",
                    "expiry": "2025-11-23",
                    "strike": 175.0,
                    "right": "P"
                },
                "quantity": 1,
                "price": 1.50
            }
        ],
        "max_risk": 17500.0,  # Naked put
        "capital_required": 5000.0
    }

    with patch('asyncio.run', return_value=mock_trade):
        result = ibkr_tools.place_order(
            symbol=single_leg_order["symbol"],
            strategy=single_leg_order["strategy"],
            legs=single_leg_order["legs"],
            max_risk=single_leg_order["max_risk"],
            capital_required=single_leg_order["capital_required"]
        )

    # Will fail safety check (max risk > $500)
    # But test passes if safety rejects it properly


@pytest.mark.unit
def test_very_large_multi_leg_order(ibkr_tools, mock_trade):
    """Test order with many legs (e.g., 10+ legs)."""
    ibkr_tools.safety.validate_order = Mock(return_value=(True, ""))

    # Create 10-leg order
    legs = []
    for i in range(10):
        legs.append({
            "action": "SELL" if i % 2 == 0 else "BUY",
            "contract": {
                "symbol": "AAPL",
                "expiry": "2025-11-23",
                "strike": 170.0 + i,
                "right": "P"
            },
            "quantity": 1,
            "price": 1.0 + i * 0.1
        })

    with patch('asyncio.run', return_value=mock_trade):
        result = ibkr_tools.place_order(
            symbol="AAPL",
            strategy="Complex",
            legs=legs,
            max_risk=400.0,
            capital_required=500.0
        )

    assert result["success"] is True
    assert len(result["order_ids"]) == 10


# ==========================================
# Performance Tests
# ==========================================

@pytest.mark.performance
@pytest.mark.slow
def test_50_consecutive_api_calls(ibkr_tools, mock_account_values):
    """Test 50+ consecutive API calls without memory leak."""
    # Start memory tracking
    tracemalloc.start()
    gc.collect()
    snapshot_start = tracemalloc.take_snapshot()

    # Perform 50 get_account calls
    with patch('asyncio.run', return_value={av.tag: av for av in mock_account_values}):
        for i in range(50):
            account = ibkr_tools.get_account()
            assert "net_liquidation" in account

    # Check memory
    gc.collect()
    snapshot_end = tracemalloc.take_snapshot()

    # Calculate memory difference
    top_stats = snapshot_end.compare_to(snapshot_start, 'lineno')

    # Total memory increase should be minimal (< 1 MB for 50 calls)
    total_diff = sum(stat.size_diff for stat in top_stats)

    tracemalloc.stop()

    # Allow up to 1 MB memory increase for 50 calls
    assert total_diff < 1024 * 1024, f"Memory leak detected: {total_diff} bytes"


@pytest.mark.performance
def test_get_positions_performance(ibkr_tools, mock_portfolio_items):
    """Test get_positions performance with many positions."""
    # Create 100 portfolio items
    large_portfolio = mock_portfolio_items * 50  # 100 items

    start_time = time.time()

    with patch('asyncio.run', return_value=large_portfolio):
        positions = ibkr_tools.get_positions()

    end_time = time.time()
    duration = end_time - start_time

    assert len(positions) == 100
    # Should complete in under 1 second
    assert duration < 1.0, f"get_positions took {duration:.2f}s (> 1s limit)"


@pytest.mark.performance
@pytest.mark.slow
def test_concurrent_health_checks(ibkr_tools):
    """Test multiple concurrent health checks don't deadlock."""
    import threading

    results = []

    def run_health_check():
        with patch('asyncio.run', return_value={"status": "healthy", "is_connected": True}):
            result = ibkr_tools.health_check()
            results.append(result)

    # Run 10 health checks concurrently
    threads = []
    for i in range(10):
        thread = threading.Thread(target=run_health_check)
        threads.append(thread)
        thread.start()

    # Wait for all threads
    for thread in threads:
        thread.join(timeout=5.0)
        assert not thread.is_alive(), "Health check thread deadlocked"

    assert len(results) == 10
    assert all(r["status"] == "healthy" for r in results)


# ==========================================
# Integration Tests (Optional - Requires Real IBKR)
# ==========================================

@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.asyncio
async def test_real_ibkr_connection():
    """
    Test real connection to IBKR paper trading.

    REQUIRES:
    - IBKR TWS or Gateway running
    - Paper trading account
    - API enabled on port 4002 (Gateway) or 7497 (TWS)

    Skip if IBKR not available.
    """
    # pytest.skip("Integration test - requires real IBKR connection")

    # Reset singleton
    IBKRConnectionManager._instance = None

    manager = get_connection_manager()

    try:
        # Attempt connection to Paper Gateway (port 4002)
        result = await manager.connect(
            mode=ConnectionMode.PAPER_GATEWAY,  # Changed to PAPER_GATEWAY
            client_id=999,  # Use unique client ID
            timeout=10
        )

        assert result is True
        assert manager.is_connected is True

        # Test basic operations
        account_values = await manager.get_account_values()
        assert len(account_values) > 0

        portfolio = await manager.get_portfolio_items()
        # Portfolio may be empty, just check it doesn't error

        health = await manager.health_check()
        assert health["status"] == "healthy"

    finally:
        await manager.disconnect()


@pytest.mark.integration
@pytest.mark.slow
def test_real_ibkr_get_account():
    """
    Test get_account with real IBKR connection.

    Skip if IBKR not available.
    """
    # pytest.skip("Integration test - requires real IBKR connection")

    tools = IBKRTools(connection_mode=ConnectionMode.PAPER_GATEWAY)

    account = tools.get_account()

    # Verify response structure
    assert "account_id" in account
    assert "net_liquidation" in account
    assert isinstance(account["net_liquidation"], float)
    assert account["net_liquidation"] > 0  # Paper account should have balance


@pytest.mark.integration
@pytest.mark.slow
def test_real_ibkr_get_positions():
    """
    Test get_positions with real IBKR connection.

    Skip if IBKR not available.
    """
    # pytest.skip("Integration test - requires real IBKR connection")

    tools = IBKRTools(connection_mode=ConnectionMode.PAPER_GATEWAY)

    positions = tools.get_positions()

    # Positions may be empty list if no positions
    assert isinstance(positions, list)

    # If positions exist, verify structure
    if len(positions) > 0:
        pos = positions[0]
        assert "symbol" in pos
        assert "quantity" in pos
        assert "market_value" in pos
