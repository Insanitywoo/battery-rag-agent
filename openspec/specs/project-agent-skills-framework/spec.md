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
The system SHALL route user inputs only among the supported task types in this capability, and this change SHALL expand the bounded task set to include writing-oriented tasks such as `introduction_outline`, `related_work_draft`, `method_framework`, `conclusion_draft`, `citation_check`, and `markdown_export` in addition to the existing bounded research tasks.

#### Scenario: Writing task type stays within supported set
- **WHEN** the router classifies a writing-oriented user request
- **THEN** the routed task type SHALL be one of the supported bounded writing or research task types for this capability

#### Scenario: Uncertain routing degrades safely
- **WHEN** the router cannot determine a task type with enough confidence
- **THEN** the system SHALL return clarification guidance or SHALL fall back safely to `research_qa`

### Requirement: Agent execution SHALL persist owner-scoped task records
The system SHALL persist an `agent_tasks` record for each task execution attempt, and each record SHALL remain bound to `user_id` and `project_id`.

#### Scenario: Agent task record is stored
- **WHEN** an authenticated owner runs an Agent task
- **THEN** the system SHALL store the task input, task type, status, result payload, and sanitized error state for that owner and project

### Requirement: Agent execution SHALL remain evidence-first
Every Skill in this capability SHALL prefer project evidence over unsupported synthesis, SHALL avoid fabricating conclusions, and SHALL mark unsupported or weakly supported content with warnings or manual-confirmation language, including writing-oriented outputs.

#### Scenario: Writing-oriented Skill avoids fabricated citations
- **WHEN** a writing-oriented Skill lacks enough evidence to support a citation, result, or claim
- **THEN** the system SHALL return unsupported-claim markers or manual-confirmation language rather than inventing references, experiments, or sources

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

### Requirement: Agent execution SHALL support bounded external-reference assistance for literature workflows
The system SHALL allow literature-review-oriented and related-work-oriented flows in this capability to reuse saved project-scoped `external_references`, and any live external metadata lookup enabled by this change SHALL remain bounded to explicit user search intent rather than private document content.

#### Scenario: Literature workflow uses saved external references safely
- **WHEN** an authenticated owner runs a literature-review-oriented or related-work-oriented task
- **THEN** the Agent or writing flow MAY use saved project-scoped external references in addition to internal project evidence, while preserving owner and project isolation

### Requirement: External references SHALL remain distinct from internal evidence
The Agent framework SHALL label external metadata as `external reference`, SHALL NOT treat it as uploaded-document evidence, and SHALL NOT auto-ingest it into chunks, embeddings, or vector search state in this change.

#### Scenario: External result does not masquerade as uploaded-document evidence
- **WHEN** an Agent or writing flow uses a saved or live external scholarly result
- **THEN** the output SHALL label that material as external reference content and SHALL NOT present it as internal project document evidence
