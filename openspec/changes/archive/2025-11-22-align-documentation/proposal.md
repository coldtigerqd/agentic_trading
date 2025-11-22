# Proposal: Align Documentation with Implementation Reality

## Summary

Comprehensive cleanup and realignment of project documentation to accurately reflect the current implementation state of Agentic AlphaHive. This includes updating README.md and project.md to match actual code, consolidating redundant data persistence code, unifying data sync pathways, and removing obsolete files.

## Background

The project has evolved significantly from its original design, but documentation has not kept pace. This creates confusion about actual capabilities, running modes, and system architecture.

### Current State Problems

1. **Interaction Model Mismatch**
   - README describes automatic 5-minute loop via `main_loop.py`
   - **Reality**: System now uses manual command-triggered trading analysis in Claude Code
   - Impact: Users expect wrong behavior

2. **Watchdog Function Confusion**
   - README describes heartbeat monitoring
   - **Reality**: Heartbeat monitoring no longer needed; should merge data sync + account monitoring
   - Impact: Two separate daemons when one would suffice

3. **Data Sync Path Chaos**
   - Multiple redundant scripts: `sync_with_rest_api.py`, `run_sync_once.py`, `demo_incremental_sync.py`
   - Unclear primary path (slash command vs REST API vs skills)
   - Impact: Confusing entry points, duplicate code

4. **Data Persistence Code Duplication**
   - `DB_PATH` defined 3 times
   - `get_db_connection()` implemented 3 different ways with inconsistent error handling
   - Impact: Maintenance burden, potential bugs

5. **Documented but Unimplemented Features**
   - `dream_lab/` directory doesn't exist
   - Genetic algorithm optimizer not implemented
   - News sentiment MCP server incomplete
   - Impact: False expectations

6. **Migration Not Documented**
   - Shift from MCP ThetaData to REST API undocumented
   - Rationale for changes missing
   - Impact: Confusion about which approach to use

## Goals

1. **Accuracy**: Documentation precisely matches implementation
2. **Clarity**: Clear distinction between implemented, deprecated, and planned features
3. **Maintainability**: Eliminate code duplication, establish single source of truth
4. **Usability**: Users understand how to actually run and use the system

## Proposed Changes

### 1. Restructure README.md

Transform from "aspirational spec" to "current reality documentation":

**New Structure**:
- §1 System Overview - What the system IS today (manual command-triggered analysis)
- §2 Architecture - Actual implemented components only
- §3 Setup & Installation - Step-by-step user guide
- §4 Usage Guide - How to trigger trading analysis via slash commands
- §5 Development Guide - Skills library, adding strategies, testing
- §6 Roadmap - Clearly labeled future features (Dream Lab, News Sentiment, etc.)

**Remove**:
- References to automatic main loop
- Dream Lab detailed descriptions (move to Roadmap)
- Heartbeat monitoring descriptions
- Redundant script documentation

**Add**:
- Slash command usage examples
- Workflow skills documentation
- REST API vs MCP clarification

### 2. Update openspec/project.md

**Update Tech Stack**:
- Clarify ThetaData uses REST API (not MCP)
- Document actual MCP servers: IBKR only
- Update operational constraints for manual mode

**Update Architecture Patterns**:
- Document slash command → skills pathway
- Clarify Commander invocation model
- Remove heartbeat monitoring references

### 3. Consolidate Data Persistence Layer

**Create**: `data_lake/db_config.py`
- Unified `DB_PATH` definition
- Single `get_db_connection()` with context manager
- Consistent PRAGMA settings (WAL, NORMAL sync)

**Refactor**:
- `db_helpers.py` - import from db_config
- `market_data_manager.py` - import from db_config, convert to context managers
- `seed_watchlist.py` - import from db_config

**Create**: `data_lake/__init__.py`
- Unified public API for data persistence layer

### 4. Unify Data Sync Pathway

**Primary Path**: Slash command → `skills/workflow_skills.py`
- Document this as the main entry point
- Create corresponding slash command

**Secondary Path**: Background daemon (non-trading hours)
- Keep `runtime/data_sync_daemon.py` for automated syncing
- Document as supplementary, not primary

**Remove**:
- `scripts/sync_with_rest_api.py` (redundant)
- `scripts/run_sync_once.py` (redundant)
- Keep `scripts/demo_incremental_sync.py` as example only

### 5. Reorganize Watchdog Functions

**Merge** `runtime/watchdog.py` + `runtime/data_sync_daemon.py`:
- Account drawdown monitoring (keep)
- Data sync during non-trading hours (integrate)
- Heartbeat monitoring (remove - not needed for manual mode)

**New unified daemon**:
- Monitors account for circuit breakers
- Performs background data sync
- Single process, clear responsibilities

### 6. Create Migration Documentation

**New file**: `MIGRATION.md`
- Document MCP → REST API shift for ThetaData
- Document automatic loop → manual command shift
- Document rationale and benefits
- Provide migration guide for any legacy users

### 7. Clean Up Obsolete Files

**Archive or Delete**:
- `docs/enhance_plan.md` (internal discussion, not user docs)
- `main_loop.py` → move to `runtime/legacy/` with deprecation note
- Redundant sync scripts (see §4)
- Empty or placeholder test files

**Relocate**:
- `IBKR_CONNECTION_TEST_SUMMARY.md` → `mcp-servers/ibkr/docs/`

## Non-Goals

- No changes to actual functionality (documentation only + code consolidation)
- No new features (only documenting existing)
- No breaking API changes to skills or MCP servers

## Success Criteria

1. ✅ Every feature in README is actually implemented
2. ✅ Every implemented feature is documented in README
3. ✅ Clear separation: "Current" vs "Roadmap" sections
4. ✅ Single `get_db_connection()` implementation
5. ✅ Primary data sync path clearly documented
6. ✅ `openspec validate` passes with no errors
7. ✅ No redundant code in `data_lake/`
8. ✅ Migration documentation explains architectural shifts

## Timeline & Approach

**Phase 1**: Code consolidation (data persistence, sync pathways)
**Phase 2**: Documentation updates (README, project.md, MIGRATION.md)
**Phase 3**: File cleanup and reorganization
**Phase 4**: Validation and testing

## Open Questions

1. Should `main_loop.py` be deleted or moved to `runtime/legacy/`? (Recommend: legacy)
2. Should we create a single unified daemon or keep watchdog + data_sync separate? (Recommend: unified)
3. Keep `docs/` directory or flatten to root-level markdown files? (Recommend: flatten or remove)

## Dependencies

- No external dependencies
- No API changes
- Safe to implement on current branch: `docs/cleanup-and-align-with-implementation`

## Related Issues

- Resolves documentation-code mismatch
- Addresses user confusion about running modes
- Improves maintainability via code consolidation
