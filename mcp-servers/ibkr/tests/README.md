# IBKR MCP Server Test Suite

Comprehensive test suite for the Interactive Brokers (IBKR) MCP server, providing unit tests, integration tests, performance tests, and edge case coverage.

## Test Structure

```
tests/
├── __init__.py              # Test package initialization
├── conftest.py              # Shared pytest fixtures and configuration
├── pytest.ini               # Pytest configuration
├── test_connection.py       # Connection manager tests (30+ test cases)
├── test_tools.py            # MCP tools tests (25+ test cases)
├── test_safety.py           # Safety layer tests (25+ test cases)
├── test_integration.py      # Integration and performance tests (20+ test cases)
└── README.md                # This file
```

## Quick Start

### Install Test Dependencies

```bash
pip install pytest pytest-asyncio pytest-cov pytest-mock
```

### Run All Unit Tests

```bash
cd mcp-servers/ibkr
pytest -m unit
```

### Run All Tests (Unit + Integration + Performance)

```bash
pytest
```

### Run with Coverage Report

```bash
pytest --cov=. --cov-report=html
```

The HTML coverage report will be available at `htmlcov/index.html`.

## Test Markers

The test suite uses custom pytest markers to categorize tests:

| Marker | Description | Usage |
|--------|-------------|-------|
| `@pytest.mark.unit` | Unit tests with mocked dependencies | Fast tests for CI/CD |
| `@pytest.mark.integration` | Integration tests with real IBKR | Requires IBKR TWS/Gateway |
| `@pytest.mark.slow` | Tests that take > 1 second | Often performance tests |
| `@pytest.mark.performance` | Performance and memory tests | Memory leak detection, etc. |

### Running Specific Test Categories

```bash
# Only unit tests (fastest, no external dependencies)
pytest -m unit

# Only integration tests (requires IBKR paper trading)
pytest -m integration

# Only performance tests
pytest -m performance

# Exclude slow tests
pytest -m "not slow"

# Unit tests excluding slow ones
pytest -m "unit and not slow"
```

## Test Coverage

### 1. Connection Manager Tests (`test_connection.py`)

**30+ test cases covering:**
- ✅ Singleton pattern validation
- ✅ Connection to different modes (PAPER_TWS, PAPER_GATEWAY, LIVE_TWS, LIVE_GATEWAY)
- ✅ Connection failure handling
- ✅ Disconnection and cleanup
- ✅ Automatic reconnection with max retry limits
- ✅ Health checks (healthy, disconnected, unhealthy states)
- ✅ Account operations (`get_account_values`, `get_portfolio_items`)
- ✅ Order operations (`place_order`, `cancel_order`, `get_open_trades`)
- ✅ Market data retrieval (`get_current_price`)
- ✅ Event handlers (`_on_connected`, `_on_disconnected`, `_on_error`)
- ✅ Connection mode configurations

**Example:**
```bash
pytest tests/test_connection.py -v
```

### 2. MCP Tools Tests (`test_tools.py`)

**25+ test cases covering all 6 MCP tools:**
- ✅ Tool metadata validation (proper JSON schemas)
- ✅ `get_account()` - success and error handling
- ✅ `get_positions()` - all positions, filtered, empty
- ✅ `place_order()` - multi-leg orders, safety rejection, execution failures
- ✅ `close_position()` - success and position not found
- ✅ `get_order_status()` - status retrieval
- ✅ `health_check()` - healthy and error states
- ✅ Contract creation (options and stocks)
- ✅ Order creation (limit and market orders)
- ✅ Connection management (`_ensure_connected`)

**Example:**
```bash
pytest tests/test_tools.py::test_get_account_success -v
```

### 3. Safety Layer Tests (`test_safety.py`)

**25+ test cases covering all safety validations:**
- ✅ Safety limits defaults
- ✅ Max trade risk validation ($500 limit)
- ✅ Daily loss limit validation ($1,000 limit)
- ✅ Concentration limit validation (30% max per symbol)
- ✅ Circuit breaker triggering (10% drawdown)
- ✅ Consecutive loss limit (5 losses)
- ✅ Emergency stop enforcement
- ✅ Order leg validation
- ✅ Violation logging
- ✅ Edge cases (missing fields, zero risk, negative risk)
- ✅ Multiple simultaneous violations

**Example:**
```bash
pytest tests/test_safety.py::test_validate_order_max_risk_fail -v
```

### 4. Integration & Performance Tests (`test_integration.py`)

**20+ test cases covering:**
- ✅ Multi-leg order execution:
  - Iron Condor (4 legs)
  - Credit Spreads (2 legs)
  - Partial leg failures
- ✅ Error handling:
  - Connection loss during execution
  - Invalid contract data
  - API rate limiting (pacing violations)
  - Market closed errors
