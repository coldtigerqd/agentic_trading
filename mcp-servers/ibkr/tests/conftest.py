"""
Pytest configuration and shared fixtures for IBKR MCP server tests.
"""

import pytest
import asyncio
from unittest.mock import Mock, MagicMock, AsyncMock
from pathlib import Path
import json
import tempfile
from datetime import datetime

# Import modules under test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from connection import IBKRConnectionManager, ConnectionMode
from tools import IBKRTools
from safety import SafetyValidator, SafetyLimits


# ==========================================
# Fixtures - Mock IBKR Client
# ==========================================

@pytest.fixture
def mock_ib():
    """Mock ib_insync IB client."""
    ib = MagicMock()
    ib.isConnected.return_value = True
    ib.accountValues.return_value = []
    ib.portfolio.return_value = []
    ib.openTrades.return_value = []
    return ib


@pytest.fixture
def mock_account_values():
    """Mock IBKR account values."""
    class MockAccountValue:
        def __init__(self, tag, value, currency="USD", account="DU1234567"):
            self.tag = tag
            self.value = value
            self.currency = currency
            self.account = account

    return [
        MockAccountValue("NetLiquidation", "25000.00"),
        MockAccountValue("TotalCashValue", "15000.00"),
        MockAccountValue("BuyingPower", "50000.00"),
        MockAccountValue("UnrealizedPnL", "250.00"),
        MockAccountValue("RealizedPnL", "1500.00"),
    ]


@pytest.fixture
def mock_portfolio_items():
    """Mock IBKR portfolio items."""
    class MockContract:
        def __init__(self, symbol, secType="OPT", strike=None, right=None, expiry=None):
            self.symbol = symbol
            self.secType = secType
            self.strike = strike
            self.right = right
            self.lastTradeDateOrContractMonth = expiry

    class MockPortfolioItem:
        def __init__(self, symbol, position, avgCost, marketPrice, marketValue, unrealizedPNL, realizedPNL, **kwargs):
            self.contract = MockContract(symbol, **kwargs)
            self.position = position
            self.averageCost = avgCost
            self.marketPrice = marketPrice
            self.marketValue = marketValue
            self.unrealizedPNL = unrealizedPNL
            self.realizedPNL = realizedPNL

    return [
        MockPortfolioItem(
            symbol="AAPL",
            secType="OPT",
            strike=175.0,
            right="P",
            expiry="20251123",
            position=-1,
            avgCost=1.25,
            marketPrice=1.50,
            marketValue=-150.00,
            unrealizedPNL=-25.00,
            realizedPNL=0.0
        ),
        MockPortfolioItem(
            symbol="AAPL",
            secType="OPT",
            strike=170.0,
            right="P",
            expiry="20251123",
            position=1,
            avgCost=0.80,
            marketPrice=0.60,
            marketValue=60.00,
            unrealizedPNL=20.00,
            realizedPNL=0.0
        ),
    ]


@pytest.fixture
def mock_trade():
    """Mock IBKR Trade object."""
    class MockOrder:
        def __init__(self):
            self.orderId = 100001
            self.orderType = "LMT"
            self.action = "SELL"
            self.totalQuantity = 1

    class MockTrade:
        def __init__(self):
            self.order = MockOrder()
            self.orderStatus = MagicMock()
            self.orderStatus.status = "Submitted"

    return MockTrade()


# ==========================================
# Fixtures - Connection Manager
# ==========================================

@pytest.fixture
def connection_manager(monkeypatch, mock_ib):
    """
    Connection manager with mocked IB client.

    This fixture patches the IB class to return a mock instead of
    creating a real IBKR connection.
    """
    # Reset singleton
    IBKRConnectionManager._instance = None

    # Mock the IB class
    from ib_insync import IB
    monkeypatch.setattr("connection.IB", lambda: mock_ib)

    manager = IBKRConnectionManager()
    manager.ib = mock_ib
    manager.is_connected = True
    manager.mode = ConnectionMode.PAPER_TWS

    return manager


