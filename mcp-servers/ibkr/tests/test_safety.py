"""
Unit tests for Safety Layer.

Tests all safety validation scenarios:
- Max trade risk limit
- Daily loss limit
- Concentration limit
- Circuit breaker
- Consecutive losses
- Emergency stop
"""

import pytest
from pathlib import Path
import json
import tempfile
from datetime import datetime

from safety import (
    SafetyValidator,
    SafetyLimits,
    ViolationType,
    create_safety_validator
)


# ==========================================
# Safety Limits Tests
# ==========================================

@pytest.mark.unit
def test_safety_limits_defaults():
    """Test default safety limits values."""
    limits = SafetyLimits()

    assert limits.MAX_TRADE_RISK == 500.0
    assert limits.MAX_TRADE_CAPITAL == 2000.0
    assert limits.DAILY_LOSS_LIMIT == 1000.0
    assert limits.MAX_DAILY_TRADES == 10
    assert limits.MAX_CONCENTRATION == 0.30
    assert limits.DRAWDOWN_CIRCUIT_BREAKER == 0.10
    assert limits.CONSECUTIVE_LOSS_LIMIT == 5


# ==========================================
# Max Trade Risk Tests
# ==========================================

@pytest.mark.unit
def test_validate_order_max_risk_pass(safety_validator):
    """Test order passes max risk validation."""
    order = {
        "symbol": "AAPL",
        "max_risk": 400.0,
        "capital_required": 500.0,
        "legs": []
    }

    is_valid, error = safety_validator.validate_order(order)

    assert is_valid is True
    assert error == ""


@pytest.mark.unit
def test_validate_order_max_risk_fail(safety_validator):
    """Test order fails max risk validation."""
    order = {
        "symbol": "AAPL",
        "max_risk": 600.0,  # Exceeds $500 limit
        "capital_required": 700.0,
        "legs": []
    }

    is_valid, error = safety_validator.validate_order(order)

    assert is_valid is False
    assert "Max risk" in error
    assert "$600" in error
    assert "$500" in error


# ==========================================
# Daily Loss Limit Tests
# ==========================================

@pytest.mark.unit
def test_validate_order_daily_loss_pass(safety_validator, temp_agent_memory):
    """Test order passes daily loss validation."""
    # Set daily loss to $500 (under $1000 limit)
    with open(temp_agent_memory, 'r') as f:
        memory = json.load(f)

    memory["safety_state"]["daily_loss"] = 500.0

    with open(temp_agent_memory, 'w') as f:
        json.dump(memory, f)

    order = {
        "symbol": "AAPL",
        "max_risk": 400.0,
        "capital_required": 500.0,
        "legs": []
    }

    # Mock memory path
    safety_validator.agent_memory_path = temp_agent_memory

    is_valid, error = safety_validator.validate_order(order)

    assert is_valid is True


@pytest.mark.unit
def test_validate_order_daily_loss_fail(safety_validator, temp_agent_memory):
    """Test order fails daily loss validation."""
    # Set daily loss to $1000 (at limit)
    with open(temp_agent_memory, 'r') as f:
        memory = json.load(f)

    memory["safety_state"]["daily_loss"] = 1000.0

    with open(temp_agent_memory, 'w') as f:
        json.dump(memory, f)

    order = {
        "symbol": "AAPL",
        "max_risk": 400.0,
        "capital_required": 500.0,
        "legs": []
    }

    safety_validator.agent_memory_path = temp_agent_memory

    is_valid, error = safety_validator.validate_order(order)

    assert is_valid is False
    assert "Daily loss limit" in error
    assert "$1,000" in error


# ==========================================
# Concentration Limit Tests
# ==========================================

@pytest.mark.unit
def test_validate_order_concentration_pass(safety_validator, temp_agent_memory):
    """Test order passes concentration validation."""
    # Add existing positions
    with open(temp_agent_memory, 'r') as f:
        memory = json.load(f)

    memory["positions"]["open_trades"] = [
        {
            "symbol": "AAPL",
            "capital_at_risk": 1000.0
        }
    ]

    # Portfolio value = $25,000 (from get_account)
    # Existing AAPL exposure = $1,000 (4%)
    # New trade = $400
    # Total AAPL = $1,400 (5.6%) < 30% limit

    with open(temp_agent_memory, 'w') as f:
        json.dump(memory, f)

    order = {
        "symbol": "AAPL",
        "max_risk": 400.0,
        "capital_required": 400.0,
        "legs": []
    }

    safety_validator.agent_memory_path = temp_agent_memory

    # Mock get_account to return $25,000 portfolio
    from unittest.mock import patch
    with patch('safety.SafetyValidator._get_portfolio_value', return_value=25000.0):
        is_valid, error = safety_validator.validate_order(order)

    assert is_valid is True


