# Capability: Swarm Intelligence

**Version:** 1.0.0
**Status:** Proposed
**Owner:** Core Runtime Team

## Overview

Swarm Intelligence provides template-based strategy definitions and JSON-based instance configurations, enabling parameter-logic separation and concurrent multi-agent analysis.

## ADDED Requirements

### Requirement: Template-Based Strategy Logic
**Priority:** MUST
**Category:** Architecture

The system MUST support Jinja2 Markdown templates that define trading strategy logic independently from parameters.

#### Scenario: Render template with instance parameters

**Given** Template `vol_sniper.md` exists with placeholders `{{ min_iv_rank }}`, `{{ symbol_pool }}`
**When** Instance `tech_aggressive.json` specifies `{"min_iv_rank": 80, "symbol_pool": ["NVDA", "AMD"]}`
**Then** swarm_core renders complete prompt with values injected

**Verification:**
- Templates stored in `swarm_intelligence/templates/*.md`
- Jinja2 syntax for parameter injection
- Rendered prompt contains no unfilled placeholders

### Requirement: JSON Instance Configuration
**Priority:** MUST
**Category:** Configuration

Each swarm instance MUST be defined in a JSON file containing template reference and parameters.

#### Scenario: Load active instance configuration

**Given** File `swarm_intelligence/active_instances/tech_aggressive.json` exists
**When** System loads instance configuration
**Then** configuration contains:
```json
{
  "id": "tech_aggressive",
  "template": "vol_sniper.md",
  "parameters": {
    "symbol_pool": ["NVDA", "AMD", "TSLA"],
    "min_iv_rank": 80,
    "max_delta_exposure": 0.30
  }
}
```

**Verification:**
- All instances in `active_instances/` directory
- Each has unique `id` field
- Template file exists in `templates/`

### Requirement: Concurrent Instance Execution
**Priority:** MUST
**Category:** Performance

The system MUST execute multiple swarm instances concurrently using asyncio.

#### Scenario: Execute 10 instances concurrently

**Given** 10 active instance configurations exist
**When** `consult_swarm()` is invoked
**Then** all 10 LLM API calls execute concurrently
**And** total execution time < 30 seconds

**Verification:**
- Uses `asyncio.gather()` for concurrent execution
- Configurable `max_concurrent` parameter
- Implements timeout per instance (default 20s)

## Cross-Capability Dependencies

- **Used by**: `skills-library` (swarm_core skill)
- **Requires**: `data-persistence` for snapshot storage
