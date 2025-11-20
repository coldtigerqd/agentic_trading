# watchlist-manager Specification

## Purpose
TBD - created by archiving change enhance-swarm-intelligence. Update Purpose after archive.
## Requirements
### Requirement: Performance-Based Symbol Scoring

The system MUST calculate a composite performance score for each symbol combining Sharpe ratio, win rate, average P&L, and trade frequency.

**Priority:** MUST
**Impact:** Core algorithm for identifying top performers

#### Scenario: Calculate composite score for high-performing symbol

**Given** a symbol with 90 days of trade history:
- Sharpe ratio: 1.5 (excellent risk-adjusted return)
- Win rate: 65% (15 wins out of 23 trades)
- Average P&L: $250 per trade
- Trade count: 23 trades (2.5 trades per week)

**When** the system calculates `calculate_symbol_score(symbol, lookback_days=90)`
**Then** it SHALL return a composite score where:
- Sharpe ratio contributes 40% weight: 1.5 * 0.4 = 0.6
- Win rate contributes 30% weight: 0.65 * 0.3 = 0.195
- Avg P&L normalized to [0,1] contributes 20% weight
- Trade frequency normalized contributes 10% weight
- Total score is sum of weighted components
- Score is in range [0.0, 1.0] for normalization

#### Scenario: Penalize low-performing symbol

**Given** a symbol with poor performance:
- Sharpe ratio: -0.5 (losing money on risk-adjusted basis)
- Win rate: 35% (7 wins out of 20 trades)
- Average P&L: -$50 per trade
- Trade count: 20 trades

**When** the system calculates composite score
**Then** it SHALL return a score <0.3
**And** SHALL identify symbol in bottom 20% for rotation

---

### Requirement: Automated Watchlist Rotation

The system MUST automatically rotate underperforming symbols out and replace them with better candidates weekly.

**Priority:** MUST
**Impact:** Maintains watchlist quality without manual intervention

#### Scenario: Rotate bottom 20% performers weekly

**Given** a watchlist of 20 symbols with performance scores calculated
**And** today is Monday (weekly evaluation day)
**And** bottom 4 symbols (20%) have scores <0.4
**And** 10 candidate symbols available, 3 with scores >0.6

**When** the system calls `update_watchlist(current_watchlist, candidates)`
**Then** it SHALL return a recommendation dict containing:
- `remove`: List of 3 bottom performers (not 4, limited by churn)
- `add`: List of 3 top candidates (scores >0.6)
- `reason`: "Performance-based rotation (bottom 20% replaced)"
- `changes_count`: 3 (churn limit enforced)

**And** SHALL NOT rotate more than 3 symbols per week (churn limit)
**And** SHALL preserve 17 existing symbols (85% stability)

#### Scenario: Skip rotation when no better candidates

**Given** current watchlist with lowest score 0.5
**And** all candidate symbols have scores <0.5

**When** the system evaluates watchlist update
**Then** it SHALL return:
- `remove`: []
- `add`: []
- `reason`: "No better candidates available"
- `changes_count`: 0

**And** SHALL preserve entire current watchlist

---

### Requirement: Sector Diversification Enforcement

The system MUST enforce sector diversification limits to avoid concentration risk.

**Priority:** MUST
**Impact:** Risk management and portfolio balance

#### Scenario: Reject rotation that violates sector limits

**Given** a 20-symbol watchlist with sector distribution:
- Technology: 5 symbols (25%)
- Finance: 4 symbols (20%)
- Energy: 3 symbols (15%)
- Healthcare: 8 symbols (40%)

**When** rotation recommends adding 2 more Healthcare symbols
**Then** the system SHALL:
- Detect that Healthcare would become 50% (10/20 symbols)
- Reject the addition (max 30% per sector)
- Return `sector_limit_violated: true` in response
- Suggest alternative candidates from under-represented sectors

#### Scenario: Enforce balanced distribution during rotation

**Given** rotation candidates from multiple sectors
**When** system selects 3 symbols to add
**Then** it SHALL prioritize candidates to maintain balance:
- If Technology <20%, prefer Tech candidates
- If Finance >30%, exclude Finance candidates
- Result: No sector exceeds 30% of watchlist

---

### Requirement: Churn Limit Enforcement

The system MUST limit watchlist changes to maximum 3 symbols per week to avoid excessive trading.

**Priority:** MUST
**Impact:** Prevents overtrading and maintains strategy stability

#### Scenario: Limit rotation to 3 changes despite 5 underperformers

**Given** 5 symbols in bottom 20% with scores <0.3
**And** 8 excellent candidates with scores >0.7

**When** system evaluates rotation
**Then** it SHALL:
- Identify worst 3 underperformers (not all 5)
- Replace with best 3 candidates
- Return `changes_count: 3` (limit enforced)
- Defer remaining 2 underperformers to next week

**And** SHALL log: "Churn limit reached: 2 additional changes deferred"

---

### Requirement: Performance Metric Calculation

The system MUST accurately calculate Sharpe ratio, win rate, average P&L, and trade frequency from trade history.

**Priority:** MUST
**Impact:** Accurate scoring depends on correct metric calculation

#### Scenario: Calculate Sharpe ratio from trade history

**Given** 20 trades over 90 days with returns: [0.05, -0.02, 0.03, ..., 0.01]
**When** system calculates Sharpe ratio
**Then** it SHALL:
- Compute mean return: μ = mean(returns)
- Compute standard deviation: σ = std(returns)
- Calculate Sharpe: (μ - 0.0) / σ  (assuming risk-free rate = 0)
- Annualize: Sharpe * sqrt(252 / 90)  (252 trading days per year)
- Return value typically in range [-2.0, 3.0]

#### Scenario: Calculate win rate from trade records

**Given** 30 trades: 18 profitable, 12 losing
**When** system calculates win rate
**Then** it SHALL return 0.60 (18/30 = 60%)
**And** SHALL handle edge case of 0 trades (return 0.5 neutral)

---

### Requirement: Watchlist Update Integration

The system MUST integrate watchlist updates into Commander workflow without disrupting trading decisions.

**Priority:** MUST
**Impact:** Seamless operation without manual intervention

#### Scenario: Process watchlist update during Commander ACT phase

**Given** Commander has evaluated signals and selected a trade
**And** watchlist manager recommends 3 symbol changes
**And** current time is Monday morning

**When** Commander reaches ACT phase
**Then** it SHALL:
1. Execute selected trade first (priority)
2. Process watchlist updates after trade execution
3. Call `add_to_watchlist()` for each new symbol (priority=5)
4. Call `remove_from_watchlist()` for each removed symbol
5. Log changes to trades.db with reason "Performance-based rotation"

**And** SHALL NOT delay trade execution for watchlist updates

---