# ==========================================
# Fixtures - IBKRTools
# ==========================================

@pytest.fixture
def ibkr_tools(connection_manager, monkeypatch):
    """IBKRTools instance with mocked connection."""
    # Prevent actual connection attempt
    monkeypatch.setattr(IBKRTools, "_ensure_connected", lambda self: None)

    tools = IBKRTools(connection_mode=ConnectionMode.PAPER_TWS)
    tools.connection_manager = connection_manager

    return tools


# ==========================================
# Fixtures - Safety Validator
# ==========================================

@pytest.fixture
def safety_validator():
    """Safety validator instance."""
    return SafetyValidator()


@pytest.fixture
def safety_limits():
    """Safety limits instance."""
    return SafetyLimits()


# ==========================================
# Fixtures - Agent Memory
# ==========================================

@pytest.fixture
def temp_agent_memory():
    """Temporary agent memory file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        memory = {
            "version": "1.0.0",
            "agent_state": {
                "mode": "shadow",
                "cycle_count": 0,
                "emergency_stop": False
            },
            "positions": {
                "open_trades": [],
                "closed_trades_count": 0,
                "total_p_l": 0.0
            },
            "safety_state": {
                "daily_loss": 0.0,
                "daily_loss_limit": 1000.0,
                "circuit_breaker_triggered": False,
                "consecutive_losses": 0
            },
            "performance_metrics": {
                "total_trades": 0,
                "profitable_trades": 0,
                "win_rate": 0.0,
                "sharpe_ratio": 0.0,
                "max_drawdown": 0.0
            }
        }
        json.dump(memory, f)
        temp_path = Path(f.name)

    yield temp_path

    # Cleanup
    if temp_path.exists():
        temp_path.unlink()


# ==========================================
# Fixtures - Sample Orders
# ==========================================

@pytest.fixture
def sample_iron_condor_order():
    """Sample Iron Condor order for testing."""
    return {
        "symbol": "AAPL",
        "strategy": "Iron Condor",
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
            },
            {
                "action": "BUY",
                "contract": {
                    "symbol": "AAPL",
                    "expiry": "2025-11-23",
                    "strike": 170.0,
                    "right": "P"
                },
                "quantity": 1,
                "price": 0.80
            },
            {
                "action": "SELL",
                "contract": {
                    "symbol": "AAPL",
                    "expiry": "2025-11-23",
                    "strike": 186.0,
                    "right": "C"
                },
                "quantity": 1,
                "price": 1.40
            },
            {
                "action": "BUY",
                "contract": {
                    "symbol": "AAPL",
                    "expiry": "2025-11-23",
                    "strike": 191.0,
                    "right": "C"
                },
                "quantity": 1,
                "price": 0.75
            }
        ],
        "max_risk": 365.0,
        "capital_required": 500.0
    }


@pytest.fixture
def sample_credit_spread_order():
    """Sample Credit Spread order for testing."""
    return {
        "symbol": "TSLA",
        "strategy": "Put Credit Spread",
        "legs": [
            {
                "action": "SELL",
                "contract": {
                    "symbol": "TSLA",
                    "expiry": "2025-12-15",
                    "strike": 200.0,
                    "right": "P"
                },
                "quantity": 1,
                "price": 3.50
            },
            {
                "action": "BUY",
                "contract": {
                    "symbol": "TSLA",
                    "expiry": "2025-12-15",
                    "strike": 195.0,
                    "right": "P"
                },
                "quantity": 1,
                "price": 2.00
            }
        ],
        "max_risk": 350.0,
        "capital_required": 500.0
    }


# ==========================================
# Event Loop Fixture
# ==========================================

@pytest.fixture(scope="function")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# ==========================================
# Pytest Configuration
# ==========================================

def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "unit: Unit tests with mocked dependencies")
    config.addinivalue_line("markers", "integration: Integration tests with real IBKR")
    config.addinivalue_line("markers", "slow: Slow tests (> 1 second)")
    config.addinivalue_line("markers", "performance: Performance and memory tests")
