# IBKR MCP Server

MCP (Model Context Protocol) server for Interactive Brokers trading operations with built-in safety layer.

## Overview

This MCP server exposes IBKR trading functionality to Claude Code agent runtime. All trading operations are validated against hard-coded safety limits to prevent catastrophic errors.

## Features

- **Real IBKR Integration**: Live connection to IBKR TWS/Gateway via ib_insync
- **Safety Layer**: Hard-coded limits on trade risk, daily losses, concentration, and drawdowns
- **Multi-Leg Orders**: Support for complex options strategies (Iron Condors, spreads, etc.)
- **Circuit Breakers**: Automatic trading suspension on excessive losses
- **Trade Logging**: Complete audit trail of all trading decisions and executions
- **Position Management**: Real-time position tracking and P&L monitoring
- **Health Monitoring**: Connection health checks and automatic reconnection
- **Paper & Live Trading**: Supports both paper and live trading modes

## Prerequisites

### 1. Interactive Brokers Account

You need an IBKR account with API access:
- **Paper Trading Account** (recommended for testing): Free, no risk
- **Live Trading Account**: Real money (use after thorough testing)

### 2. IBKR TWS or Gateway

Download and install **Trader Workstation (TWS)** or **IB Gateway**:

- **TWS (Full Platform)**: https://www.interactivebrokers.com/en/trading/tws.php
- **Gateway (API-only)**: https://www.interactivebrokers.com/en/trading/ibgateway-stable.php
- **Paper Trading Version**: Use paper trading version for testing

### 3. Python Dependencies

```bash
pip install ib-insync>=0.9.86 mcp>=0.9.0
```

## Setup Instructions

### Step 1: Configure IBKR TWS/Gateway

1. **Launch TWS or Gateway** (paper trading version for testing)

2. **Enable API Access**:
   - In TWS: `File > Global Configuration > API > Settings`
   - In Gateway: Click on settings icon

3. **Configure API Settings**:
   - ✅ Enable "ActiveX and Socket Clients"
   - ✅ Set Socket Port:
     - **Paper TWS**: 7497
     - **Live TWS**: 7496
     - **Paper Gateway**: 4002
     - **Live Gateway**: 4001
   - ✅ Add "127.0.0.1" to "Trusted IP Addresses"
   - ⚠️ For testing, you may enable "Read-Only API"
   - ❌ Do NOT check "Allow connections from localhost only" if running remotely

4. **Restart TWS/Gateway** after changes

### Step 2: Test Connection

Test the connection using Python:

```python
from ib_insync import IB

ib = IB()
ib.connect('localhost', 7497, clientId=1)  # Paper TWS

print(f"Connected: {ib.isConnected()}")
print(f"Account: {ib.accountValues()[:3]}")  # Show first 3 values

ib.disconnect()
```

If this works, you're ready!

### Step 3: Configure MCP Server

Add to Claude Code config (`~/.config/claude/config.json`):

```json
{
  "mcpServers": {
    "ibkr": {
      "command": "python",
      "args": ["/home/adt/project/trade/mcp-servers/ibkr/server.py"],
      "env": {
        "IBKR_MODE": "paper_gateway",
        "IBKR_CLIENT_ID": "1"
      }
    }
  }
}
```

**Connection Modes**:
- `paper_tws`: Paper Trading TWS (port 7497) - **RECOMMENDED**
- `paper_gateway`: Paper Trading Gateway (port 4002)
- `live_tws`: Live Trading TWS (port 7496) ⚠️
- `live_gateway`: Live Trading Gateway (port 4001) ⚠️

### Step 4: Start Trading Agent

```bash
# Shadow Mode (human approval for each trade)
./trade_agent.sh --shadow-mode

# Live Mode (autonomous trading)
./trade_agent.sh --live-mode
```

## Safety Limits

The following safety limits are enforced (defined in `safety.py`):