- ✅ Edge cases:
  - Empty legs array
  - Single leg orders
  - Very large orders (10+ legs)
- ✅ Performance tests:
  - 50+ consecutive API calls without memory leak
  - Position retrieval with 100+ items
  - Concurrent health checks (deadlock detection)
- ✅ Integration tests (skipped by default):
  - Real IBKR paper trading connection
  - Account data retrieval
  - Position data retrieval

**Example:**
```bash
# Run all integration tests (unit tests only by default)
pytest tests/test_integration.py -m unit -v

# Run performance tests
pytest tests/test_integration.py -m performance -v

# Run real IBKR integration tests (requires TWS/Gateway)
pytest tests/test_integration.py -m integration -v
```

## Integration Tests (Real IBKR Connection)

Integration tests are marked with `@pytest.mark.integration` and **skipped by default**. They require:

1. **IBKR TWS or Gateway** running locally
2. **Paper trading account** enabled
3. **API enabled** on the appropriate port:
   - TWS Paper Trading: `localhost:7497`
   - Gateway Paper Trading: `localhost:4002`

### Setup for Integration Tests

1. Start IBKR TWS or Gateway
2. Enable API connections:
   - TWS: File → Global Configuration → API → Settings
   - Check "Enable ActiveX and Socket Clients"
   - Uncheck "Read-Only API" for testing
3. Note your client ID (default is usually 0 or 1)

### Run Integration Tests

```bash
# Run integration tests (will attempt real IBKR connection)
pytest -m integration -v

# Run ALL tests including integration
pytest -v
```

**Note:** Integration tests will fail if IBKR is not running. Remove the `pytest.skip()` call in each integration test to enable them.

## Performance Tests

Performance tests validate:
- **Memory leak detection**: 50+ consecutive API calls should not increase memory by more than 1 MB
- **Execution time**: Operations should complete within specified time limits
- **Concurrency**: Multiple operations should not deadlock

### Run Performance Tests

```bash
pytest -m performance -v
```

### Memory Leak Test Example

```python
@pytest.mark.performance
@pytest.mark.slow
def test_50_consecutive_api_calls(ibkr_tools, mock_account_values):
    """Test 50+ consecutive API calls without memory leak."""
    tracemalloc.start()
    gc.collect()
    snapshot_start = tracemalloc.take_snapshot()

    # Perform 50 API calls
    for i in range(50):
        account = ibkr_tools.get_account()
        assert "net_liquidation" in account

    gc.collect()
    snapshot_end = tracemalloc.take_snapshot()
    top_stats = snapshot_end.compare_to(snapshot_start, 'lineno')
    total_diff = sum(stat.size_diff for stat in top_stats)
    tracemalloc.stop()

    # Assert memory increase < 1 MB
    assert total_diff < 1024 * 1024
```

## Test Fixtures

Shared fixtures are defined in `conftest.py`:

| Fixture | Description |
|---------|-------------|
| `mock_ib` | Mock ib_insync IB client |
| `mock_account_values` | Mock IBKR account values |
| `mock_portfolio_items` | Mock IBKR portfolio items with options |
| `mock_trade` | Mock IBKR Trade object |
| `connection_manager` | Connection manager with mocked IB client |
| `ibkr_tools` | IBKRTools instance with mocked connection |
| `safety_validator` | SafetyValidator instance |
| `safety_limits` | SafetyLimits instance |
| `temp_agent_memory` | Temporary agent memory file |
| `sample_iron_condor_order` | Sample 4-leg Iron Condor order |
| `sample_credit_spread_order` | Sample 2-leg Credit Spread order |
| `event_loop` | Async event loop for async tests |

## Common Testing Scenarios

### Test a Multi-Leg Order

```python
def test_iron_condor_execution(ibkr_tools, sample_iron_condor_order):
    ibkr_tools.safety.validate_order = Mock(return_value=(True, ""))

    with patch('asyncio.run', return_value=mock_trade):
        result = ibkr_tools.place_order(
            symbol=sample_iron_condor_order["symbol"],
            strategy=sample_iron_condor_order["strategy"],
            legs=sample_iron_condor_order["legs"],
            max_risk=sample_iron_condor_order["max_risk"],
            capital_required=sample_iron_condor_order["capital_required"]
        )

    assert result["success"] is True
    assert len(result["order_ids"]) == 4  # 4 legs
```

### Test Safety Layer Rejection

```python
def test_safety_rejection(ibkr_tools, sample_iron_condor_order):
    # Mock safety to reject order
    ibkr_tools.safety.validate_order = Mock(
        return_value=(False, "Max risk exceeds limit")
    )

    result = ibkr_tools.place_order(
        symbol=sample_iron_condor_order["symbol"],
        strategy=sample_iron_condor_order["strategy"],
        legs=sample_iron_condor_order["legs"],
        max_risk=600.0,  # Exceeds $500 limit
        capital_required=sample_iron_condor_order["capital_required"]
    )

    assert result["success"] is False
    assert "safety layer" in result["message"].lower()
```

