# Paper Trading Validation Guide

## Overview

This guide walks you through validating the Agentic AlphaHive Runtime system using IBKR Paper Trading before considering live trading.

## Prerequisites

### 1. IBKR Paper Trading Account

- Sign up at: https://www.interactivebrokers.com/en/trading/tws.php
- Download and install **IB Gateway** (lighter than TWS)
- **Important**: Use Paper Trading mode (port 4002)

### 2. API Keys Required

Create a `.env` file in the project root:

```bash
# Copy from example
cp .env.example .env

# Edit with your keys
nano .env
```

Required keys:
```
OPENROUTER_API_KEY=your_key_here    # Get from https://openrouter.ai/keys
IBKR_PORT=4002                       # Paper trading port
IBKR_CLIENT_ID=1                     # Main AI client
THETADATA_API_KEY=your_key_here      # Optional, for market data
```

### 3. Start IBKR Gateway

```bash
# On Linux/Mac
~/IBController/IBControllerGatewayStart.sh &

# On Windows
# Run IB Gateway from Start Menu

# Verify it's running on port 4002
netstat -an | grep 4002
```

**Important**:
- Enable API connections in IB Gateway settings
- Set "Read-Only API" to FALSE (required for paper trading)
- Port 4002 = Paper Trading Gateway

## Step-by-Step Validation

### Step 1: Reset Circuit Breaker

The circuit breaker may have been triggered during development testing:

```bash
# Check status
cat ~/trading_workspace/state/agent_memory.json

# Circuit breaker should show:
{
  "safety_state": {
    "circuit_breaker_triggered": false,
    "circuit_breaker_timestamp": null
  }
}
```

✅ **Already done** - Circuit breaker is reset!

### Step 2: Verify IBKR Connection

Test that the system can connect to IBKR Paper Trading:

```bash
# Test IBKR MCP server health
python3 -c "
from mcp_servers.ibkr import get_connection_manager, ConnectionMode
manager = get_connection_manager()
manager.connect_sync(mode=ConnectionMode.PAPER_GATEWAY, client_id=1)
print(f'Connected: {manager.is_connected}')
"
```

Expected output:
```
✅ Connected to IBKR Paper Trading (Gateway)
Connected: True
```

Or use the MCP tool directly:

```python
# In Claude Code
mcp__ibkr__health_check()
# Should return: {"is_connected": true, "mode": "Paper Trading (Gateway)", ...}

mcp__ibkr__get_account()
# Should return real account data from IBKR, not mock $10,000
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Initialize Database

```bash
# Create trades database
python -c "from data_lake import db_helpers; print('Database initialized')"

# Verify database exists
ls -lh data_lake/trades.db
```

### Step 5: Run Test Cycle

Start the runtime with IBKR connection:

```bash
# Run the main loop (press Ctrl+C to stop)
python runtime/main_loop.py
```

**What to look for:**

✅ **Good signs:**
```
INFO - === Agentic AlphaHive Runtime Starting ===
INFO - Watchdog process started (PID: XXXXX)
INFO - === Starting Trading Cycle ===
INFO - Current account value: $1,027,195.09    # <-- Real IBKR value!
INFO - Watchdog monitoring started
```

❌ **Bad signs:**
```
WARNING - Circuit breaker active - skipping cycle    # Circuit breaker triggered
ERROR - Failed to connect to IBKR                    # IBKR Gateway not running
WARNING - Using fallback account value               # Can't reach IBKR
INFO - Initial account value: $10000.00              # Mock data (not real IBKR)
```

### Step 6: Run Commander Agent (via Claude Code)

The main loop provides the runtime, but **Claude Code acts as the Commander** to make trading decisions.

In Claude Code, start a trading cycle:

```python
# === SENSE Phase ===
# Get account and positions
account = mcp__ibkr__get_account()
positions = mcp__ibkr__get_positions()

print(f"Account: ${account['net_liquidation']:,.2f}")
print(f"Positions: {len(positions)}")

# Get market data
symbols = ["AAPL", "NVDA", "TSLA"]
quotes = mcp__ThetaData__stock_snapshot_quote(symbol=symbols)

# === THINK Phase ===
from skills import consult_swarm

