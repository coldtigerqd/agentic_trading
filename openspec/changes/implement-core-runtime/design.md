# Design: Core Runtime System

**Change ID:** `implement-core-runtime`
**Last Updated:** 2025-11-20

## Context

The Agentic AlphaHive Runtime is a headless autonomous trading system where Claude Code acts as the operating system kernel. The system must support:

- **Safety-first architecture**: Independent watchdog that cannot be bypassed by AI
- **Recursive intelligence**: Commander orchestrates concurrent swarm of sub-agents
- **Parameter-logic separation**: Swarm templates (logic) + JSON configs (parameters)
- **Full auditability**: Every decision captured with complete context
- **Paper trading**: Validate in simulation before any live trading

### Constraints

1. **Safety is non-negotiable**: Watchdog must be truly independent
2. **Snapshot everything**: All swarm inputs must be captured for replay
3. **No AI code generation for orders**: Use validated primitives only
4. **Claude Code is the orchestrator**: Skills are tools, not autonomous agents

## Goals / Non-Goals

### Goals
- Implement MVP recursive swarm architecture
- Establish foundation for dream mode evolution
- Enable paper trading with full safety validation
- Create modular, testable components

### Non-Goals
- Live trading (requires separate approval gate)
- Web UI or real-time monitoring
- Complex backtesting infrastructure
- Multi-user support

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                       Claude Code Runtime                        │
│                     (Commander Agent)                            │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  System Prompt: prompts/commander_system.md                │ │
│  │  - Trading philosophy & risk management rules              │ │
│  │  - Workflow: sense → think (swarm) → decide → act         │ │
│  └────────────────────────────────────────────────────────────┘ │
│                              ↓                                   │
│              ┌───────────────┼───────────────┐                  │
│              ↓               ↓               ↓                  │
│    ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│    │ swarm_core() │  │ math_core()  │  │execution_gate│       │
│    │   Skill      │  │    Skill     │  │   ()Skill    │       │
│    └──────────────┘  └──────────────┘  └──────────────┘       │
└────────────────────────┼──────────────────────────────────────┘
                         ↓
        ┌────────────────────────────────────────┐
        │    Swarm Intelligence Engine           │
        │  (skills/swarm_core.py)                │
        │                                        │
        │  ┌──────────────────────────────────┐ │
        │  │ 1. Load active_instances/*.json  │ │
        │  │ 2. Render templates with params  │ │
        │  │ 3. Concurrent LLM API calls      │ │
        │  │ 4. Save input snapshots          │ │
        │  │ 5. Aggregate signals             │ │
        │  └──────────────────────────────────┘ │
        └────────────────────────────────────────┘
                ↓              ↓              ↓
        ┌─────────┐    ┌─────────┐    ┌─────────┐
        │Instance1│    │Instance2│    │InstanceN│
        │(Agent 1)│    │(Agent 2)│    │(Agent N)│
        └─────────┘    └─────────┘    └─────────┘
              ↓              ↓              ↓
        [Snapshots saved to data_lake/snapshots/]
              ↓              ↓              ↓
        ┌──────────────────────────────────────┐
        │   Signal Aggregation                 │
        │   [{instance_id, signal, params...}] │
        └──────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    Independent Watchdog                          │
│                 (Separate Python Process)                        │
│                                                                   │
│  - Separate IBKR connection (different client_id)                │
│  - Monitors AI process heartbeat (60s timeout)                   │
│  - Checks account value for circuit breakers                     │
│  - Can force-kill AI process and panic-close positions           │
│  - Logs all safety events independently                          │
└─────────────────────────────────────────────────────────────────┘
```

## Data Flow

### Trading Decision Flow

```
1. Runtime Startup
   └─ watchdog.py starts first
   └─ main_loop.py starts, registers heartbeat with watchdog
   └─ Commander loads system prompt

2. Market Sensing
   └─ Commander calls IBKR MCP: get_account()
   └─ Commander calls ThetaData MCP: get market data
   └─ Commander updates internal state

3. Swarm Analysis (THE CRITICAL PHASE)
   └─ Commander: skill.consult_swarm(sector="ALL")
   └─ swarm_core.py:
       ├─ Load all active_instances/*.json
       ├─ For each instance:
       │   ├─ Read template from templates/{instance.template}
       │   ├─ Inject parameters into template (Jinja2)
       │   ├─ Package with market data snapshot
       │   └─ Save complete input to snapshots/TIMESTAMP_INSTANCE.json
       ├─ Launch concurrent LLM API calls (asyncio.gather)
       ├─ Parse responses into signals
       ├─ Aggregate and deduplicate signals
       └─ Return signal list to Commander

4. Commander Decision
   └─ Evaluate each signal
   └─ Apply portfolio constraints
   └─ Calculate position sizing (Kelly criterion)
   └─ Make go/no-go decision

5. Order Execution
   └─ Commander: skill.execution_gate(order_params)
   └─ execution_gate.py:
       ├─ Safety validation (safety.py)
       ├─ Order construction (IBKR format)
       ├─ Submit to IBKR MCP: place_order()
       └─ Log order to trades.db

6. Sleep & Monitor
   └─ Commander enters sleep
   └─ Watchdog continues monitoring
   └─ Next cycle triggered by schedule or event
```

## Component Designs

### 1. Swarm Core Skill (`skills/swarm_core.py`)

```python
def consult_swarm(
    sector: str = "ALL",
    market_data: Optional[Dict] = None,
    max_concurrent: int = 50
) -> List[Signal]:
    """
    Execute swarm intelligence analysis.

    Args:
        sector: Filter instances by sector ("ALL", "TECH", "FINANCE", etc.)
        market_data: Current market snapshot (if None, fetches fresh data)
        max_concurrent: Maximum concurrent LLM API calls

    Returns:
        List of Signal objects with structure:
        {
            "instance_id": "tech_aggressive",
            "template_used": "vol_sniper",
            "target": "NVDA",
            "signal": "SHORT_PUT_SPREAD",
            "params": {...},
            "confidence": 0.88,
            "reasoning": "..."
        }
    """
    # 1. Load active instances
    instances = load_instances(sector_filter=sector)

    # 2. Fetch market data if not provided
    if market_data is None:
        market_data = fetch_market_snapshot()

    # 3. Prepare prompts
    prompts = []
    for instance in instances:
        template = load_template(instance['template'])
        rendered = render_template(template, instance['parameters'])
        prompt_package = {
            'instance_id': instance['id'],
            'prompt': rendered,
            'market_data': market_data,
            'timestamp': datetime.now().isoformat()
        }

        # CRITICAL: Save input snapshot
        save_snapshot(prompt_package)
        prompts.append(prompt_package)

    # 4. Concurrent execution
    loop = asyncio.get_event_loop()
    responses = loop.run_until_complete(
        execute_swarm_concurrent(prompts, max_concurrent)
    )

    # 5. Parse and aggregate
    signals = [parse_signal(r) for r in responses]
    signals = deduplicate_signals(signals)

    return signals
```

**Key Decisions:**
- **Snapshot BEFORE execution**: Ensures we can replay exact inputs
- **asyncio for concurrency**: I/O-bound operations benefit most
- **Max concurrent limit**: Prevent API rate limiting
- **Deduplication**: Multiple instances may suggest same trade

### 2. Execution Gate Skill (`skills/execution_gate.py`)

```python
def place_order_with_guard(
    symbol: str,
    strategy: str,
    legs: List[Dict],
    max_risk: float,
    capital_required: float,
    metadata: Optional[Dict] = None
) -> OrderResult:
    """
    Validated order placement primitive.

    SAFETY LAYER ENFORCEMENT:
    - All orders pass through SafetyValidator
    - Rejects orders exceeding limits
    - Logs all attempts (approved + rejected)
    - No bypasses allowed

    Args:
        symbol: Underlying ticker
        strategy: Strategy name (e.g., "IRON_CONDOR", "PUT_SPREAD")
        legs: List of order legs with action/contract/quantity/price
        max_risk: Maximum risk for this trade ($)
        capital_required: Capital to deploy ($)
        metadata: Optional context (reasoning, confidence, etc.)

    Returns:
        OrderResult with status, order_id, errors
    """
    # 1. Safety validation (CANNOT BE BYPASSED)
    order_dict = {
        'symbol': symbol,
        'strategy': strategy,
        'legs': legs,
        'max_risk': max_risk,
        'capital_required': capital_required
    }

    is_valid, error_msg = safety_validator.validate_order(order_dict)
    if not is_valid:
        log_rejected_order(order_dict, error_msg)
        return OrderResult(success=False, error=error_msg)

    # 2. Construct IBKR order
    ibkr_order = build_ibkr_order(symbol, legs, strategy)

    # 3. Submit via IBKR MCP
    result = ibkr_mcp.place_order(
        symbol=symbol,
        strategy=strategy,
        legs=legs,
        max_risk=max_risk,
        capital_required=capital_required,
        metadata=metadata
    )

    # 4. Log to database
    log_order_to_db(order_dict, result, metadata)

    return result
```

**Key Decisions:**
- **No order bypasses**: Even Commander must use this function
- **Safety layer is first**: Validation happens before construction
- **Comprehensive logging**: Both approved and rejected orders logged
- **Metadata support**: Capture reasoning for post-analysis

### 3. Math Core Skill (`skills/math_core.py`)

```python
def kelly_criterion(
    win_prob: float,
    win_amount: float,
    loss_amount: float,
    bankroll: float,
    fraction: float = 0.25
) -> float:
    """
    Calculate position size using Kelly Criterion.

    Uses fractional Kelly (default 0.25) for safety.
    """
    kelly = (win_prob * win_amount - (1 - win_prob) * loss_amount) / win_amount
    kelly_fraction = kelly * fraction
    position_size = bankroll * kelly_fraction
    return max(0, position_size)  # Never negative


def black_scholes_iv(
    option_price: float,
    spot: float,
    strike: float,
    time_to_expiry: float,
    rate: float,
    is_call: bool
) -> float:
    """
    Calculate implied volatility using Newton-Raphson.
    """
    # Implementation details...
    pass
```

**Key Decisions:**
- **Deterministic math only**: No randomness, always reproducible
- **Fractional Kelly by default**: Full Kelly is too aggressive
- **Type hints**: Ensure correct usage by Commander

### 4. Runtime Main Loop (`runtime/main_loop.py`)

```python
def trading_cycle():
    """
    Single iteration of the trading decision cycle.
    """
    logger.info("=== Starting Trading Cycle ===")

    # 1. Heartbeat to watchdog
    send_heartbeat()

    # 2. Check if trading is allowed
    if is_circuit_breaker_triggered():
        logger.warning("Circuit breaker active, skipping cycle")
        return

    # 3. Market sensing
    account = ibkr.get_account()
    logger.info(f"Account value: ${account['NetLiquidation']}")

    # 4. Invoke Commander (Claude Code)
    # This is where Commander agent takes over
    # Commander will:
    #   - Call swarm_core.consult_swarm()
    #   - Evaluate signals
    #   - Make trading decisions
    #   - Call execution_gate.place_order_with_guard()

    # The main_loop just provides the scheduling framework
    # Actual decisions are made by Commander agent

    invoke_commander_agent()

    # 5. Post-cycle cleanup
    send_heartbeat()
    logger.info("=== Cycle Complete ===")


def main():
    """Main entry point."""
    logger.info("Agentic AlphaHive Runtime Starting")

    # Start watchdog in separate process
    watchdog_process = start_watchdog()

    try:
        while True:
            trading_cycle()
            time.sleep(CYCLE_INTERVAL_SECONDS)
    except KeyboardInterrupt:
        logger.info("Shutting down gracefully")
    finally:
        watchdog_process.terminate()
```

### 5. Independent Watchdog (`runtime/watchdog.py`)

```python
class IndependentWatchdog:
    """
    SAFETY-CRITICAL COMPONENT

    Must run as separate process with independent IBKR connection.
    Must survive if AI process crashes or deadlocks.
    """

    def __init__(self):
        # Separate IBKR connection with different client_id
        self.ibkr_connection = ib_insync.IB()
        self.ibkr_connection.connect(
            'localhost',
            4002,  # Paper trading gateway
            clientId=999  # Different from AI process
        )

        self.last_heartbeat = time.time()
        self.initial_account_value = None

    def monitor_loop(self):
        """Main monitoring loop."""
        while True:
            # Check 1: AI process heartbeat
            if time.time() - self.last_heartbeat > 60:
                self.handle_frozen_ai()

            # Check 2: Account drawdown
            account_value = self.get_account_value()
            if self.check_drawdown_circuit_breaker(account_value):
                self.trigger_panic_close()

            # Check 3: Daily loss limit
            if self.check_daily_loss_limit():
                self.trigger_shutdown()

            time.sleep(10)  # Check every 10 seconds

    def handle_frozen_ai(self):
        """AI process is frozen - force kill and close positions."""
        logger.critical("AI PROCESS FROZEN - INITIATING EMERGENCY SHUTDOWN")

        # 1. Force kill AI process
        os.kill(ai_process_pid, signal.SIGKILL)

        # 2. Close all positions
        self.panic_close_all_positions()

        # 3. Log event
        log_emergency_event("FROZEN_AI")

        # 4. Alert human
        send_alert("CRITICAL: AI frozen, positions closed, system halted")

    def panic_close_all_positions(self):
        """Force close all open positions at market."""
        positions = self.ibkr_connection.positions()
        for pos in positions:
            order = MarketOrder('SELL' if pos.position > 0 else 'BUY',
                               abs(pos.position))
            self.ibkr_connection.placeOrder(pos.contract, order)

        logger.critical(f"PANIC CLOSE: {len(positions)} positions closed")
```

**Key Decisions:**
- **Separate process**: Uses `multiprocessing`, not threading
- **Independent IBKR connection**: Different client_id ensures it always works
- **Force kill capability**: Can kill frozen AI process
- **Panic close**: Market orders to exit immediately
- **No AI dependency**: Pure Python logic, no LLM calls

## Data Models

### Snapshot Format (JSON)

```json
{
  "snapshot_id": "20251120T093045_tech_aggressive",
  "timestamp": "2025-11-20T09:30:45.123Z",
  "instance_id": "tech_aggressive",
  "template_name": "vol_sniper",
  "rendered_prompt": "...",
  "market_data": {
    "symbols": ["NVDA", "AMD", "TSLA"],
    "quotes": {...},
    "options_chains": {...}
  },
  "agent_response": {
    "signal": "SHORT_PUT_SPREAD",
    "target": "NVDA",
    "confidence": 0.88,
    "reasoning": "..."
  }
}
```

### Trades Database Schema (SQLite)

```sql
CREATE TABLE trades (
    trade_id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    symbol TEXT NOT NULL,
    strategy TEXT NOT NULL,
    signal_source TEXT,  -- instance_id that generated signal
    legs TEXT NOT NULL,  -- JSON array
    max_risk REAL NOT NULL,
    capital_required REAL NOT NULL,
    confidence REAL,
    reasoning TEXT,
    order_id INTEGER,
    status TEXT,  -- 'SUBMITTED', 'FILLED', 'REJECTED', 'CANCELLED'
    fill_price REAL,
    pnl REAL
);

CREATE TABLE safety_events (
    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    event_type TEXT NOT NULL,  -- 'ORDER_REJECTED', 'CIRCUIT_BREAKER', etc.
    details TEXT,  -- JSON
    action_taken TEXT
);
```

## Testing Strategy

### Unit Tests
- Test each skill function with mocked dependencies
- Test safety validator with various order scenarios
- Test template rendering with different parameters

### Integration Tests
- Test full swarm execution with mock LLM API
- Test watchdog detection of frozen process
- Test database writes and snapshot creation

### Paper Trading Tests
- Run full cycles against IBKR paper account
- Verify orders are constructed correctly
- Test safety rejections (intentionally violate limits)
- Verify watchdog can close positions

## Migration Plan

### Phase 1: Core Infrastructure (This Change)
1. Create directory structure
2. Implement skills (swarm_core, math_core, execution_gate)
3. Implement runtime (main_loop, watchdog)
4. Create initial template and instance
5. Set up database schema

### Phase 2: Integration & Testing
1. Unit test all skills
2. Integration test with mock LLM
3. Paper trading validation
4. Safety testing (intentional violations)

### Phase 3: Monitoring & Refinement
1. Add comprehensive logging
2. Create debugging tools
3. Refine swarm prompts
4. Tune safety parameters

### Future Phases
- Phase 4: Dream mode evolution (genetic algorithm)
- Phase 5: Advanced strategies and templates
- Phase 6: Live trading (requires separate approval)

## Risks / Trade-offs

### Risk: Watchdog process communication
**Trade-off**: IPC complexity vs safety guarantee

**Decision**: Use file-based heartbeat (simple, reliable)
- AI writes heartbeat timestamp to file
- Watchdog reads file to check liveness
- Simple but slightly slower than shared memory

**Mitigation**: 10-second write interval is sufficient for safety

### Risk: LLM API rate limiting
**Trade-off**: Fast concurrent execution vs API limits

**Decision**: Implement exponential backoff + max_concurrent limit
- Start with 10 concurrent, increase if no errors
- Back off if rate limit errors detected
- Log all API errors for debugging

### Risk: Snapshot storage growth
**Trade-off**: Complete auditability vs disk space

**Decision**: Keep all snapshots, implement rotation policy
- Compress snapshots after 7 days
- Archive to cold storage after 30 days
- Never delete (regulatory compliance)

## Open Questions (Resolved)

1. **Q: Should watchdog have kill switch API?**
   **A**: No. Watchdog is fire-and-forget for safety. Human intervention via process signals only.

2. **Q: How to handle partial swarm failures?**
   **A**: Continue with successful responses, log failures, alert if >50% fail.

3. **Q: Snapshot format: before or after LLM response?**
   **A**: Both. Input snapshot before, append response after completion.

## Success Metrics

- [ ] Swarm executes 10 instances in < 30 seconds
- [ ] Watchdog detects frozen process within 60 seconds
- [ ] 100% of orders pass through safety validation
- [ ] All snapshots contain complete reproducible context
- [ ] Paper trading cycle completes without errors
- [ ] Test coverage > 80% for all skills
