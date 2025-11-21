#!/usr/bin/env python3
"""
Integration tests for swarm intelligence execution.

Tests the full cycle: load instances → execute concurrently → parse signals → create snapshots
"""

import pytest
import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, patch, MagicMock

# Import skills
from skills.swarm_core import (
    load_instances,
    load_template,
    render_template,
    consult_swarm,
    parse_signal
)
from data_lake.snapshot_manager import list_snapshots


@pytest.fixture
def mock_market_data():
    """Provide sample market data for testing"""
    return {
        "timestamp": "2025-11-21T10:00:00",
        "symbols": {
            "NVDA": {"price": 495.20, "iv_rank": 85, "volume": 50000000},
            "AMD": {"price": 145.30, "iv_rank": 78, "volume": 30000000},
            "TSLA": {"price": 242.80, "iv_rank": 92, "volume": 120000000}
        },
        "SPY": {"price": 568.50, "trend": "bullish"}
    }


@pytest.fixture
def mock_llm_response():
    """Mock LLM API response with valid signal"""
    return {
        "signal": "SHORT_PUT_SPREAD",
        "target": "NVDA",
        "reasoning": "High IV rank (85%) suggests premium selling opportunity. Bullish market trend supports downside protection.",
        "params": {
            "strike_short": 490,
            "strike_long": 485,
            "expiry": "2025-12-20",
            "max_risk": 500,
            "capital_required": 500
        },
        "confidence": 0.82
    }


class TestSwarmInstanceLoading:
    """Test swarm configuration loading"""

    def test_load_all_instances(self):
        """Should load all active instance configurations"""
        instances = load_instances()
        assert len(instances) >= 2, "Expected at least 2 active instances"

        # Verify required fields
        for instance in instances:
            assert "id" in instance
            assert "template" in instance
            assert "parameters" in instance

    def test_load_specific_template(self):
        """Should load and validate template content"""
        template = load_template("vol_sniper.md")

        # Check for key sections
        assert "Volatility Sniper" in template
        assert "{{ symbol_pool }}" in template or "symbol_pool" in template
        assert "signal" in template.lower()

    def test_template_rendering(self):
        """Should render template with Jinja2 parameters"""
        template = load_template("vol_sniper.md")

        params = {
            "symbol_pool": ["NVDA", "AMD"],
            "min_iv_rank": 80,
            "max_delta_exposure": 0.30,
            "sentiment_filter": "neutral_or_better"
        }

        rendered = render_template(template, params)

        # Verify parameters were injected
        assert "NVDA" in rendered or "AMD" in rendered
        assert "{{ symbol_pool }}" not in rendered  # No unrendered placeholders


class TestSwarmExecution:
    """Test concurrent swarm execution"""

    @pytest.mark.asyncio
    async def test_concurrent_execution_mock(self, mock_market_data, mock_llm_response):
        """Should execute multiple instances concurrently with mocked LLM"""

        # Mock the LLM API call
        with patch('skills.swarm_core.call_llm_api', new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = mock_llm_response

            # Run swarm consultation
            signals = await consult_swarm(
                sector="TECH",
                market_data=mock_market_data,
                max_concurrent=5
            )

            # Verify signals returned
            assert isinstance(signals, list)
            assert len(signals) > 0

            # Verify signal structure
            for signal in signals:
                assert "instance_id" in signal
                assert "target" in signal
                assert "signal" in signal
                assert "confidence" in signal
                assert 0 <= signal["confidence"] <= 1

    def test_signal_parsing(self, mock_llm_response):
        """Should correctly parse LLM response into signal structure"""
        signal = parse_signal(
            raw_response=mock_llm_response,
            instance_id="tech_aggressive"
        )

        assert signal["target"] == "NVDA"
        assert signal["signal"] == "SHORT_PUT_SPREAD"
        assert signal["confidence"] == 0.82
        assert "params" in signal


class TestSwarmSnapshots:
    """Test snapshot creation during swarm execution"""

    @pytest.mark.asyncio
    async def test_snapshots_created(self, mock_market_data, mock_llm_response):
        """Should create snapshots for each swarm invocation"""

        with patch('skills.swarm_core.call_llm_api', new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = mock_llm_response

            # Clear old snapshots for this test
            snapshot_dir = Path.home() / "trading_workspace" / "snapshots"
            if snapshot_dir.exists():
                initial_count = len(list(snapshot_dir.glob("*.json")))
            else:
                initial_count = 0

            # Run swarm
            await consult_swarm(sector="TECH", market_data=mock_market_data)

            # Verify snapshots increased
            if snapshot_dir.exists():
                final_count = len(list(snapshot_dir.glob("*.json")))
                assert final_count > initial_count, "Snapshots should be created"


class TestSwarmErrorHandling:
    """Test error handling in swarm execution"""

    @pytest.mark.asyncio
    async def test_timeout_handling(self, mock_market_data):
        """Should handle LLM API timeouts gracefully"""

        async def slow_llm(*args, **kwargs):
            await asyncio.sleep(10)  # Simulate timeout
            return {}

        with patch('skills.swarm_core.call_llm_api', new=slow_llm):
            with pytest.raises(asyncio.TimeoutError):
                await consult_swarm(
                    sector="TECH",
                    market_data=mock_market_data,
                    timeout=1  # 1 second timeout
                )

    @pytest.mark.asyncio
    async def test_partial_failure_handling(self, mock_market_data, mock_llm_response):
        """Should continue execution if some instances fail"""

        call_count = 0

        async def flaky_llm(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count % 2 == 0:
                raise Exception("API error")
            return mock_llm_response

        with patch('skills.swarm_core.call_llm_api', new=flaky_llm):
            signals = await consult_swarm(sector="TECH", market_data=mock_market_data)

            # Should get some signals despite failures
            assert len(signals) > 0


class TestSwarmDeduplication:
    """Test signal deduplication logic"""

    def test_duplicate_signals_removed(self):
        """Should remove duplicate signals for same target"""
        from skills.swarm_core import deduplicate_signals

        signals = [
            {"instance_id": "a", "target": "NVDA", "signal": "PUT_SPREAD", "confidence": 0.75},
            {"instance_id": "b", "target": "NVDA", "signal": "PUT_SPREAD", "confidence": 0.82},  # Higher confidence
            {"instance_id": "c", "target": "AMD", "signal": "CALL_SPREAD", "confidence": 0.70}
        ]

        deduped = deduplicate_signals(signals)

        # Should keep only highest confidence NVDA signal
        assert len(deduped) == 2
        nvda_signals = [s for s in deduped if s["target"] == "NVDA"]
        assert len(nvda_signals) == 1
        assert nvda_signals[0]["instance_id"] == "b"  # Higher confidence


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
