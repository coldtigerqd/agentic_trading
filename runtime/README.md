# Agentic AlphaHive Runtime

## Overview

The Agentic AlphaHive Runtime is a headless autonomous trading system where Claude Code acts as the Commander, orchestrating a recursive swarm of specialized trading agents.

## Quick Start

### Prerequisites

1. **Python 3.8+** installed
2. **OpenRouter API key** in `.env` file (for swarm intelligence)
3. **IBKR Gateway** running on localhost:4002 (paper trading)
4. **ThetaData API key** in `.env` file (optional)

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Initialize database
python -c "from data_lake import db_helpers"

# Verify setup
python -c "import skills; print('Skills loaded successfully')"
```

### Running the System

```bash
# Start the main loop (includes watchdog)
python runtime/main_loop.py
```

## Architecture

```
Commander (Claude Code)
    ↓
Skills Library
    ├─ swarm_core: Concurrent agent orchestration
    ├─ math_core: Financial calculations
    └─ execution_gate: Validated order submission
    ↓
MCP Servers
    ├─ IBKR: Order execution
    └─ ThetaData: Market data
```

## Safety Features

- **Independent Watchdog**: Separate process monitors AI health
- **Hard-coded Limits**: Max risk $500, max capital $2000 per trade
- **Circuit Breakers**: 10% drawdown triggers automatic shutdown
- **Full Auditability**: All decisions logged with complete context

## Configuration

### Swarm Instances

Located in `swarm_intelligence/active_instances/`:
- `tech_aggressive.json`: High IV tech stocks
- `finance_conservative.json`: Conservative financial stocks

### Templates

Located in `swarm_intelligence/templates/`:
- `vol_sniper.md`: Volatility-based premium selling

## Testing

```bash
# Run unit tests
pytest tests/test_skills.py -v

# Test database
python -c "from data_lake.db_helpers import query_trades; print(query_trades())"

# Test swarm loading
python -c "from skills.swarm_core import load_instances; print(load_instances())"
```

## Monitoring

### Logs
- Main loop: Console output
- Watchdog: Console output with WATCHDOG prefix
- Safety events: `data_lake/trades.db` (safety_events table)

### Heartbeat
- Location: `~/trading_workspace/heartbeat.txt`
- Updated every cycle
- Monitored by watchdog

### Circuit Breaker
- Status: `~/trading_workspace/state/agent_memory.json`
- Manual reset required after trigger

## Development Workflow

1. **Create new strategy template** in `swarm_intelligence/templates/`
2. **Create instance configuration** in `swarm_intelligence/active_instances/`
3. **Test template rendering** with `skills.swarm_core`
4. **Run paper trading cycle** and verify logs
5. **Review snapshots** in `data_lake/snapshots/`

## Troubleshooting

### Watchdog Not Starting
- Check `multiprocessing` module is available
- Ensure heartbeat file path is writable

### Orders Being Rejected
- **This is expected!** Safety layer is working
- Check `data_lake/trades.db` safety_events table
- Adjust position sizes or check limit violations

### Swarm Not Executing
- Verify instances exist in `active_instances/`
- Check template files exist in `templates/`
- Review console logs for loading errors

## Next Steps

- Test OpenRouter/Gemini integration with real API key
- Connect IBKR MCP for real order submission
- Integrate ThetaData MCP for market data
- Add dream mode evolution (genetic algorithm)
- Implement comprehensive backtesting

## Safety Checklist

Before live trading:
- [ ] All unit tests passing
- [ ] Paper trading validated for 30 days
- [ ] Watchdog panic close tested
- [ ] Circuit breaker tested
- [ ] Order rejection handling verified
- [ ] Manual kill switch documented
- [ ] Human approval for live trading transition
