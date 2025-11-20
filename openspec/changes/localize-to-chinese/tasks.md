# Tasks: Chinese Localization Implementation

## Overview (概述)

This file outlines the ordered task list for implementing comprehensive Chinese localization. Tasks are grouped by capability and sequenced to minimize dependencies while delivering incremental user value.

**Execution Strategy**:
- Complete tasks sequentially within each phase
- Validate after each task before proceeding
- Commit frequently with descriptive messages

---

## Phase 1: Prompts & Templates (Week 1)

### Task 1.1: Create Translation Glossary
**Status**: Pending
**Assignee**: TBD
**Effort**: 2 hours

**Description**: Create `docs/translation_glossary.md` with standardized Chinese translations for all recurring terms.

**Deliverables**:
- Glossary file with 50+ term mappings
- Examples of correct usage for ambiguous terms
- Guidelines for preserving technical terms in English

**Validation**:
- [ ] Review glossary with domain expert
- [ ] Confirm no conflicting translations
- [ ] Verify all terms from prompts covered

---

### Task 1.2: Translate Commander System Prompt
**Status**: Pending
**Assignee**: TBD
**Effort**: 4 hours
**Depends on**: Task 1.1

**Description**: Translate `prompts/commander_system.md` to Chinese following glossary standards.

**Deliverables**:
- Fully translated Commander prompt
- All code examples tested for syntax validity
- Translation notes for ambiguous sections

**Validation**:
- [ ] Run Commander cycle with Chinese prompt
- [ ] Verify LLM generates coherent reasoning
- [ ] Confirm all Python code snippets execute
- [ ] Check Jinja2 variables unchanged

**Commands**:
```bash
# Test Commander workflow
python -c "from skills import consult_swarm; print(consult_swarm('TECH'))"
```

---

### Task 1.3: Translate Trend Scout Template
**Status**: Pending
**Assignee**: TBD
**Effort**: 2 hours
**Depends on**: Task 1.1

**Description**: Translate `swarm_intelligence/templates/trend_scout.md`.

**Deliverables**:
- Translated template with preserved Jinja2 syntax
- Tested template rendering

**Validation**:
- [ ] Render template with test parameters
- [ ] Verify Chinese output is coherent
- [ ] Confirm Jinja2 variables unchanged
- [ ] Test swarm signal generation

---

### Task 1.4: Translate Vol Sniper Template
**Status**: Pending
**Assignee**: TBD
**Effort**: 2 hours
**Depends on**: Task 1.1

**Description**: Translate `swarm_intelligence/templates/vol_sniper.md`.

**Deliverables**: Same as Task 1.3

**Validation**: Same as Task 1.3

---

### Task 1.5: Translate Mean Reversion Template
**Status**: Pending
**Assignee**: TBD
**Effort**: 2 hours
**Depends on**: Task 1.1

**Description**: Translate `swarm_intelligence/templates/mean_reversion.md`.

**Deliverables**: Same as Task 1.3

**Validation**: Same as Task 1.3

---

### Task 1.6: Translate Breakout Scout Template
**Status**: Pending
**Assignee**: TBD
**Effort**: 2 hours
**Depends on**: Task 1.1

**Description**: Translate `swarm_intelligence/templates/breakout_scout.md`.

**Deliverables**: Same as Task 1.3

**Validation**: Same as Task 1.3

---

### Task 1.7: Translate Correlation Arbitrage Template
**Status**: Pending
**Assignee**: TBD
**Effort**: 2 hours
**Depends on**: Task 1.1

**Description**: Translate `swarm_intelligence/templates/correlation_arbitrage.md`.

**Deliverables**: Same as Task 1.3

**Validation**: Same as Task 1.3

---

### Task 1.8: Integration Test - Full Swarm Consultation
**Status**: Pending
**Assignee**: TBD
**Effort**: 1 hour
**Depends on**: Tasks 1.3-1.7