market_data = {
    "timestamp": "2025-11-20T01:00:00",
    "symbols": symbols,
    "quotes": quotes,
    "account": account,
    "positions": positions
}

# Consult the swarm for signals
signals = consult_swarm(sector="TECH", market_data=market_data)

print(f"Swarm returned {len(signals)} signals:")
for signal in signals:
    print(f"  - {signal['instance_id']}: {signal['signal']} on {signal['target']}")

# === DECIDE Phase ===
from skills import place_order_with_guard

approved_trades = []
for signal in signals:
    if signal["signal"] == "NO_TRADE":
        continue

    # Validate against safety limits
    result = place_order_with_guard(
        symbol=signal["target"],
        strategy=signal["signal"],
        legs=signal["params"]["legs"],
        max_risk=signal["params"]["max_risk"],
        capital_required=signal["params"]["capital_required"]
    )

    if result.success:
        approved_trades.append((signal, result))
    else:
        print(f"❌ Rejected: {result.error}")

# === ACT Phase ===
from skills.mcp_bridge import execute_order_with_ibkr

for signal, validated_order in approved_trades:
    try:
        # Submit to IBKR
        ibkr_result = mcp__ibkr__place_order(
            symbol=signal["target"],
            strategy=signal["signal"],
            legs=signal["params"]["legs"],
            max_risk=signal["params"]["max_risk"],
            capital_required=signal["params"]["capital_required"]
        )

        # Update trade status
        final_result = execute_order_with_ibkr(
            validated_order=validated_order,
            legs=signal["params"]["legs"],
            symbol=signal["target"],
            strategy=signal["signal"],
            max_risk=signal["params"]["max_risk"],
            capital_required=signal["params"]["capital_required"],
            metadata={"ibkr_result": ibkr_result}
        )

        if final_result.success:
            print(f"✅ Order placed: {signal['target']} (order_id={final_result.order_id})")
        else:
            print(f"❌ IBKR rejected: {final_result.error}")

    except Exception as e:
        print(f"❌ Error: {e}")
```

## Validation Checklist

Complete these tests before considering live trading:

### Safety Layer Tests

- [ ] **Max risk violation**: Attempt order with max_risk > $500
  - Expected: Rejected with safety violation logged
- [ ] **Max capital violation**: Attempt order with capital > $2000
  - Expected: Rejected with safety violation logged
- [ ] **Circuit breaker**: Simulate 10% drawdown
  - Expected: All trading halts, requires manual reset

### Functional Tests

- [ ] **Account data**: Verify real IBKR account values (not $10,000 mock)
- [ ] **Positions fetch**: Get current positions from IBKR
- [ ] **Swarm execution**: Swarm returns signals within 30 seconds
- [ ] **Order validation**: place_order_with_guard() validates correctly
- [ ] **Order submission**: IBKR MCP accepts valid paper orders
- [ ] **Snapshot logging**: Each decision creates snapshot in data_lake/snapshots/
- [ ] **Trade logging**: Orders logged to trades.db

### Watchdog Tests

- [ ] **Heartbeat monitoring**: Watchdog detects stale heartbeat (stop main_loop)
- [ ] **Real account value**: Watchdog shows real IBKR value, not $10,000
- [ ] **Circuit breaker trigger**: Watchdog can trigger circuit breaker on drawdown
- [ ] **Independent process**: Watchdog runs as separate process (check with `ps aux | grep watchdog`)

### 30-Day Validation Period

Run paper trading for 30 consecutive days:

1. **Daily monitoring** (15 min/day):
   - Check logs for errors
   - Review snapshots in data_lake/snapshots/
   - Verify no circuit breaker triggers
   - Review trade decisions in trades.db

2. **Weekly review** (1 hour/week):
   - Analyze P&L (if trades executed)
   - Review safety violations
   - Check swarm signal quality
   - Update strategy templates if needed

3. **Metrics to track**:
   ```sql
   -- Query trades database
   SELECT
       COUNT(*) as total_signals,
       SUM(CASE WHEN status='VALIDATED' THEN 1 ELSE 0 END) as validated,
       SUM(CASE WHEN status='REJECTED' THEN 1 ELSE 0 END) as rejected,
       AVG(CASE WHEN status='FILLED' THEN pnl ELSE NULL END) as avg_pnl
   FROM trades;
   ```

## Troubleshooting

### "Circuit breaker active - skipping cycle"

**Cause**: Circuit breaker was triggered (10% drawdown or manual trigger)

**Fix**:
```bash
# Reset circuit breaker
python -c "
import json
from pathlib import Path