| Limit | Value | Description |
|-------|-------|-------------|
| MAX_TRADE_RISK | $500 | Maximum risk per single trade |
| DAILY_LOSS_LIMIT | $1,000 | Maximum daily loss before shutdown |
| MAX_CONCENTRATION | 30% | Maximum portfolio allocation to single symbol |
| DRAWDOWN_CIRCUIT_BREAKER | 10% | Stop trading at 10% account drawdown |
| CONSECUTIVE_LOSS_LIMIT | 5 | Stop after 5 consecutive losses |

**WARNING**: These limits are intentionally conservative. DO NOT modify without human approval.

## Available Tools

### `get_account()`
Get account information including balance, buying power, and P&L.

**Returns**:
```json
{
  "account_id": "U1234567",
  "net_liquidation": 25000.00,
  "cash_balance": 15000.00,
  "buying_power": 25000.00,
  "total_positions_value": 10000.00,
  "unrealized_pnl": 250.00,
  "realized_pnl": 1500.00
}
```

### `get_positions(symbol?: string)`
Get current open positions, optionally filtered by symbol.

**Parameters**:
- `symbol` (optional): Filter positions by underlying symbol

**Returns**:
```json
[
  {
    "symbol": "AAPL",
    "quantity": 1,
    "avg_cost": 175.00,
    "current_price": 180.00,
    "market_value": 180.00,
    "unrealized_pnl": 5.00,
    "unrealized_pnl_percent": 2.86
  }
]
```

### `place_order(symbol, strategy, legs, max_risk, capital_required, metadata?)`
Place a multi-leg options order with safety validation.

**Parameters**:
- `symbol`: Underlying symbol (e.g., "AAPL")
- `strategy`: Strategy name (e.g., "Iron Condor")
- `legs`: Array of order legs (see example below)
- `max_risk`: Maximum risk for this trade ($)
- `capital_required`: Capital required for this trade ($)
- `metadata` (optional): Additional context (agent reasoning, confidence, etc.)

**Example**:
```json
{
  "symbol": "AAPL",
  "strategy": "Iron Condor",
  "legs": [
    {
      "action": "SELL",
      "contract": {
        "symbol": "AAPL",
        "expiry": "2025-11-23",
        "strike": 175,
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
        "strike": 170,
        "right": "P"
      },
      "quantity": 1,
      "price": 0.80
    }
  ],
  "max_risk": 450.00,
  "capital_required": 500.00
}
```

**Returns**:
```json
{
  "success": true,
  "order_ids": [100001, 100002, 100003, 100004],
  "trade_id": "IRON_CONDOR_AAPL_20251119_103045",
  "message": "Order placed successfully",
  "timestamp": "2025-11-19T10:30:45Z"
}
```

### `close_position(trade_id)`
Close an existing position by trade ID.

**Parameters**:
- `trade_id`: Trade ID from `place_order` response

**Returns**:
```json
{
  "success": true,
  "trade_id": "IRON_CONDOR_AAPL_20251119_103045",
  "close_order_ids": [200001, 200002],
  "realized_pnl": 125.50,
  "message": "Position closed successfully"
}
```

### `get_order_status(order_id)`
Get status of a specific order by order ID.

**Parameters**:
- `order_id`: IBKR order ID

**Returns**:
```json
{
  "order_id": 100001,
  "status": "Filled",
  "filled_quantity": 1,
  "avg_fill_price": 1.25,
  "timestamp": "2025-11-19T10:30:50Z"
}
```

## Usage

### Starting the Server

```bash
cd mcp-servers/ibkr
python server.py
```

The server listens on stdio for MCP protocol messages.

### Configuration

Add to your Claude Code MCP configuration:

```json
{
  "mcpServers": {
    "ibkr": {
      "command": "python",
      "args": ["/path/to/mcp-servers/ibkr/server.py"],
      "env": {
        "IBKR_HOST": "127.0.0.1",
        "IBKR_PORT": "7497"
      }
    }
  }
}
```

