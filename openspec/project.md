# Project Context

## Purpose

**Agentic AlphaHive Runtime** is a headless, non-interactive quantitative trading system that uses **Claude Code** as the core operating system and **Model Context Protocol (MCP)** for external financial infrastructure integration.

**Core Goals:**
- Autonomous options trading with recursive agent architecture (Commander + Alpha Swarm)
- Parameter-logic separation for safe "dream mode" evolution
- Hard-coded safety layer independent of AI decision-making
- Snapshot-driven decision logging for full auditability
- Paper trading first, with explicit safety gates before live trading

## Tech Stack

### Core Runtime
- **Claude Code**: Primary agent orchestration and decision-making engine
- **Python 3**: MCP server implementation, safety layer, trading tools
- **MCP Protocol (2024-11-05)**: Communication between Claude and external services

### Financial Infrastructure
- **Interactive Brokers (IBKR)**: Order execution and account management (via MCP)
- **ThetaData REST API**: Market data, options chains, historical data (direct HTTP calls, not MCP)
- **ib_insync**: Python library for IBKR TWS/Gateway integration

### Data & Processing
- **asyncio**: Concurrent swarm agent operations
- **SQLite**: Trade records and historical data storage
- **Jinja2**: Template rendering for swarm agent prompts
- **JSON**: Configuration and parameter storage

### Testing & Validation
- **pytest**: Test framework for MCP servers
- **pytest-asyncio**: Async test support
- **Mock IBKR connections**: Paper trading mode for safe testing

## Project Conventions

### Code Style

**Python (MCP Servers & Tools):**
- PEP 8 compliance with type hints
- Descriptive function/variable names: `validate_order()`, `max_trade_risk`
- Docstrings for all public functions with Args/Returns sections
- Use dataclasses for structured configuration (e.g., `SafetyLimits`)

**File Naming:**
- Snake case: `swarm_core.py`, `execution_gate.py`
- Test files: `test_*.py` pattern
- MCP servers: `server.py` in dedicated directories

**Configuration Files:**
- JSON for parameters: `active_instances/*.json`
- Markdown for templates: `templates/*.md`
- Environment variables for secrets: `.env` file

### Architecture Patterns

**Recursive Agent Structure:**
- **Commander** (Claude Code): High-level decision making via manual command triggers
- **Alpha Swarm** (Concurrent sub-agents): Parallel analysis via `swarm_core.py` Skill
- **Separation of concerns**: Logic (templates) vs Parameters (JSON configs)
- **Interaction Model**: Manual command-triggered (not automatic loop)

**MCP Server Pattern:**
- IBKR uses MCP server for trading operations
- ThetaData uses direct REST API (not MCP) for better reliability
- Servers expose tools via JSON-RPC over stdio (for MCP-based services)
- Safety validation happens before API calls, not after

**Safety Layer:**
- Hard-coded limits in `safety.py` (DO NOT modify without human approval)
- Independent watchdog process (`runtime/watchdog.py`) with separate IBKR connection
- Circuit breakers: daily loss limit ($1,000), drawdown triggers (10%), max trade risk ($500)
- Order validation before execution via `place_order_with_guard()`
- **Note**: Manual command mode eliminates need for heartbeat monitoring

**Data Flow:**
1. User command → Commander health check → Market data sync
2. Commander calls swarm analysis → Signal aggregation
3. All swarm inputs saved to `data_lake/snapshots/` for reproducibility
4. Commander decision → Order validation → IBKR submission
5. Results logged to `trades.db` for post-analysis

### Testing Strategy

**MCP Server Tests:**
- Unit tests: `tests/test_tools.py`, `tests/test_safety.py`
- Integration tests: `tests/test_integration.py` (requires IBKR connection)
- Connection tests: `tests/test_connection.py`
- Run with: `pytest mcp-servers/ibkr/tests/`

**Safety Validation:**
- All order operations tested against safety limits
- Mock trading environment before paper trading
- Paper trading validation before live trading
- Test circuit breakers with simulated drawdowns

**Swarm Testing:**
- Template rendering validation
- Concurrent agent execution stress tests
- Signal aggregation and de-duplication tests