**Description**: Test `consult_swarm()` with all translated templates to verify end-to-end workflow.

**Validation**:
- [ ] All 5 strategy instances generate signals
- [ ] Chinese reasoning fields are present
- [ ] JSON structure matches schema
- [ ] No template rendering errors

**Commands**:
```bash
python -c "
from skills import consult_swarm
signals = consult_swarm('ALL', max_concurrent=5)
print(f'Generated {len(signals)} signals')
for sig in signals:
    assert 'reasoning' in sig, 'Missing reasoning field'
    assert sig['confidence'] is not None
"
```

---

## Phase 2: Skills Output (Week 2)

### Task 2.1: Localize Market Data Skills
**Status**: Pending
**Assignee**: TBD
**Effort**: 3 hours
**Depends on**: Task 1.1

**Description**: Translate print statements, logs, and docstrings in `skills/market_data.py`.

**Deliverables**:
- All print statements in Chinese
- All logger calls in Chinese with English error codes
- Docstrings translated with English parameter names
- Variable names unchanged

**Validation**:
- [ ] Run `get_historical_bars()` and verify Chinese output
- [ ] Run `get_latest_price()` and verify Chinese staleness warning
- [ ] Check logs for Chinese messages
- [ ] IDE hover shows Chinese docstring

---

### Task 2.2: Localize Data Sync Skills
**Status**: Pending
**Assignee**: TBD
**Effort**: 2 hours
**Depends on**: Task 1.1

**Description**: Translate `skills/data_sync.py` output messages.

**Deliverables**: Same as Task 2.1

**Validation**:
- [ ] Run `sync_watchlist_incremental()` and verify Chinese progress
- [ ] Trigger error and verify Chinese log message

---

### Task 2.3: Localize Data Quality Skills
**Status**: Pending
**Assignee**: TBD
**Effort**: 2 hours
**Depends on**: Task 1.1

**Description**: Translate `skills/data_quality.py` validation messages.

**Deliverables**: Same as Task 2.1

**Validation**:
- [ ] Trigger data quality failure and verify Chinese report
- [ ] Check recommendations are actionable in Chinese

---

### Task 2.4: Localize Swarm Core Skills
**Status**: Pending
**Assignee**: TBD
**Effort**: 3 hours
**Depends on**: Task 1.1

**Description**: Translate `skills/swarm_core.py` orchestration logs.

**Deliverables**: Same as Task 2.1

**Validation**:
- [ ] Run `consult_swarm()` and verify Chinese status messages
- [ ] Check snapshot filenames unchanged
- [ ] Verify error messages in Chinese

---

### Task 2.5: Localize Execution Gate Skills
**Status**: Pending
**Assignee**: TBD
**Effort**: 3 hours
**Depends on**: Task 1.1

**Description**: Translate `skills/execution_gate.py` validation messages.

**Deliverables**: Same as Task 2.1

**Validation**:
- [ ] Trigger validation error and verify Chinese message
- [ ] Check OrderResult.error contains Chinese + English code

---

### Task 2.6: Localize MCP Bridge Skills
**Status**: Pending
**Assignee**: TBD
**Effort**: 2 hours
**Depends on**: Task 1.1

**Description**: Translate `skills/mcp_bridge.py` IBKR interaction messages.

**Deliverables**: Same as Task 2.1

**Validation**:
- [ ] Test order submission (paper trading)
- [ ] Verify Chinese success/failure messages

---

### Task 2.7: Localize ThetaData Client
**Status**: Pending
**Assignee**: TBD
**Effort**: 2 hours
**Depends on**: Task 1.1

**Description**: Translate `skills/thetadata_client.py` error logs.

**Deliverables**: Same as Task 2.1

**Validation**:
- [ ] Trigger HTTP error and verify Chinese log
- [ ] Check connection error has Chinese guidance

---

### Task 2.8: Localize Remaining Skills
**Status**: Pending
**Assignee**: TBD
**Effort**: 4 hours
**Depends on**: Task 1.1

