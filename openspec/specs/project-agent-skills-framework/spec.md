# project-agent-skills-framework Specification

## Purpose
Define a bounded Agent and Skills framework so authenticated owners can run one structured research task at a time inside their current project without bypassing project retrieval, evidence constraints, or owner-scoped security boundaries.

## Requirements

### Requirement: The system SHALL provide a project-scoped Agent and Skills framework
The system SHALL provide a bounded Agent execution framework for authenticated users inside owned projects, and the framework SHALL route one supported research task to one registered Skill using structured inputs and outputs.

#### Scenario: Authenticated owner runs a project Agent task
- **WHEN** an authenticated owner submits a supported research task inside a project they own
- **THEN** the system SHALL route that task to one registered Skill and return a structured result within that owner and project scope

### Requirement: Skills SHALL implement a unified structured interface
Every Skill introduced in this capability SHALL implement a shared contract for structured input, structured output, and execution so the Agent Executor can invoke Skills consistently.

#### Scenario: Skill output uses shared structure
- **WHEN** any Skill returns a result
- **THEN** that result SHALL include structured content plus `sources` and `warnings`

### Requirement: The system SHALL provide a Skills Registry
The backend SHALL provide a registry that can look up supported Skills by stable identifier or task type and prevent unsupported task execution.

#### Scenario: Unsupported skill is rejected safely
- **WHEN** the Agent Executor cannot resolve a routed task type to a registered Skill
- **THEN** the system SHALL reject the execution safely and SHALL NOT fabricate a result

### Requirement: The Task Router Agent SHALL classify only supported bounded research tasks
The system SHALL route user inputs only among the supported task types in this capability: `research_qa`, `paper_summary`, `multi_paper_compare`, `literature_review`, `writing_outline`, and `evidence_check`.

#### Scenario: Routed task type stays within supported set
- **WHEN** the router classifies a user request
- **THEN** the routed task type SHALL be one of the supported bounded research task types for this capability

#### Scenario: Uncertain routing degrades safely
- **WHEN** the router cannot determine a task type with enough confidence
- **THEN** the system SHALL return clarification guidance or SHALL fall back safely to `research_qa`

### Requirement: Agent execution SHALL persist owner-scoped task records
The system SHALL persist an `agent_tasks` record for each task execution attempt, and each record SHALL remain bound to `user_id` and `project_id`.

#### Scenario: Agent task record is stored
- **WHEN** an authenticated owner runs an Agent task
- **THEN** the system SHALL store the task input, task type, status, result payload, and sanitized error state for that owner and project

### Requirement: Agent execution SHALL remain evidence-first
Every Skill in this capability SHALL prefer project evidence over unsupported synthesis, SHALL avoid fabricating conclusions, and SHALL mark unsupported or weakly supported content with warnings or manual-confirmation language.

#### Scenario: Weak evidence produces warnings instead of fabricated claims
- **WHEN** a Skill lacks enough evidence to support a conclusion
- **THEN** the system SHALL return warnings, clarification, unsupported claims, or manual-confirmation language rather than inventing unsupported content

### Requirement: EvidenceCheckSkill SHALL identify unsupported claims
The system SHALL provide an evidence-checking capability that can evaluate user-provided text against the current project knowledge base and identify unsupported claims.

#### Scenario: Unsupported claims are returned explicitly
- **WHEN** `EvidenceCheckSkill` evaluates a text that contains claims not supported by current project evidence
- **THEN** the result SHALL include `unsupported_claims` and SHALL NOT mislabel them as supported

### Requirement: Agent execution SHALL not bypass owner-scoped retrieval or data access controls
The Agent framework SHALL reuse the existing owner-scoped retrieval, document, chunk, vector, and chat isolation mechanisms and SHALL NOT access another user's project data.

#### Scenario: Cross-user Agent access is blocked
- **WHEN** a user attempts to run or inspect Agent work against another user's project scope
- **THEN** the system SHALL reject the request and SHALL NOT expose the other user's documents, chunks, vectors, chat history, task records, or sources