### Git Workflow

**Branching Strategy:**
- `main`: Stable, tested code only
- Feature branches for new capabilities
- Use OpenSpec proposals for major changes

**Commit Conventions:**
- Safety changes: `[SAFETY] Description` - require extra scrutiny
- MCP changes: `[MCP] Description`
- Agent logic: `[AGENT] Description`
- Config/params: `[CONFIG] Description` - can be modified by dream mode

**Critical Files:**
- `safety.py`: Requires human approval for any changes
- `watchdog.py`: Independent safety process, no AI modifications
- `.env`: Never commit to git

## Domain Context

**Options Trading:**
- Primary strategy: Volatility-based spreads (put spreads, call spreads)
- Metrics: IV Rank, IV Percentile, Delta, Theta, Vega exposure
- Risk management: Defined-risk strategies only (no naked options)

**Market Data:**
- Real-time quotes via ThetaData MCP
- Options chains with Greeks from ThetaData
- Position tracking via IBKR API
- News sentiment analysis (planned via news-sentiment MCP)

**Agent Decision Making:**
- Swarm produces signals with confidence scores
- Commander evaluates signals against portfolio state
- Kelly criterion for position sizing
- Final go/no-go based on macro conditions + risk limits

**Terminology:**
- **Instance**: A specific swarm configuration (template + parameters)
- **Template**: Logic/strategy in Jinja2 Markdown format
- **Swarm**: Concurrent execution of all active instances
- **Signal**: Output from swarm analysis (symbol, strategy, confidence)
- **Commander**: Primary Claude Code agent orchestrating everything

## Important Constraints

### Safety Constraints (HARD LIMITS)
- **Max trade risk**: $500 per trade
- **Max trade capital**: $2,000 per trade
- **Daily loss limit**: $1,000 (triggers shutdown)
- **Max portfolio concentration**: 30% in any single symbol
- **Drawdown circuit breaker**: 10% account drawdown triggers full stop
- **Consecutive loss limit**: 5 losses triggers suspension

### Technical Constraints
- IBKR connection required for all trading operations
- Paper trading (port 4002) before live trading (port 4001)
- MCP protocol version 2024-11-05 compatibility
- Python 3.8+ required for asyncio features

### Operational Constraints
- **Manual command mode**: Trading analysis triggered by user commands, not automatic loops
- Watchdog process runs independently for account risk monitoring
- All trading decisions must be logged with full context snapshots
- No direct code generation for orders (use `execution_gate.py` primitives)
- Configuration changes (JSON) allowed; template logic changes require review
- Data access via REST API for ThetaData; MCP for IBKR only

### Regulatory/Risk Constraints
- Options-approved IBKR account required
- Defined-risk strategies only (no naked positions)
- Pre-market and after-hours trading requires explicit approval
- All trades subject to safety layer validation (no bypasses)

## External Dependencies

### Critical Services
- **Interactive Brokers TWS/Gateway**:
  - Paper Trading: localhost:4002
  - Live Trading: localhost:4001
  - Required: Running TWS/Gateway before agent starts

- **ThetaData API**:
  - Real-time market data
  - Options chains and Greeks
  - Historical data for backtesting
  - API key in `.env` file

### MCP Servers (Internal)
- **ibkr** (`mcp-servers/ibkr/`): Trading execution, account queries, position management (implemented)
- **news-sentiment** (planned): News analysis for sentiment filtering
- **memory** (planned): Long-term agent memory and state persistence

**Note**: ThetaData is accessed via REST API (not MCP) for improved reliability and simpler debugging.

### Python Libraries
- `ib_insync`: IBKR API wrapper (install: `pip install ib_insync`)
- `asyncio`: Built-in async runtime
- `pytest`, `pytest-asyncio`: Testing framework
- `jinja2`: Template rendering for swarm prompts

### File System Dependencies
- `~/trading_workspace/state/agent_memory.json`: Agent state persistence
- `~/trading_workspace/logs/`: Safety violations, circuit breaker events
- `data_lake/snapshots/`: Decision context archival
- `data_lake/trades.db`: Trade history database