**Description**: Translate docstrings and messages in:
- `skills/market_calendar.py`
- `skills/watchlist_manager.py`
- `skills/technical_indicators.py`
- `skills/math_core.py`
- `skills/signal_enrichment.py`
- `skills/commander_workflow.py`

**Deliverables**: Same as Task 2.1

**Validation**:
- [ ] Spot-check 3 functions per file for Chinese output
- [ ] Run integration test to catch runtime errors

---

### Task 2.9: Integration Test - Full Trading Cycle
**Status**: Pending
**Assignee**: TBD
**Effort**: 2 hours
**Depends on**: Tasks 2.1-2.8

**Description**: Execute complete SENSE-THINK-DECIDE-ACT cycle and verify all output is in Chinese.

**Validation**:
- [ ] Run Commander workflow end-to-end
- [ ] Verify all console output in Chinese
- [ ] Check log file for Chinese messages
- [ ] Confirm no UnicodeEncodeError

**Commands**:
```bash
# Run full workflow
python runtime/main.py --mode test
```

---

## Phase 3: Validation & Error Messages (Week 3)

### Task 3.1: Localize Safety Validator
**Status**: Pending
**Assignee**: TBD
**Effort**: 3 hours
**Depends on**: Task 1.1

**Description**: Translate rejection messages in `mcp-servers/ibkr/safety.py`.

**Deliverables**:
- All rejection messages in Chinese with English error codes
- Error code registry defined
- Comments translated

**Validation**:
- [ ] Trigger each rejection scenario (8 total)
- [ ] Verify Chinese message with error code
- [ ] Test `grep "RISK_EXCEEDED" logs/*.log`

---

### Task 3.2: Create Error Code Registry
**Status**: Pending
**Assignee**: TBD
**Effort**: 1 hour
**Depends on**: Task 3.1

**Description**: Create `skills/error_codes.py` with standardized error code mappings.

**Deliverables**:
- Python dict with error code -> Chinese message mapping
- Usage examples in docstring

**Validation**:
- [ ] Import error_codes in 3 modules
- [ ] Verify consistent error formatting

---

### Task 3.3: Update All Error Messages to Use Registry
**Status**: Pending
**Assignee**: TBD
**Effort**: 2 hours
**Depends on**: Task 3.2

**Description**: Refactor all error messages across skills/ to use error_codes registry.

**Deliverables**:
- All error messages use `error_codes[CODE]` format
- Consistent parenthetical error codes

**Validation**:
- [ ] Grep for hardcoded English error messages (should find none)
- [ ] Trigger errors and verify format consistency

---

### Task 3.4: Localize Order Validation Errors
**Status**: Pending
**Assignee**: TBD
**Effort**: 2 hours
**Depends on**: Task 3.2

**Description**: Translate order validation errors in `execution_gate.py`.

**Deliverables**: Same as Task 3.1

**Validation**:
- [ ] Submit order with missing field -> Chinese error
- [ ] Submit order with invalid strike -> Chinese error
- [ ] Submit order with invalid expiry -> Chinese error

---

### Task 3.5: Integration Test - Error Scenarios
**Status**: Pending
**Assignee**: TBD
**Effort**: 2 hours
**Depends on**: Tasks 3.1-3.4

**Description**: Systematically trigger all error scenarios and verify Chinese messages.

**Validation**:
- [ ] Create test script that triggers 15+ error scenarios
- [ ] Verify all errors display in Chinese
- [ ] Confirm error codes are grep-able
- [ ] Check `trades.db` rejection reasons

---

## Phase 4: Documentation (Week 4)

### Task 4.1: Translate README.md (Bilingual)
**Status**: Pending
**Assignee**: TBD
**Effort**: 4 hours
**Depends on**: Task 1.1

**Description**: Create bilingual README with Chinese-primary structure.

**Deliverables**:
- Chinese system overview
- Chinese feature list
- Bilingual installation instructions
- English troubleshooting section

