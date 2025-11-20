"""
Unit tests for skills library.
"""

import pytest
from skills import kelly_criterion, black_scholes_iv, OrderResult


class TestMathCore:
    """Tests for math_core skill functions."""

    def test_kelly_criterion_basic(self):
        """Test basic Kelly criterion calculation."""
        position_size = kelly_criterion(
            win_prob=0.6,
            win_amount=500,
            loss_amount=200,
            bankroll=10000,
            fraction=0.25
        )

        assert position_size > 0
        assert position_size < 10000  # Should not exceed bankroll

    def test_kelly_criterion_never_negative(self):
        """Kelly should never return negative position."""
        position_size = kelly_criterion(
            win_prob=0.3,  # Low win probability
            win_amount=100,
            loss_amount=500,
            bankroll=10000,
            fraction=0.25
        )

        assert position_size >= 0

    def test_black_scholes_iv_convergence(self):
        """Test IV calculation converges for reasonable inputs."""
        iv = black_scholes_iv(
            option_price=5.50,
            spot=100,
            strike=105,
            time_to_expiry=0.25,
            rate=0.05,
            is_call=True
        )

        assert iv is not None
        assert 0 < iv < 2.0  # Reasonable IV range


class TestExecutionGate:
    """Tests for execution_gate skill."""

    def test_order_result_structure(self):
        """Test OrderResult dataclass."""
        result = OrderResult(
            success=True,
            trade_id=123,
            message="Order placed"
        )

        assert result.success is True
        assert result.trade_id == 123
        assert result.error is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
