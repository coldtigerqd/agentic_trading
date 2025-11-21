# Proposal: Localize System to Chinese (系统中文化)

**Change ID**: `localize-to-chinese`
**Status**: Draft
**Branch**: `feature/chinese-localization`
**Created**: 2025-11-21

## Summary (概要)

Comprehensively localize the Agentic AlphaHive Runtime system to Chinese, including all prompts, system messages, user-facing strings, logging output, and core workflow documentation. This will make the system fully accessible to Chinese-speaking users and operators, while maintaining English as a fallback for technical terms where appropriate.

全面将 Agentic AlphaHive Runtime 系统本地化为中文，包括所有提示词、系统消息、用户界面字符串、日志输出和核心工作流文档。这将使系统完全适配中文使用者和操作人员，同时在适当情况下保留英文作为技术术语的备选。

## Motivation (动机)

### Current State (现状)
- All system prompts are in English (`prompts/commander_system.md`)
- Swarm strategy templates are entirely in English (`swarm_intelligence/templates/*.md`)
- Python logging, print statements, and error messages are in English
- Documentation and inline comments mix English and Chinese
- User-facing output from skills and MCP servers is English-only

### Problem (问题)
- Chinese-speaking operators must mentally translate system behavior
- Debugging and monitoring require English comprehension
- Strategy templates are less accessible to Chinese analysts
- Mixed language documentation creates cognitive overhead
- Log analysis and incident response slower for Chinese teams

### Desired State (期望状态)
- **Commander System Prompt**: Fully localized with Chinese instructions
- **Swarm Templates**: All strategy descriptions and analysis prompts in Chinese
- **Skills Output**: Print statements, logging, and status messages in Chinese
- **Error Messages**: Validation errors, safety rejections, and exceptions in Chinese
- **Documentation**: Core workflow docs (README, QUICKSTART) bilingual or Chinese-primary
- **Code Comments**: Technical comments in Chinese where beneficial
- **Technical Terms**: Retain English for domain-specific terms (e.g., "PUT_SPREAD", "OHLC")

## Scope (范围)

### In Scope (包含)
1. **System Prompts Localization** (`prompts/`)
   - Commander system prompt (`commander_system.md`)
   - All instructions, examples, and workflow descriptions

2. **Swarm Intelligence Localization** (`swarm_intelligence/templates/`)
   - All 5 strategy templates: `trend_scout.md`, `vol_sniper.md`, `mean_reversion.md`, `breakout_scout.md`, `correlation_arbitrage.md`
   - Strategy descriptions, analysis frameworks, decision criteria

3. **Skills Output Localization** (`skills/`)
   - All `print()` statements for status messages
   - All `logger.info/warning/error()` calls
   - User-facing return messages in skill functions
   - Comments and docstrings in critical user-facing modules

4. **Validation & Error Messages**
   - Safety validator rejection messages (`mcp-servers/ibkr/safety.py`)
   - Order validation errors (`skills/execution_gate.py`)
   - Data quality validation messages (`skills/data_quality.py`)

5. **Core Documentation** (Bilingual Approach)
   - `README.md`: Chinese-primary with English sections for technical setup
   - `QUICKSTART.md`: Fully Chinese
   - `CLAUDE.md`: Bilingual (instructions for both languages)

### Out of Scope (不包含)
- MCP server internal code (low-level protocol handling)
- Third-party library code
- English-only technical documentation (e.g., OpenSpec AGENTS.md)
- Test file content (tests remain English for code consistency)
- Git commit messages (keep English for international collaboration)

### Guiding Principles (指导原则)
1. **Preserve Technical Fidelity**: Keep English terms for financial/trading concepts where no standard Chinese translation exists
2. **User-First**: Prioritize user-facing strings (prompts, logs, errors) over internal code comments
3. **Consistency**: Use standardized translations for recurring terms (e.g., "swarm" → "蜂群", "signal" → "信号")
4. **Maintainability**: Document translation choices for future contributors
5. **Incremental Validation**: Test each category of changes independently

## Dependencies (依赖)

- No external dependencies required
- No breaking changes to APIs or data structures
- Compatible with existing MCP servers and IBKR integration
- No schema changes to `trades.db` or data lake

## Risks & Mitigations (风险与缓解)

| Risk | Impact | Mitigation |
|------|--------|------------|
| Translation accuracy for financial terms | Medium | Create glossary, review with domain expert |
| Mixed-language debugging confusion | Low | Keep English variable/function names |
| Prompt engineering sensitivity to language | High | Extensively test Commander behavior with Chinese prompts |
| Character encoding issues in logs | Low | Ensure UTF-8 encoding throughout |
| Length variations in UI messages | Low | Test output formatting with longer Chinese strings |

## Success Criteria (成功标准)

1. ✅ Commander executes full trading cycle with Chinese-language reasoning
2. ✅ Swarm templates generate signals with Chinese explanations
3. ✅ All user-facing logs and errors display in Chinese
4. ✅ Safety validator rejects orders with Chinese error messages
5. ✅ README and QUICKSTART are accessible to Chinese-only speakers
6. ✅ No functional regressions in trading logic or safety checks

## Related Changes (相关变更)

- None (this is a standalone localization effort)

## Open Questions (未解决问题)

1. Should we create a language configuration option (`config.language = "zh-CN"`) or hard-code Chinese?
   - **Recommendation**: Hard-code Chinese in this change, add i18n framework in future if needed

2. How to handle bilingual error messages for debugging (e.g., include English in parentheses)?
   - **Recommendation**: Chinese primary, English technical IDs (e.g., "订单被拒绝 (RISK_EXCEEDED)")

3. Should variable names in JSON configs be translated?
   - **Recommendation**: Keep English (e.g., `symbol_pool`, not `符号池`)

4. Translation for "Commander" - 指挥官 or 司令官?
   - **Recommendation**: 指挥官 (more commonly used in tech contexts)
