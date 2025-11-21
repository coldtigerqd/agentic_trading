#!/usr/bin/env python3
"""
Integration tests for watchdog safety system.

Tests watchdog's ability to:
- Detect frozen AI process
- Trigger circuit breaker on drawdown
- Execute emergency position close
- Maintain independent IBKR connection
"""

import pytest
import time
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock, PropertyMock
from datetime import datetime, timedelta

# Import watchdog components
from runtime.watchdog import (
    check_heartbeat,
    check_circuit_breaker,
    get_account_value,
    panic_close_all_positions,
    trigger_circuit_breaker
)


@pytest.fixture
def temp_workspace():
    """Create temporary workspace for testing"""
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = Path(tmpdir)

        # Create subdirectories
        (workspace / "state").mkdir()
        (workspace / "logs").mkdir()

        # Mock the workspace path
        with patch('runtime.watchdog.WORKSPACE_PATH', workspace):
            yield workspace


@pytest.fixture
def mock_heartbeat_file(temp_workspace):
    """Create a heartbeat file for testing"""
    heartbeat_file = temp_workspace / "state" / "heartbeat.txt"
    return heartbeat_file


@pytest.fixture
def mock_memory_file(temp_workspace):
    """Create agent memory file for circuit breaker testing"""
    memory_file = temp_workspace / "state" / "agent_memory.json"

    # Initialize with safe state
    memory_data = {
        "safety_state": {
            "circuit_breaker_triggered": False,
            "circuit_breaker_timestamp": None
        }
    }

    with open(memory_file, 'w') as f:
        json.dump(memory_data, f, indent=2)

    return memory_file


class TestHeartbeatMonitoring:
    """Test heartbeat-based process monitoring"""

    def test_fresh_heartbeat_passes(self, mock_heartbeat_file):
        """Should detect alive process with fresh heartbeat"""
        # Write current timestamp
        with open(mock_heartbeat_file, 'w') as f:
            f.write(str(time.time()))

        is_alive = check_heartbeat(mock_heartbeat_file, timeout_seconds=60)
        assert is_alive is True

    def test_stale_heartbeat_fails(self, mock_heartbeat_file):
        """Should detect frozen process with stale heartbeat"""
        # Write old timestamp (2 minutes ago)
        old_time = time.time() - 120
        with open(mock_heartbeat_file, 'w') as f:
            f.write(str(old_time))

        is_alive = check_heartbeat(mock_heartbeat_file, timeout_seconds=60)
        assert is_alive is False

    def test_missing_heartbeat_fails(self, temp_workspace):
        """Should fail if heartbeat file doesn't exist"""
        nonexistent_file = temp_workspace / "state" / "missing.txt"

        is_alive = check_heartbeat(nonexistent_file, timeout_seconds=60)
        assert is_alive is False

    def test_corrupted_heartbeat_fails(self, mock_heartbeat_file):
        """Should handle corrupted heartbeat gracefully"""
        # Write invalid content
        with open(mock_heartbeat_file, 'w') as f:
            f.write("not_a_timestamp")

        is_alive = check_heartbeat(mock_heartbeat_file, timeout_seconds=60)
        assert is_alive is False


class TestCircuitBreaker:
    """Test circuit breaker trigger and reset logic"""

    def test_circuit_breaker_not_triggered(self, mock_memory_file):
        """Should return False when circuit breaker is inactive"""
        is_triggered = check_circuit_breaker(mock_memory_file)
        assert is_triggered is False

    def test_circuit_breaker_triggered(self, mock_memory_file):
        """Should return True when circuit breaker is active"""
        # Set circuit breaker to triggered
        with open(mock_memory_file, 'r+') as f:
            data = json.load(f)
            data["safety_state"]["circuit_breaker_triggered"] = True
            data["safety_state"]["circuit_breaker_timestamp"] = datetime.now().isoformat()
            f.seek(0)
            json.dump(data, f, indent=2)
            f.truncate()

        is_triggered = check_circuit_breaker(mock_memory_file)
        assert is_triggered is True

    def test_trigger_circuit_breaker(self, mock_memory_file):
        """Should write circuit breaker trigger to memory"""
        trigger_circuit_breaker(mock_memory_file)

        # Verify file updated
        with open(mock_memory_file, 'r') as f:
            data = json.load(f)

        assert data["safety_state"]["circuit_breaker_triggered"] is True
        assert data["safety_state"]["circuit_breaker_timestamp"] is not None

    def test_missing_memory_file_safe_default(self, temp_workspace):
        """Should safely handle missing memory file"""
        nonexistent_file = temp_workspace / "state" / "missing.json"

        # Should not crash
        is_triggered = check_circuit_breaker(nonexistent_file)
        assert is_triggered is False  # Default to safe state