**Validation**:
- [ ] Render in GitHub preview
- [ ] Verify all links work
- [ ] Test installation commands
- [ ] Check Chinese clarity with native speaker

---

### Task 4.2: Translate QUICKSTART.md (Full Chinese)
**Status**: Pending
**Assignee**: TBD
**Effort**: 3 hours
**Depends on**: Task 1.1

**Description**: Fully translate QUICKSTART.md to Chinese.

**Deliverables**:
- All steps in Chinese
- Chinese comments in code examples
- Chinese troubleshooting tips

**Validation**:
- [ ] Have tester follow guide from scratch
- [ ] Verify each step is actionable
- [ ] Confirm no English-only blockers

---

### Task 4.3: Add Chinese Inline Comments to Critical Modules
**Status**: Pending
**Assignee**: TBD
**Effort**: 3 hours
**Depends on**: Task 1.1

**Description**: Add Chinese comments to complex logic in:
- `skills/execution_gate.py` (validation logic)
- `skills/data_quality.py` (quality checks)
- `mcp-servers/ibkr/safety.py` (safety limits)

**Deliverables**:
- 20-30 Chinese comments added
- No misleading translations

**Validation**:
- [ ] Code review for clarity
- [ ] Verify comments match code behavior

---

### Task 4.4: Update CLAUDE.md References (Minimal)
**Status**: Pending
**Assignee**: TBD
**Effort**: 0.5 hours
**Depends on**: Task 1.2

**Description**: Update CLAUDE.md to reference Chinese Commander prompt if needed.

**Deliverables**:
- Updated prompt reference line
- No functional changes

**Validation**:
- [ ] Load CLAUDE.md in Claude Code
- [ ] Verify AI understands instructions

---

### Task 4.5: Integration Test - Documentation Walkthrough
**Status**: Pending
**Assignee**: TBD
**Effort**: 2 hours
**Depends on**: Tasks 4.1-4.4

**Description**: Have Chinese-speaking tester follow documentation end-to-end.

**Validation**:
- [ ] Tester completes setup using Chinese docs
- [ ] No English-only blockers encountered
- [ ] All commands execute successfully
- [ ] Tester provides clarity feedback

---

## Phase 5: Final Validation & Cleanup (Week 5)

### Task 5.1: UTF-8 Encoding Audit
**Status**: Pending
**Assignee**: TBD
**Effort**: 1 hour
**Depends on**: All previous tasks

**Description**: Verify UTF-8 encoding across all files.

**Deliverables**:
- `.gitattributes` configured for UTF-8
- Python files have `# -*- coding: utf-8 -*-` if needed
- Test encoding on multiple terminals

**Validation**:
- [ ] Test on macOS Terminal
- [ ] Test on Linux xterm
- [ ] Verify no UnicodeEncodeError in any scenario

**Commands**:
```bash
# Check encoding
file -i skills/*.py | grep -v utf-8

# Test terminal output
python -c "from skills import sync_watchlist_incremental; sync_watchlist_incremental()"
```

---

### Task 5.2: Regression Testing - Full System
**Status**: Pending
**Assignee**: TBD
**Effort**: 4 hours
**Depends on**: Task 5.1

**Description**: Run full regression test suite to ensure no functional breakage.

**Test Checklist**:
- [ ] Commander full cycle (SENSE-THINK-DECIDE-ACT)
- [ ] Swarm consultation with all 5 strategies
- [ ] Order validation (10 scenarios)
- [ ] Safety validator (8 rejection scenarios)
- [ ] Data sync and quality checks
- [ ] MCP server integration (IBKR, ThetaData)
- [ ] Error handling (15 scenarios)
- [ ] Watchdog circuit breaker

**Validation**:
- [ ] All tests pass
- [ ] No encoding errors
- [ ] Performance unchanged (cycle latency < 30s)
- [ ] Log files readable