### Test Error Handling

```python
def test_connection_error_handling(ibkr_tools):
    with patch.object(ibkr_tools, '_ensure_connected',
                     side_effect=ConnectionError("Not connected")):
        with pytest.raises(ConnectionError):
            ibkr_tools.get_account()
```

## Coverage Requirements

The test suite enforces **minimum 80% code coverage** via `pytest.ini`:

```ini
--cov-fail-under=80
```

To generate a detailed coverage report:

```bash
pytest --cov=. --cov-report=term-missing --cov-report=html
```

View the HTML report:

```bash
open htmlcov/index.html
```

## Continuous Integration

For CI/CD pipelines, use:

```bash
# Fast unit tests only (no integration, no slow tests)
pytest -m "unit and not slow" --cov=. --cov-report=xml

# All tests with coverage
pytest --cov=. --cov-report=xml --cov-fail-under=80
```

## Debugging Tests

### Run a Single Test

```bash
pytest tests/test_tools.py::test_get_account_success -v
```

### Run Tests with Print Statements

```bash
pytest tests/test_tools.py -v -s
```

### Run Tests with Detailed Output

```bash
pytest tests/test_tools.py -vv
```

### Run Tests and Drop into Debugger on Failure

```bash
pytest tests/test_tools.py --pdb
```

## Test Data

### Sample Iron Condor Order

```json
{
  "symbol": "AAPL",
  "strategy": "Iron Condor",
  "legs": [
    {
      "action": "SELL",
      "contract": {"symbol": "AAPL", "expiry": "2025-11-23", "strike": 175.0, "right": "P"},
      "quantity": 1,
      "price": 1.50
    },
    {
      "action": "BUY",
      "contract": {"symbol": "AAPL", "expiry": "2025-11-23", "strike": 170.0, "right": "P"},
      "quantity": 1,
      "price": 0.80
    },
    {
      "action": "SELL",
      "contract": {"symbol": "AAPL", "expiry": "2025-11-23", "strike": 186.0, "right": "C"},
      "quantity": 1,
      "price": 1.40
    },
    {
      "action": "BUY",
      "contract": {"symbol": "AAPL", "expiry": "2025-11-23", "strike": 191.0, "right": "C"},
      "quantity": 1,
      "price": 0.75
    }
  ],
  "max_risk": 365.0,
  "capital_required": 500.0
}
```

### Safety Limits

```python
MAX_TRADE_RISK = 500.0          # Max $500 risk per trade
MAX_TRADE_CAPITAL = 2000.0      # Max $2,000 capital per trade
DAILY_LOSS_LIMIT = 1000.0       # Max $1,000 loss per day
MAX_DAILY_TRADES = 10           # Max 10 trades per day
MAX_CONCENTRATION = 0.30        # Max 30% portfolio in one symbol
DRAWDOWN_CIRCUIT_BREAKER = 0.10 # 10% drawdown triggers circuit breaker
CONSECUTIVE_LOSS_LIMIT = 5      # Max 5 consecutive losses
```

## Troubleshooting

### Import Errors

If you see import errors, ensure you're running tests from the correct directory:

```bash
cd mcp-servers/ibkr
pytest
```

### Async Test Failures

If async tests fail, ensure `pytest-asyncio` is installed:

```bash
pip install pytest-asyncio
```

### Mock Issues

If mocks aren't working as expected, verify the patch path matches the import path in the module under test.

**Example:**
```python
# If tools.py imports: from connection import IBKRConnectionManager
# Then patch should be:
with patch('tools.IBKRConnectionManager'):
    ...
```

### Integration Test Skipping

Integration tests are skipped by default. To enable them, remove or comment out the `pytest.skip()` line:

```python
@pytest.mark.integration
@pytest.mark.slow
def test_real_ibkr_connection():
    # pytest.skip("Integration test - requires real IBKR connection")  # Remove this
    ...
```

## Contributing

When adding new tests:

1. **Add appropriate markers**: `@pytest.mark.unit`, `@pytest.mark.integration`, etc.
2. **Use existing fixtures** from `conftest.py` when possible
3. **Follow naming convention**: `test_<feature>_<scenario>`
4. **Document test purpose** with clear docstrings
5. **Keep tests isolated**: Each test should be independent
6. **Mock external dependencies**: Unit tests should not require IBKR connection

## Test Statistics

- **Total Test Files**: 4
- **Total Test Cases**: 80+
- **Total Lines of Test Code**: 1,910+
- **Test Categories**: Unit, Integration, Performance, Edge Cases
- **Coverage Target**: 80%+

## License

Part of the AlphaHive trading system. See main project LICENSE.