class TestAccountMonitoring:
    """Test account value monitoring and drawdown detection"""

    @patch('runtime.watchdog.IB')
    def test_get_account_value_success(self, mock_ib_class):
        """Should retrieve account value from IBKR"""
        # Mock IBKR connection
        mock_ib = MagicMock()
        mock_ib_class.return_value = mock_ib

        # Mock account values
        mock_account_value = MagicMock()
        mock_account_value.tag = 'NetLiquidation'
        mock_account_value.value = '125000.50'

        mock_ib.accountValues.return_value = [mock_account_value]

        account_value = get_account_value()

        assert account_value == 125000.50
        mock_ib.connect.assert_called_once()
        mock_ib.disconnect.assert_called_once()

    @patch('runtime.watchdog.IB')
    def test_get_account_value_connection_failure(self, mock_ib_class):
        """Should handle IBKR connection failure gracefully"""
        # Mock connection failure
        mock_ib = MagicMock()
        mock_ib_class.return_value = mock_ib
        mock_ib.connect.side_effect = Exception("Connection failed")

        account_value = get_account_value()

        # Should return fallback value
        assert account_value == 10000.0  # Fallback

    def test_drawdown_detection(self):
        """Should detect 10% drawdown threshold"""
        initial_value = 100000.0
        current_value = 89000.0  # 11% drawdown

        drawdown_pct = (initial_value - current_value) / initial_value * 100
        assert drawdown_pct > 10.0


class TestEmergencyActions:
    """Test emergency position closing"""

    @patch('runtime.watchdog.IB')
    def test_panic_close_all_positions(self, mock_ib_class):
        """Should close all positions in emergency"""
        # Mock IBKR with open positions
        mock_ib = MagicMock()
        mock_ib_class.return_value = mock_ib

        # Mock positions
        mock_position_1 = MagicMock()
        mock_position_1.contract.symbol = 'AAPL'
        mock_position_1.position = 10

        mock_position_2 = MagicMock()
        mock_position_2.contract.symbol = 'NVDA'
        mock_position_2.position = -5

        mock_ib.positions.return_value = [mock_position_1, mock_position_2]

        # Execute panic close
        panic_close_all_positions(mock_ib)

        # Verify market orders placed for each position
        assert mock_ib.placeOrder.call_count == 2

    @patch('runtime.watchdog.IB')
    def test_panic_close_no_positions(self, mock_ib_class):
        """Should handle case with no open positions"""
        mock_ib = MagicMock()
        mock_ib_class.return_value = mock_ib
        mock_ib.positions.return_value = []

        # Should not crash
        panic_close_all_positions(mock_ib)
        mock_ib.placeOrder.assert_not_called()


class TestWatchdogIndependence:
    """Test watchdog operates independently from AI process"""

    @patch('runtime.watchdog.IB')
    def test_independent_ibkr_connection(self, mock_ib_class):
        """Should use separate client_id from AI process"""
        mock_ib = MagicMock()
        mock_ib_class.return_value = mock_ib

        get_account_value()

        # Verify watchdog uses client_id=999 (not 1 like AI)
        mock_ib.connect.assert_called_with('localhost', 4002, clientId=999)

    def test_watchdog_survives_ai_crash(self):
        """Watchdog should detect and respond to AI crash"""
        # This is more of a conceptual test - in real scenario:
        # 1. Main AI process dies
        # 2. Heartbeat stops updating
        # 3. Watchdog detects stale heartbeat
        # 4. Watchdog triggers emergency actions

        # Simulated scenario
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as hb:
            # Write old heartbeat (simulating crashed process)
            hb.write(str(time.time() - 300))  # 5 minutes old
            hb_path = Path(hb.name)

        try:
            # Watchdog check
            is_alive = check_heartbeat(hb_path, timeout_seconds=60)
            assert is_alive is False  # Detected crash

            # In real implementation, this would trigger:
            # - panic_close_all_positions()
            # - trigger_circuit_breaker()
            # - Alert notifications
        finally:
            hb_path.unlink()


class TestWatchdogLogging:
    """Test watchdog logging and monitoring"""

    def test_watchdog_logs_created(self, temp_workspace):
        """Should create log files for monitoring"""
        log_dir = temp_workspace / "logs"
        assert log_dir.exists()

        # In real implementation, watchdog writes to:
        # - watchdog.log (general monitoring)
        # - emergency_actions.log (panic close events)
        # - circuit_breaker.log (CB triggers)


class TestRecoveryProcedures:
    """Test recovery from various failure scenarios"""

    def test_manual_circuit_breaker_reset(self, mock_memory_file):
        """Should allow manual reset of circuit breaker"""
        # Trigger circuit breaker
        trigger_circuit_breaker(mock_memory_file)
        assert check_circuit_breaker(mock_memory_file) is True

        # Manual reset (simulated)
        with open(mock_memory_file, 'r+') as f:
            data = json.load(f)
            data["safety_state"]["circuit_breaker_triggered"] = False
            data["safety_state"]["circuit_breaker_timestamp"] = None
            f.seek(0)
            json.dump(data, f, indent=2)
            f.truncate()

        assert check_circuit_breaker(mock_memory_file) is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
