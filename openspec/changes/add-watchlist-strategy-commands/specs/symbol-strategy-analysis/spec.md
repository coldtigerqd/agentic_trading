# symbol-strategy-analysis Specification Deltas

## ADDED Requirements

### Requirement: Analyze Symbol with Specific Strategy

The system SHALL provide a `/trade:analyze-symbol` slash command to run a single strategy instance against a single symbol for testing and educational purposes.

**Priority:** MUST
**Impact:** Core UX for strategy testing and learning

#### Scenario: Analyze symbol with high-confidence signal

**Given** strategy instance `momentum_tech_short.json` exists (momentum_hunter template)
**And** symbol AAPL has GOOD market data (58,968 bars, latest: 2025-11-22 15:59:00)
**And** AAPL shows strong momentum: 20-day MA slope = +2.3°, volume 15% above average, RSI(14) = 58

**When** user executes `/trade:analyze-symbol AAPL momentum_tech_short`

**Then** the system SHALL:
- Load strategy instance configuration from `swarm_intelligence/active_instances/momentum_tech_short.json`
- Fetch AAPL market data from cache (no ThetaData fetch needed)
- Apply momentum_hunter strategy logic to AAPL data
- Generate signal: BUY with confidence 0.82
- Display detailed output including:
  - Symbol and strategy identification
  - Data status (✓ GOOD)
  - Signal and confidence level (BUY, 0.82 HIGH)
  - Reasoning with key factors (momentum, volume, RSI, MA crossovers)
  - Key metrics table (current price, MAs, ATR, volume ratio)
  - Suggested trade structure (Iron Condor with specific strikes and DTE)
  - Next steps (verify market conditions, run full analysis, execute order)

#### Scenario: Analyze symbol with low confidence (no clear signal)

**Given** strategy instance `mean_reversion_energy.json` exists
**And** symbol TSLA has GOOD market data
**And** TSLA shows weak mean reversion setup: price deviation -1.2σ (below 2.5σ threshold)
**And** TSLA sector (tech/auto) mismatches strategy sector (energy)

**When** user executes `/trade:analyze-symbol TSLA mean_reversion_energy`

**Then** the system SHALL:
- Run analysis successfully
- Generate signal: HOLD with confidence 0.45 (LOW - below actionable threshold 0.70)
- Display reasoning explaining why signal is weak:
  - Price deviation insufficient for mean reversion
  - Sector mismatch warning
  - Volatility regime not ideal (IV Rank too low)
- Recommendation section suggesting:
  - Try different strategy more suitable for TSLA
  - Wait for better mean reversion setup
  - Check sector-specific strategies

#### Scenario: Analyze symbol not in watchlist (on-demand fetch)

**Given** strategy instance `momentum_tech_short.json` exists
**And** symbol GOOGL is not in watchlist (not in database)
**And** GOOGL is a valid ticker format

**When** user executes `/trade:analyze-symbol GOOGL momentum_tech_short`

**Then** the system SHALL:
- Detect GOOGL not in cache
- Fetch market data from ThetaData on-demand (may take 10-15 seconds for 3 years)
- Show progress indicator: "Fetching market data for GOOGL (this may take 15 seconds)..."
- Cache fetched data for future use
- Proceed with analysis using fresh data
- Suggest: "Add GOOGL to watchlist for faster future analysis: /trade:watchlist-add GOOGL"

#### Scenario: Handle stale data gracefully

**Given** strategy instance `momentum_tech_short.json` exists
**And** symbol TSLA has STALE data (latest: 5 days ago)

**When** user executes `/trade:analyze-symbol TSLA momentum_tech_short`

**Then** the system SHALL:
- Detect data staleness
- Display warning at top:
  ```
  ⚠ Warning: Data for TSLA is 5 days old (STALE). Results may be inaccurate.
  Consider running backfill: python scripts/backfill_historical_data.py --symbols TSLA --days 7
  ```
- Proceed with analysis using available data
- Include data quality warning in output

#### Scenario: Reject non-existent strategy instance

**Given** strategy instance `nonexistent_strategy.json` does not exist
**And** symbol AAPL exists with GOOD data

**When** user executes `/trade:analyze-symbol AAPL nonexistent_strategy`

**Then** the system SHALL:
- Display error: "Error: Strategy instance 'nonexistent_strategy' not found. Use /trade:strategies to list available instances."
- Not attempt analysis
- Not modify any files

#### Scenario: Reject invalid symbol format

**Given** strategy instance `momentum_tech_short.json` exists
**And** user provides invalid symbol "abc" (lowercase)

**When** user executes `/trade:analyze-symbol abc momentum_tech_short`

**Then** the system SHALL:
- Validate symbol format before loading strategy
- Display error: "Error: Symbol 'abc' not found in watchlist and is not a valid ticker"
- Not attempt data fetch or analysis

#### Scenario: Handle strategy execution error gracefully

**Given** strategy instance `broken_strategy.json` exists but has buggy logic
**And** symbol AAPL has GOOD data
**And** strategy raises exception during analysis (e.g., division by zero in custom indicator)

**When** user executes `/trade:analyze-symbol AAPL broken_strategy`

**Then** the system SHALL:
- Catch exception during strategy execution
- Display error with details:
  ```
  Error: Strategy 'broken_strategy' failed during analysis
  Details: ZeroDivisionError: division by zero in calculate_custom_indicator()

  Check strategy configuration in:
  swarm_intelligence/active_instances/broken_strategy.json
  ```
- Not crash the command
- Suggest reviewing strategy configuration

---

### Requirement: Educational Output Format

The system SHALL provide detailed, educational output from `/trade:analyze-symbol` to help users understand strategy reasoning and improve their trading knowledge.

**Priority:** SHOULD
**Impact:** Enhanced learning and transparency

#### Scenario: Display clear reasoning for signal

**Given** analysis generates BUY signal with 0.85 confidence for AAPL

**When** output is displayed

**Then** the system SHALL include:
- **Reasoning section** with bullet points explaining:
  - Each factor that contributed to the signal (e.g., "Strong upward momentum: 20-day MA slope = +2.3°")
  - How each factor compares to strategy thresholds (e.g., "Volume 15% above average (threshold: >10%)")
  - Confirmations and contradictions (e.g., "RSI = 58 (neutral, room to run)")
- **Key Metrics table** showing:
  - Current price and technical indicators (MAs, RSI, ATR)
  - Relative values (% above/below MAs)
  - Volatility measures (ATR, IV Rank)
- **Suggested Trade structure** if signal is actionable (confidence ≥0.70):
  - Specific strikes based on delta targeting
  - DTE (days to expiration) range
  - Max risk and target premium
  - Expected ROI

#### Scenario: Explain why signal is not actionable

**Given** analysis generates HOLD signal with 0.45 confidence for TSLA

**When** output is displayed

**Then** the system SHALL include:
- Clear statement: "Signal: HOLD | Confidence: 0.45 (LOW - below actionable threshold)"
- **Reasoning section** explaining shortcomings:
  - Which thresholds were not met (e.g., "Price deviation -1.2σ (below 2.5σ threshold)")
  - Mismatches or concerns (e.g., "Sector mismatch: TSLA is tech/auto, strategy optimized for energy")
- **Recommendation section** suggesting:
  - Alternative strategies better suited for the symbol
  - Conditions to wait for before re-evaluating
  - How to find appropriate strategies (e.g., "Check sector-specific strategies")