## Safety Validation

All `place_order` calls are validated against:

1. **Emergency Stop**: Checks if emergency stop flag is set
2. **Circuit Breaker**: Checks if circuit breaker has been triggered
3. **Max Trade Risk**: Validates trade risk ≤ $500
4. **Daily Loss Limit**: Checks if daily losses ≥ $1,000
5. **Consecutive Losses**: Checks if ≥ 5 consecutive losses
6. **Concentration Limit**: Validates symbol exposure ≤ 30% of portfolio
7. **Order Leg Validation**: Checks minimum prices and spread widths

If any validation fails, the order is **rejected** and logged to `~/trading_workspace/logs/safety_violations.log`.

## Logging

All trading operations are logged to:

- **Trade Execution**: `~/trading_workspace/logs/trades/{trade_id}.json`
- **Trade Closes**: `~/trading_workspace/logs/trades/{trade_id}_close.json`
- **Safety Violations**: `~/trading_workspace/logs/safety_violations.log`
- **Circuit Breaker Events**: `~/trading_workspace/logs/circuit_breaker.log`

## Development Status

**Phase 2.1 COMPLETE**:
- ✅ MCP protocol handler
- ✅ Complete safety layer
- ✅ Tool definitions and metadata
- ✅ Logging infrastructure
- ✅ **Real IBKR TWS/Gateway connection** (via ib_insync)
- ✅ **Real-time position updates**
- ✅ **Order execution with IBKR API**
- ✅ **Connection health checks and auto-reconnection**

**TODO** (Phase 2.2+):
- [ ] Order status monitoring improvements
- [ ] Enhanced error handling for edge cases
- [ ] Comprehensive integration tests with paper trading

## Testing

To test the safety layer without IBKR connection:

```python
from safety import SafetyValidator

validator = SafetyValidator()

# Test order validation
order = {
    "symbol": "AAPL",
    "strategy": "Iron Condor",
    "max_risk": 600.0,  # Exceeds limit
    "capital_required": 500.0,
    "legs": []
}

is_valid, error = validator.validate_order(order)
print(f"Valid: {is_valid}, Error: {error}")
# Output: Valid: False, Error: Max risk ($600.00) exceeds limit ($500.00)
```

## Troubleshooting

### Connection Issues

**"Connection refused" Error**:
- Check that TWS/Gateway is running
- Verify API is enabled in settings
- Confirm correct port number (7497 for paper TWS)
- Check firewall settings

**"Connection timeout" Error**:
- Verify host and port in config
- Ensure TWS/Gateway is listening on the correct port
- Try restarting TWS/Gateway

**"Already connected" Error**:
- Another client is using the same client ID
- Change `IBKR_CLIENT_ID` to a different value (1-32)
- Or disconnect the other client first

**"Market data not available" Error**:
- Options trading requires market data subscription
- Paper trading: Delayed data is free
- Live trading: Subscribe to real-time options data

### Common Issues

**Orders rejected with "Invalid contract"**:
- Verify expiry date format: YYYY-MM-DD (will be converted to YYYYMMDD)
- Check that strike price exists in option chain
- Ensure right is "C" or "P"

**Health check shows "unhealthy"**:
- Connection to TWS/Gateway may be lost
- Check TWS/Gateway is still running
- Server will attempt automatic reconnection

## Architecture

```
mcp-servers/ibkr/
├── server.py          # MCP protocol handler
├── connection.py      # IBKR connection manager (ib_insync)
├── tools.py           # Tool implementations
├── safety.py          # Safety layer and validation
├── __init__.py        # Package exports
└── README.md          # This file
```

## Security Considerations

- Safety limits are hard-coded in `safety.py` - require code review to modify
- All orders are logged with full audit trail
- Emergency stop flag (`emergency_stop`) can be set manually to block all trades
- Circuit breakers automatically suspend trading on excessive losses

## License

Part of AlphaHive Agent Runtime project.
