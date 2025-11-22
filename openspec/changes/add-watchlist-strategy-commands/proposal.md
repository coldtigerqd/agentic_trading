# Proposal: Add Watchlist and Strategy Management Slash Commands

## Change ID
`add-watchlist-strategy-commands`

## Problem Statement

Currently, users must manually call Python skills or run scripts to manage the watchlist and swarm strategy instances. There is no convenient slash command interface similar to `/trade:analyze` for:

1. **Watchlist Management**: Adding/removing symbols, viewing current watchlist
2. **Strategy Pool Management**: Viewing active strategies, enabling/disabling strategy instances
3. **Symbol-Strategy Analysis**: Running specific strategies against specific symbols

This creates friction in the user workflow and reduces the system's usability compared to the existing `/trade:*` command family.

## Proposed Solution

Add a comprehensive set of slash commands under `/trade:` namespace to manage watchlist and strategy operations:

### Watchlist Commands
- `/trade:watchlist` - Display current watchlist with data status
- `/trade:watchlist-add` - Add symbol(s) to watchlist with priority
- `/trade:watchlist-remove` - Remove symbol(s) from watchlist

### Strategy Commands
- `/trade:strategies` - List all active swarm strategy instances
- `/trade:strategy-enable` - Enable a strategy instance
- `/trade:strategy-disable` - Disable a strategy instance
- `/trade:analyze-symbol` - Run specific strategy against specific symbol

## Scope

This change affects:
- **Slash Commands** (`.claude/commands/trade/`): New command definitions
- **Skills Library** (`skills/`): Ensure watchlist/swarm management functions are exposed
- **Documentation** (`README.md`): Update command reference

## Dependencies

- Existing watchlist management functions in `skills/market_data.py`
- Existing swarm instance management in `swarm_intelligence/active_instances/`
- Existing `/trade:*` command patterns

## Success Criteria

1. ✅ Users can add/remove watchlist symbols via slash commands
2. ✅ Users can view current watchlist with data freshness indicators
3. ✅ Users can list all active strategy instances
4. ✅ Users can enable/disable strategy instances without editing JSON
5. ✅ Users can run specific strategies against specific symbols for testing
6. ✅ All commands follow consistent `/trade:` namespace pattern
7. ✅ Error handling provides clear feedback for invalid operations

## Non-Goals

- Modifying strategy template logic (only instance enable/disable)
- Creating new strategy templates via commands
- Batch operations beyond basic add/remove
- GUI or web interface (CLI commands only)

## Timeline Estimate

- **Design & Spec**: 30 minutes
- **Implementation**: 2-3 hours
- **Testing**: 1 hour
- **Documentation**: 30 minutes
- **Total**: ~4-5 hours

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Command naming conflicts with existing `/trade:*` | Follow established patterns, verify no collisions |
| Strategy enable/disable corrupts JSON | Use atomic file operations, validate JSON before write |
| Watchlist changes break ongoing backfill | Document that changes only affect future syncs |
| Over-complexity in command arguments | Keep commands simple, use interactive prompts when needed |

## Related Changes

None (standalone feature)

## Approval Required

- [ ] Architecture review
- [ ] Security review (watchlist/strategy modifications)
- [ ] UX review (command naming and parameters)
