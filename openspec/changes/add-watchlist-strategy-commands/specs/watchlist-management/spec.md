# watchlist-management Specification Deltas

## ADDED Requirements

### Requirement: Display Current Watchlist

The system SHALL provide a `/trade:watchlist` slash command that displays all symbols currently being monitored with their priority levels, data freshness indicators, and cache statistics.

**Priority:** MUST
**Impact:** Core UX for watchlist visibility

#### Scenario: View watchlist with varied data freshness

**Given** watchlist database contains 5 symbols:
- AAPL (priority=1, data updated 1 hour ago, 58,968 bars)
- MSFT (priority=2, data updated 2 hours ago, 58,968 bars)
- QQQ (priority=3, data updated 30 minutes ago, 58,968 bars)
- TSLA (priority=5, data updated 5 days ago, 45,234 bars)
- NVDA (priority=5, data updated 1 hour ago, 58,968 bars)

**When** user executes `/trade:watchlist`

**Then** the system SHALL display:
- Table with columns: Symbol, Priority, Status, Latest Data, Total Bars
- Data freshness indicators:
  - ✓ GOOD: Data within last 24 hours (AAPL, MSFT, QQQ, NVDA)
  - ⚠ STALE: Data 1-7 days old (TSLA)
  - ✗ CRITICAL: Data >7 days old or missing
- Sorted by priority (1=highest, 10=lowest)
- Summary line: "Total: 5 symbols | Data Status: 4 GOOD, 1 STALE, 0 CRITICAL"

#### Scenario: Empty watchlist

**Given** watchlist database is empty (no symbols added yet)

**When** user executes `/trade:watchlist`

**Then** the system SHALL display:
- "Watchlist is empty"
- Helpful suggestion: "Add symbols with: /trade:watchlist-add SYMBOL"

---

### Requirement: Add Symbols to Watchlist

The system SHALL provide a `/trade:watchlist-add` slash command to add one or more symbols to monitoring with optional priority and notes.

**Priority:** MUST
**Impact:** Core UX for watchlist management

#### Scenario: Add single symbol with default priority

**Given** watchlist does not contain symbol GOOGL
**And** GOOGL is a valid ticker format (uppercase, 2-5 letters)

**When** user executes `/trade:watchlist-add GOOGL`

**Then** the system SHALL:
- Add GOOGL to watchlist database with `priority=5` (default)
- Set `is_active=true` and record `added_at` timestamp
- Display: "✓ Added GOOGL to watchlist (priority=5)"
- Suggest next step: "Run backfill: python scripts/backfill_historical_data.py --symbols GOOGL --days 1095"

#### Scenario: Add multiple symbols with custom priority and notes

**Given** watchlist does not contain symbols GOOGL or META

**When** user executes `/trade:watchlist-add GOOGL META --priority 3 --notes "Tech sector expansion"`

**Then** the system SHALL:
- Add both GOOGL and META with `priority=3`
- Store notes "Tech sector expansion" for both symbols
- Set `is_active=true` for both
- Display success message for each symbol
- Suggest backfill for both symbols

#### Scenario: Update existing symbol priority

**Given** watchlist contains AAPL with `priority=5`

**When** user executes `/trade:watchlist-add AAPL --priority 1`

**Then** the system SHALL:
- Update AAPL's priority from 5 to 1 (not create duplicate)
- Display: "ℹ AAPL already in watchlist. Updated priority: 5 → 1"
- Preserve existing cached data

#### Scenario: Reject invalid ticker format

**Given** user provides invalid ticker "abc" (lowercase)

**When** user executes `/trade:watchlist-add abc`

**Then** the system SHALL:
- Reject with error: "Error: 'abc' is not a valid ticker format (must be 2-5 uppercase letters)"
- Not modify database

---

### Requirement: Remove Symbols from Watchlist

The system SHALL provide a `/trade:watchlist-remove` slash command to stop monitoring one or more symbols with safety checks for active positions.

**Priority:** MUST
**Impact:** Core UX with risk management safeguards

#### Scenario: Remove symbol without active positions

**Given** watchlist contains TSLA
**And** TSLA has no active positions in IBKR account

**When** user executes `/trade:watchlist-remove TSLA`

**Then** the system SHALL:
- Set `is_active=false` for TSLA (soft delete)
- Preserve all cached historical data (58,968 bars remain in database)
- Record `removed_at` timestamp
- Display: "✓ Removed TSLA from watchlist (soft delete)"
- Confirm: "Historical data preserved (58,968 bars)"

#### Scenario: Prevent removal of symbol with active positions

**Given** watchlist contains AAPL
**And** AAPL has 2 active positions in IBKR:
  - Iron Condor expiring 2025-11-29 (P&L: +$125)
  - Bull Put Spread expiring 2025-12-06 (P&L: -$50)

**When** user executes `/trade:watchlist-remove AAPL`

**Then** the system SHALL:
- Check IBKR for active positions via `mcp__ibkr__get_positions(symbol='AAPL')`
- Block removal without `--force` flag
- Display warning:
  ```
  ⚠ Warning: AAPL has 2 active positions:
    - Iron Condor expiring 2025-11-29 (P&L: +$125)
    - Bull Put Spread expiring 2025-12-06 (P&L: -$50)

  Removal cancelled. Use --force to remove despite active positions.
  ```
- Not modify database

#### Scenario: Force remove symbol with active positions

**Given** watchlist contains AAPL with 2 active positions
**And** user explicitly adds `--force` flag

**When** user executes `/trade:watchlist-remove AAPL --force`

**Then** the system SHALL:
- Set `is_active=false` for AAPL
- Preserve cached data
- Display:
  ```
  ✓ Removed AAPL from watchlist (soft delete)
    - Historical data preserved (58,968 bars)
    - Active positions: 2 (you are responsible for managing these)
  ```

#### Scenario: Attempt to remove non-existent symbol

**Given** watchlist does not contain symbol XYZQ

**When** user executes `/trade:watchlist-remove XYZQ`

**Then** the system SHALL:
- Display error: "Error: XYZQ is not in the watchlist"
- Not modify database