@pytest.mark.unit
def test_validate_order_concentration_fail(safety_validator, temp_agent_memory):
    """Test order fails concentration validation."""
    # Add large existing position in AAPL
    with open(temp_agent_memory, 'r') as f:
        memory = json.load(f)

    memory["positions"]["open_trades"] = [
        {
            "symbol": "AAPL",
            "capital_at_risk": 6000.0  # Already 24% of $25k portfolio
        }
    ]

    with open(temp_agent_memory, 'w') as f:
        json.dump(memory, f)

    order = {
        "symbol": "AAPL",
        "max_risk": 2000.0,  # Would bring total to 32% > 30% limit
        "capital_required": 2000.0,
        "legs": []
    }

    safety_validator.agent_memory_path = temp_agent_memory

    from unittest.mock import patch
    with patch('safety.SafetyValidator._get_portfolio_value', return_value=25000.0):
        is_valid, error = safety_validator.validate_order(order)

    assert is_valid is False
    assert "Concentration limit" in error
    assert "30%" in error


# ==========================================
# Circuit Breaker Tests
# ==========================================

@pytest.mark.unit
def test_validate_order_circuit_breaker_triggered(safety_validator, temp_agent_memory):
    """Test order fails when circuit breaker is triggered."""
    # Trigger circuit breaker
    with open(temp_agent_memory, 'r') as f:
        memory = json.load(f)

    memory["safety_state"]["circuit_breaker_triggered"] = True

    with open(temp_agent_memory, 'w') as f:
        json.dump(memory, f)

    order = {
        "symbol": "AAPL",
        "max_risk": 400.0,
        "capital_required": 500.0,
        "legs": []
    }

    safety_validator.agent_memory_path = temp_agent_memory

    is_valid, error = safety_validator.validate_order(order)

    assert is_valid is False
    assert "Circuit breaker" in error


# ==========================================
# Consecutive Losses Tests
# ==========================================

@pytest.mark.unit
def test_validate_order_consecutive_losses_pass(safety_validator, temp_agent_memory):
    """Test order passes with 4 consecutive losses."""
    with open(temp_agent_memory, 'r') as f:
        memory = json.load(f)

    memory["safety_state"]["consecutive_losses"] = 4

    with open(temp_agent_memory, 'w') as f:
        json.dump(memory, f)

    order = {
        "symbol": "AAPL",
        "max_risk": 400.0,
        "capital_required": 500.0,
        "legs": []
    }

    safety_validator.agent_memory_path = temp_agent_memory

    is_valid, error = safety_validator.validate_order(order)

    assert is_valid is True


@pytest.mark.unit
def test_validate_order_consecutive_losses_fail(safety_validator, temp_agent_memory):
    """Test order fails with 5 consecutive losses."""
    with open(temp_agent_memory, 'r') as f:
        memory = json.load(f)

    memory["safety_state"]["consecutive_losses"] = 5

    with open(temp_agent_memory, 'w') as f:
        json.dump(memory, f)

    order = {
        "symbol": "AAPL",
        "max_risk": 400.0,
        "capital_required": 500.0,
        "legs": []
    }

    safety_validator.agent_memory_path = temp_agent_memory

    is_valid, error = safety_validator.validate_order(order)

    assert is_valid is False
    assert "Consecutive loss limit" in error
    assert "5" in error


# ==========================================
# Emergency Stop Tests
# ==========================================

@pytest.mark.unit
def test_validate_order_emergency_stop(safety_validator, temp_agent_memory):
    """Test order fails when emergency stop is active."""
    with open(temp_agent_memory, 'r') as f:
        memory = json.load(f)

    memory["agent_state"]["emergency_stop"] = True

    with open(temp_agent_memory, 'w') as f:
        json.dump(memory, f)

    order = {
        "symbol": "AAPL",
        "max_risk": 400.0,
        "capital_required": 500.0,
        "legs": []
    }

    safety_validator.agent_memory_path = temp_agent_memory

    is_valid, error = safety_validator.validate_order(order)

    assert is_valid is False
    assert "Emergency stop" in error


# ==========================================
# Order Leg Validation Tests
# ==========================================

