## Why

Battery-RAG Agent can now ingest project documents, build a project-scoped vector knowledge base, and answer project questions through streaming RAG chat. The next step is to move from a single chat interaction pattern toward a reusable Agent plus Skills framework that can classify different research intents, invoke the right structured capability, and persist task records for later inspection.

Without this layer, every future research workflow such as paper summary, evidence checking, or literature-review drafting would have to be implemented as a separate ad hoc endpoint. This change establishes the extensible Agent and Skills architecture first, while keeping execution bounded to the current project's own knowledge base and evidence constraints.

## What Changes

- Add a backend Skill base interface with structured input and output contracts.
- Add a Skills Registry so project-scoped skills can be discovered and invoked consistently.
- Add a lightweight Task Router Agent that maps user intent to a supported task type using rules plus optional LLM assistance.
- Add an Agent Executor that validates ownership, routes the task, invokes the selected Skill, and persists structured task records.
- Add support for the following task types:
  - `research_qa`
  - `paper_summary`
  - `multi_paper_compare`
  - `literature_review`
  - `writing_outline`
  - `evidence_check`
- Add the following skills:
  - `RetrievalSkill`
  - `ResearchQASkill`
  - `PaperSummarySkill`
  - `MultiPaperCompareSkill`
  - `LiteratureReviewSkill`
  - `OutlineSkill`
  - `EvidenceCheckSkill`
- Add `agent_tasks` persistence for task input, task type, status, result payload, and error state.
- Add an authenticated owner-scoped `POST /api/projects/{project_id}/agent/run` endpoint.
- Add a project-scoped frontend Agent page for submitting research tasks and viewing structured results.
- Require Agent outputs to remain evidence-first and include sources or warnings wherever possible.
- Update `.env.example` and `README.md` with Agent and Skills usage notes.

## Capabilities

### New Capabilities

- `project-agent-skills-framework`: Defines the Skill contract, registry, task router, executor, task persistence, and evidence-first structured outputs for project-scoped research tasks.

### Modified Capabilities

- `backend-shell`: Expands accepted backend scope from vector DB plus RAG chat into vector DB plus RAG chat plus project-scoped Agent and Skills APIs.
- `frontend-auth-workspace`: Expands the authenticated project workspace to include a project Agent route and structured task result presentation.
- `project-rag-chat`: Clarifies that `research_qa` skill execution reuses the same backend-only retrieval and evidence-grounded answer principles without replacing chat history flows.
- `project-vector-knowledge-base`: Clarifies that Skills must reuse existing owner-scoped semantic retrieval rather than bypassing vector filters.
- `user-project-workspace`: Expands project detail and workspace navigation to include a project Agent entry point.
- `local-dev-infra`: Extends environment and documentation coverage to include Agent task configuration while keeping provider keys backend-only.

## Impact

- Affected code: backend Agent services, Skill implementations, task persistence models, routing APIs, frontend project Agent page, shared result types, and documentation.
- Affected APIs: `POST /api/projects/{project_id}/agent/run`, Agent task history/detail APIs if introduced in implementation, and project navigation payloads.
- Affected systems: PostgreSQL Agent task persistence, backend LLM gateway orchestration, vector retrieval reuse, and project-scoped ownership enforcement.
- Dependencies likely introduced or activated: structured task classification helpers, skill registry wiring, and reusable result serialization for evidence-bearing outputs.