memory_file = Path.home() / 'trading_workspace/state/agent_memory.json'
with open(memory_file, 'w') as f:
    json.dump({
        'safety_state': {
            'circuit_breaker_triggered': False,
            'circuit_breaker_timestamp': None
        }
    }, f, indent=2)

print('Circuit breaker reset')
"
```

### "Using fallback account value: $10,000"

**Cause**: Watchdog can't connect to IBKR Gateway

**Fix**:
1. Verify IBKR Gateway is running: `netstat -an | grep 4002`
2. Check .env has correct IBKR_PORT=4002
3. Enable API in IB Gateway settings
4. Set "Read-Only API" to FALSE

### "ERROR: Failed to connect to IBKR"

**Cause**: IBKR Gateway not running or wrong port

**Fix**:
1. Start IB Gateway: `~/IBController/IBControllerGatewayStart.sh`
2. Wait 30 seconds for startup
3. Verify with: `telnet localhost 4002`
4. Check logs: `~/IBController/Logs/`

### Swarm returns empty signals

**Cause**: LLM API key missing or invalid

**Fix**:
```bash
# Check .env file
grep OPENROUTER_API_KEY .env

# Test OpenRouter connection
curl https://openrouter.ai/api/v1/auth/key \
  -H "Authorization: Bearer $OPENROUTER_API_KEY"
```

## Success Criteria

Before transitioning to live trading:

### Technical Requirements
- ✅ All unit tests pass
- ✅ Watchdog detects frozen process within 60s
- ✅ Real IBKR data flowing (not mock $10,000)
- ✅ Circuit breaker triggers on 10% drawdown
- ✅ Safety layer rejects over-limit orders
- ✅ All decisions logged with snapshots

### Validation Requirements
- ✅ 30 days of paper trading completed
- ✅ Zero critical errors in logs
- ✅ P&L tracking accurate
- ✅ Watchdog never failed to detect issues
- ✅ Manual kill switch tested and works

### Human Approval Requirements
- ✅ Strategy performance meets expectations
- ✅ Risk management working correctly
- ✅ You understand and accept the risks
- ✅ Capital allocation decided
- ✅ Emergency procedures documented

## Next Steps After Validation

1. **Review 30-day results** with a mentor or experienced trader
2. **Adjust safety limits** if needed (in .env and execution_gate.py)
3. **Start small** with live trading (e.g., $5,000 account)
4. **Monitor closely** for first week of live trading
5. **Scale gradually** as confidence builds

## Emergency Procedures

If something goes wrong during paper trading:

### Manual Kill Switch
```bash
# Kill all processes
pkill -f "python runtime/main_loop.py"
pkill -f "runtime.watchdog"

# Reset circuit breaker
python -c "from data_lake.db_helpers import reset_circuit_breaker; reset_circuit_breaker()"
```

### Close All Positions (via IBKR)
```python
# In Claude Code
positions = mcp__ibkr__get_positions()

for pos in positions:
    print(f"Closing {pos['symbol']}...")
    # Manually close via IB Gateway UI or create close orders
```

### Review Logs
```bash
# Check what happened
tail -n 100 ~/trading_workspace/logs/main.log
tail -n 100 ~/trading_workspace/logs/watchdog.log

# Review trade database
sqlite3 data_lake/trades.db "SELECT * FROM trades ORDER BY created_at DESC LIMIT 10;"
```

---

## Summary

Paper trading validation is **mandatory** before live trading. Take your time, be thorough, and don't skip steps. The 30-day validation period helps you:

1. **Build confidence** in the system's safety mechanisms
2. **Understand** the AI's decision-making process
3. **Identify edge cases** before risking real money
4. **Refine strategies** based on market conditions
5. **Verify technical reliability** under various scenarios

Remember: **Paper trading should be boring**. If it's exciting or stressful, the system isn't ready for live trading yet.
