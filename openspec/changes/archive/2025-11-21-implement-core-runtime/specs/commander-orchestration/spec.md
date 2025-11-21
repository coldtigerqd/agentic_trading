# Capability: Commander Orchestration

**Version:** 1.0.0
**Status:** Proposed
**Owner:** Core Runtime Team

## Overview

Commander Orchestration defines the system prompt and decision-making workflow for the Claude Code agent that serves as the central orchestrator.

## ADDED Requirements

### Requirement: Commander System Prompt
**Priority:** MUST
**Category:** Core Functionality

The system MUST provide a comprehensive system prompt that defines Commander's role, workflow, and constraints.

#### Scenario: Commander follows trading cycle workflow

**Given** Commander loads system prompt from `prompts/commander_system.md`
**When** Trading cycle begins
**Then** Commander executes workflow:
1. Sense: Query account state and market data
2. Think: Invoke swarm for analysis
3. Decide: Evaluate signals with risk management
4. Act: Submit orders through execution gate

**Verification:**
- System prompt stored in `prompts/commander_system.md`
- Workflow clearly documented in prompt
- Safety constraints emphasized
- No direct code generation for orders allowed

### Requirement: Signal Evaluation Logic
**Priority:** MUST
**Category:** Decision Making

Commander MUST evaluate swarm signals against portfolio constraints before execution.

#### Scenario: Filter signals by confidence threshold

**Given** Swarm returns 5 signals with confidence scores [0.65, 0.75, 0.82, 0.90, 0.55]
**When** Commander evaluates signals with min confidence 0.70
**Then** Commander proceeds with 3 signals: [0.75, 0.82, 0.90]

**Verification:**
- Confidence filtering logic in system prompt
- Multiple evaluation criteria supported
- Portfolio concentration limits enforced

## Cross-Capability Dependencies

- **Uses**: `skills-library` for swarm/math/execution functions
- **Uses**: `runtime-lifecycle` for cycle scheduling