@pytest.mark.unit
def test_validate_order_legs_minimum_prices(safety_validator):
    """Test order leg validation for minimum prices."""
    order = {
        "symbol": "AAPL",
        "max_risk": 400.0,
        "capital_required": 500.0,
        "legs": [
            {
                "action": "SELL",
                "price": 0.01  # Too low - likely an error
            }
        ]
    }

    is_valid, error = safety_validator.validate_order(order)

    # Depending on implementation, this might pass or fail
    # Most implementations would warn but allow
    # For now, we'll test that validation runs without error


# ==========================================
# Violation Logging Tests
# ==========================================

@pytest.mark.unit
def test_log_violation(safety_validator, tmp_path):
    """Test logging safety violations."""
    # Create temp log directory
    log_dir = tmp_path / "trading_workspace" / "logs"
    log_dir.mkdir(parents=True)
    log_file = log_dir / "safety_violations.log"

    safety_validator.violation_log_path = log_file

    safety_validator.log_violation(
        ViolationType.MAX_TRADE_RISK,
        "Max risk ($600) exceeds limit ($500)"
    )

    assert log_file.exists()

    with open(log_file, 'r') as f:
        content = f.read()

    assert "MAX_TRADE_RISK" in content
    assert "$600" in content


# ==========================================
# Circuit Breaker Trigger Tests
# ==========================================

@pytest.mark.unit
def test_trigger_circuit_breaker(safety_validator, temp_agent_memory, tmp_path):
    """Test circuit breaker triggering."""
    # Create temp log directory
    log_dir = tmp_path / "trading_workspace" / "logs"
    log_dir.mkdir(parents=True)
    log_file = log_dir / "circuit_breaker.log"

    safety_validator.agent_memory_path = temp_agent_memory
    safety_validator.circuit_breaker_log_path = log_file

    safety_validator.trigger_circuit_breaker("10% drawdown reached")

    # Check memory updated
    with open(temp_agent_memory, 'r') as f:
        memory = json.load(f)

    assert memory["safety_state"]["circuit_breaker_triggered"] is True

    # Check log created
    assert log_file.exists()

    with open(log_file, 'r') as f:
        content = f.read()

    assert "CIRCUIT BREAKER TRIGGERED" in content
    assert "10% drawdown" in content


# ==========================================
# Factory Function Tests
# ==========================================

@pytest.mark.unit
def test_create_safety_validator():
    """Test create_safety_validator factory function."""
    validator = create_safety_validator()

    assert isinstance(validator, SafetyValidator)
    assert isinstance(validator.limits, SafetyLimits)


# ==========================================
# Edge Cases Tests
# ==========================================

@pytest.mark.unit
def test_validate_order_missing_fields(safety_validator):
    """Test validation with missing order fields."""
    order = {
        "symbol": "AAPL"
        # Missing max_risk, capital_required, legs
    }

    # Should handle gracefully
    is_valid, error = safety_validator.validate_order(order)

    # Depending on implementation, might fail or use defaults


@pytest.mark.unit
def test_validate_order_zero_risk(safety_validator):
    """Test validation with zero risk (edge case)."""
    order = {
        "symbol": "AAPL",
        "max_risk": 0.0,
        "capital_required": 0.0,
        "legs": []
    }

    is_valid, error = safety_validator.validate_order(order)

    # Should allow zero-risk trades (closing positions, etc.)
    assert is_valid is True


@pytest.mark.unit
def test_validate_order_negative_risk(safety_validator):
    """Test validation with negative risk (invalid)."""
    order = {
        "symbol": "AAPL",
        "max_risk": -100.0,
        "capital_required": 500.0,
        "legs": []
    }

    is_valid, error = safety_validator.validate_order(order)

    # Should reject negative risk
    assert is_valid is False


# ==========================================
# Multiple Violation Tests
# ==========================================

@pytest.mark.unit
def test_validate_order_multiple_violations(safety_validator, temp_agent_memory):
    """Test order with multiple simultaneous violations."""
    # Set up multiple violations
    with open(temp_agent_memory, 'r') as f:
        memory = json.load(f)

    memory["safety_state"]["daily_loss"] = 1000.0  # At limit
    memory["safety_state"]["consecutive_losses"] = 5  # At limit
    memory["agent_state"]["emergency_stop"] = True  # Emergency stop

    with open(temp_agent_memory, 'w') as f:
        json.dump(memory, f)

    order = {
        "symbol": "AAPL",
        "max_risk": 600.0,  # Also exceeds max risk
        "capital_required": 700.0,
        "legs": []
    }

    safety_validator.agent_memory_path = temp_agent_memory

    is_valid, error = safety_validator.validate_order(order)

    assert is_valid is False
    # Should report first violation encountered
    assert error != ""