**Commands**:
```bash
# Run pytest suite
pytest skills/tests/ -v
pytest mcp-servers/ibkr/tests/ -v

# Run manual integration test
python runtime/main.py --mode test --cycles 3
```

---

### Task 5.3: Documentation Review by Native Speaker
**Status**: Pending
**Assignee**: TBD (Chinese-speaking domain expert)
**Effort**: 2 hours
**Depends on**: Task 4.5

**Description**: Have native Chinese speaker review all translated content for accuracy and clarity.

**Review Scope**:
- Commander prompt
- All 5 swarm templates
- Error messages
- Documentation (README, QUICKSTART)

**Deliverables**:
- Review feedback document
- List of corrections needed

**Validation**:
- [ ] All feedback addressed
- [ ] No technical inaccuracies
- [ ] No misleading translations

---

### Task 5.4: Create Translation Maintenance Guide
**Status**: Pending
**Assignee**: TBD
**Effort**: 2 hours
**Depends on**: Task 5.3

**Description**: Create `docs/translation_maintenance.md` with guidelines for future updates.

**Deliverables**:
- Guide for translating new prompts
- Error code naming conventions
- Examples of good/bad translations
- Update checklist for adding new features

**Validation**:
- [ ] Review by 2 team members
- [ ] Add to onboarding docs

---

### Task 5.5: OpenSpec Validation & Archival
**Status**: Pending
**Assignee**: TBD
**Effort**: 1 hour
**Depends on**: Task 5.2

**Description**: Validate OpenSpec change and prepare for archival.

**Commands**:
```bash
# Validate change
openspec validate localize-to-chinese --strict

# Show change summary
openspec show localize-to-chinese --deltas-only

# Archive (after approval)
openspec archive localize-to-chinese
```

**Validation**:
- [ ] No validation errors
- [ ] All scenarios pass
- [ ] Ready for archival

---

### Task 5.6: Git Commit & PR
**Status**: Pending
**Assignee**: TBD
**Effort**: 1 hour
**Depends on**: Task 5.5

**Description**: Create final commit and pull request.

**Deliverables**:
- Descriptive commit message
- PR with checklist of completed items
- Screenshots of Chinese output

**Commands**:
```bash
# Commit all changes
git add .
git commit -m "feat: comprehensive Chinese localization

Localize all prompts, skills output, error messages, and documentation to Chinese.

Core changes:
- Commander system prompt fully translated
- All 5 swarm strategy templates translated
- Skills print/log output in Chinese
- Error messages with English error codes
- Bilingual README, full Chinese QUICKSTART

Testing:
- Full Commander cycle executed successfully
- All swarm strategies generate signals with Chinese reasoning
- Safety validator rejects orders with Chinese messages
- No encoding errors on macOS/Linux terminals

Closes #<issue_number>

🤖 Generated with OpenSpec
"

# Push branch
git push origin feature/chinese-localization

# Create PR (via gh CLI or web interface)
gh pr create --title "feat: 系统全面中文化 (Comprehensive Chinese Localization)" \
  --body "详见 openspec/changes/localize-to-chinese/proposal.md"
```

**Validation**:
- [ ] PR passes CI checks
- [ ] All tasks marked complete
- [ ] Documentation links work in PR

---

## Summary Statistics

**Total Tasks**: 31
**Estimated Effort**: ~60 hours (3 weeks with 1 full-time contributor)
**Phases**: 5
**Test Tasks**: 6 (integration tests)

**Parallel Opportunities**:
- Phase 1 Tasks 1.3-1.7 can be done concurrently (5 template translations)
- Phase 2 Tasks 2.1-2.8 can be split across 2 contributors (10 skills files)
- Phase 4 Tasks 4.1-4.3 can be done concurrently (documentation + comments)

**Critical Path**:
1. Task 1.1 (Glossary) → Blocks all translation tasks
2. Task 1.2 (Commander prompt) → Blocks integration testing
3. Task 5.2 (Regression testing) → Blocks final sign-off
