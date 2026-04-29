# Battery-RAG Agent Agent and Skills Spec

## Purpose

This document defines the design principles for agent orchestration and skills in Battery-RAG Agent.

## Agent Mission

The agent layer exists to turn multi-step research requests into structured, observable workflows that reuse approved platform capabilities. The agent is an orchestrator, not an unrestricted autonomous system.

## Design Principles

- Prefer deterministic routing and explicit skill boundaries in the MVP.
- Keep the agent thin; domain behavior should live in skills and services.
- Every agent action must remain inside project and evidence boundaries.
- Long-running agent work must be observable through persisted task states.
- Human review is expected for research-writing outputs.

## Agent Responsibilities

- Interpret the user task in project context.
- Classify the task into a supported task type.
- Select the required skill or skill sequence.
- Coordinate retrieval, drafting, aggregation, and export steps.
- Persist status, intermediate step metadata, and final output references.

## Non-Responsibilities

- Arbitrary tool invention at runtime.
- Accessing data outside the active project.
- Writing unchecked claims as final truth.
- Executing arbitrary code on behalf of users.

## Task Routing Principles

The MVP should start with explicit task routing rules that can later evolve toward model-assisted classification.

Initial supported task types:

- `qa`
- `summarize_paper`
- `compare_papers`
- `research_report`
- `related_work`
- `outline`
- `experiment_analysis`
- `citation_check`
- `export`

If intent is ambiguous, the router should fall back to the safest supported path, usually `qa` or a clarification request in the product experience.

## Skill Model

Skills are bounded, reusable capabilities with explicit inputs and outputs.

### Skill Requirements

- Each skill must have a stable name and description.
- Each skill must declare structured inputs and outputs.
- Each skill must return structured metadata including success state and source references where relevant.
- Skills must not contain hardcoded provider secrets.
- Skills must use shared platform services such as the LLM gateway, RAG service, export service, or analysis tool wrappers.

### Standard Skill Output Shape

Skill outputs should conceptually support:

- success flag
- result payload
- sources
- metadata
- error information when unsuccessful

## Initial Skill Set For MVP

- RetrievalSkill
- PaperSummarySkill
- MultiPaperCompareSkill
- RelatedWorkSkill
- OutlineSkill
- ExperimentAnalysisSkill
- CitationCheckSkill
- MarkdownExportSkill

The MVP may defer richer skills such as automated BibTeX enrichment, external literature search, and full LaTeX packaging.

## Evidence Rules For Agent Workflows

- Skills that generate research content must preserve provenance notes.
- Agent-produced drafts must distinguish supported findings from synthesis or suggested structure.
- Citation check should be treated as a first-class safety step for writing-oriented flows.
- The agent must not suppress evidence gaps simply to produce a smoother narrative.

## Tooling Boundaries

- Tools available to the agent must be explicitly approved and server-side controlled.
- Python analysis is allowed only through predefined wrappers for structured experiment analysis.
- External search, when enabled later, must preserve source provenance and reliability cues.
- Skills should prefer internal project evidence before external evidence unless the task explicitly requires external retrieval.

## State and Observability

Agent tasks must persist:

- `task_id`
- `user_id`
- `project_id`
- task type
- current status
- step list or progress markers
- final result reference
- failure metadata when applicable

Supported task states:

- `pending`
- `running`
- `completed`
- `failed`

## MVP Agent Scope

The MVP must support:

- a bounded task router,
- project-scoped skill execution,
- persisted task status,
- source-aware outputs for writing and analysis tasks,
- markdown artifact generation for save and export flows.

The MVP may defer:

- autonomous replanning,
- recursive self-improvement loops,
- multi-agent collaboration,
- open-ended browsing by the agent,
- user-defined custom skills.
