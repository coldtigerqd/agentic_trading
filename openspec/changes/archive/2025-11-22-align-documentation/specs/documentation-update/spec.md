# Spec Delta: Documentation Update

## MODIFIED Requirements

### Requirement: Accurate System Documentation

User-facing documentation SHALL precisely reflect the current implementation state, with clear separation between implemented, deprecated, and planned features. Documentation MUST NOT describe unimplemented features as current capabilities.

**Rationale**: Documentation that describes unimplemented features creates false expectations and confusion. Documentation that omits implemented features leaves users unable to utilize the system properly.

#### Scenario: User reads README to understand system capabilities

**Given** a new user reading the README.md file
**When** they read the "System Overview" section
**Then** they should understand the system uses manual command-triggered analysis (not automatic loops)
**And** they should see only actually implemented features described
**And** they should find planned features clearly labeled in a "Roadmap" section

#### Scenario: User wants to run a trading analysis

**Given** a user has completed setup
**When** they read the "Usage Guide" section
**Then** they should find clear instructions for triggering analysis via slash commands
**And** they should see examples of manual command invocation
**And** they should NOT see references to automatic 5-minute loops

#### Scenario: Developer wants to understand architecture

**Given** a developer reading openspec/project.md
**When** they review the "Tech Stack" section
**Then** ThetaData should be documented as using REST API (not MCP)
**And** only actually implemented MCP servers should be listed
**And** operational constraints should reflect manual mode

---

### Requirement: Migration Documentation

Architectural changes SHALL be documented with rationale and migration guidance. The system MUST provide MIGRATION.md explaining major architectural shifts.

**Rationale**: Users or developers on previous architectures need clear guidance to understand changes and migrate if needed.

#### Scenario: User discovers main_loop.py is deprecated

**Given** a user who previously used main_loop.py
**When** they read MIGRATION.md
**Then** they should understand why automatic loop mode was deprecated
**And** they should find clear steps to migrate to manual command mode
**And** they should see examples of the new workflow

#### Scenario: Developer wonders why REST API instead of MCP

**Given** a developer reviewing ThetaData integration
**When** they read MIGRATION.md
**Then** they should find the rationale for REST API vs MCP
**And** they should understand the benefits (reliability, performance, simplicity)
**And** they should see which components still use MCP and why

---

## ADDED Requirements

### Requirement: Future Features Roadmap

Planned but unimplemented features SHALL be clearly separated in documentation to avoid confusion with current capabilities. The README MUST contain a dedicated "Roadmap" section for planned features.

**Rationale**: Aspirational features are valuable to document for project direction, but must not be conflated with current capabilities.

#### Scenario: User reads about Dream Lab feature

**Given** a user interested in the genetic algorithm optimizer
**When** they read the README
**Then** Dream Lab should appear ONLY in the "Roadmap" section
**And** it should be clearly marked as "planned" or "未来功能"
**And** it should NOT appear in "Current Capabilities" or "Functional Modules"

#### Scenario: Developer evaluates available MCP servers

**Given** a developer reviewing available MCP integrations
**When** they read project.md
**Then** only IBKR should be listed as implemented MCP server
**And** News Sentiment should be marked as "in-progress" or "incomplete"
**And** any future MCP servers should be in a "Planned" subsection
