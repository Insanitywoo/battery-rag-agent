## Context

Battery-RAG Agent already has the core building blocks needed for grounded writing assistance:

- authenticated owner-scoped projects
- project document storage and chunk ingestion
- project vector retrieval with `user_id + project_id` filtering
- backend-only LLM access
- a bounded Agent and Skills framework

The next increment is not unrestricted long-form paper generation. It is a bounded writing-assistant layer that helps users produce structured drafting artifacts for the current project and keeps each artifact tied to current project evidence, warnings, and unsupported-claim markers.

This change crosses several boundaries:

- the backend must persist writing outputs as first-class project artifacts
- the writing layer must reuse the existing retrieval and evidence boundaries rather than bypassing them
- the Agent framework must expand to recognize writing-oriented tasks safely
- the frontend must expose a dedicated writing workspace and artifact history
- Markdown export must remain owner-scoped and artifact-scoped

Primary constraints:

- only authenticated users may use the writing assistant
- users may only generate, view, delete, and export writing artifacts in projects they own
- writing outputs must remain evidence-first
- unsupported conclusions must be marked as needing manual confirmation
- the system must not fabricate references, experimental results, or citations
- the frontend must not call model providers directly
- this change must not introduce web search, scholarly APIs, BibTeX generation, LaTeX or Word export, PDF export, external tools, experiment analysis, or multi-step ReAct autonomy

## Goals / Non-Goals

**Goals:**

- add a project-scoped writing workspace
- support explicit and auto-routed writing task types
- persist writing outputs in `writing_artifacts`
- keep sources and unsupported claims attached to each artifact
- support artifact history, delete, and Markdown export
- extend the Agent framework with writing-oriented Skills
- preserve evidence-first output behavior

**Non-Goals:**

- automatic full-paper ghostwriting
- external literature search or reference managers
- BibTeX generation
- LaTeX, Word, or PDF export
- external tool calls
- experiment analysis or plotting
- complex multi-step autonomous writing agents

## Decisions

### Decision: Use a dedicated writing API while reusing Agent and Skills internals

This change should not force all writing operations through `POST /api/projects/{project_id}/agent/run`. Instead:

- the backend should expose a dedicated `writing/run` API for writing assistant flows
- that API should reuse the Task Router, retrieval helpers, and writing-oriented Skills where appropriate
- writing artifacts should be persisted independently from `agent_tasks`

This keeps the writing workspace product-oriented while still leveraging the bounded Agent framework underneath.

### Decision: Persist writing outputs as `writing_artifacts`

This change should add a dedicated `writing_artifacts` model with:

- `id`
- `user_id`
- `project_id`
- `artifact_type`
- `title`
- `content_markdown`
- `sources_json`
- `unsupported_claims_json`
- `created_at`
- `updated_at`

Suggested `artifact_type` values:

- `outline`
- `introduction_outline`
- `related_work`
- `method_framework`
- `conclusion`
- `citation_check`

This keeps writing history durable, inspectable, and exportable without conflating it with chat history or generic task records.

### Decision: Treat writing assistant generation as structured drafting assistance, not final-paper authorship

Each writing-oriented Skill should produce:

- markdown-ready content
- source references
- unsupported claims
- warnings

The outputs should be suitable for researcher review and editing, but not positioned as fully authoritative or publication-ready text.

### Decision: Keep evidence-first rules explicit in writing prompts

Every writing prompt should include:

- a system instruction
- the user's writing task
- retrieved project evidence chunks
- instructions to surface sources
- instructions to surface unsupported claims
- explicit prohibition against fabricated references, fabricated results, and fabricated citations

If evidence is insufficient, the output should:

- say that manual confirmation is required
- keep unsupported claims separate
- avoid invented source statements

### Decision: Extend the Task Router with writing task types but prefer explicit task selection in the writing page

The writing page should let users explicitly choose a writing task type first. The router still matters for:

- optional auto mode
- writing-oriented natural-language prompts
- future reuse from the broader Agent layer

Suggested writing task types:

- `writing_outline`
- `introduction_outline`
- `related_work_draft`
- `method_framework`
- `conclusion_draft`
- `citation_check`
- `markdown_export`

The router should remain bounded and should degrade to clarification rather than over-committing on ambiguous writing requests.

### Decision: Reuse retrieval foundations from existing project vector search

Writing-oriented Skills should reuse:

- existing `user_id + project_id` vector filters
- current chunk lineage and source references
- backend-only LLM prompt assembly
- current evidence-first safeguards

This prevents the writing assistant from creating a second retrieval path with weaker ownership guarantees.

### Decision: Keep Markdown export server-side and artifact-scoped

`MarkdownExportSkill` should generate artifact Markdown from persisted writing results, and the export endpoint should only serve:

- artifacts owned by the current user
- artifacts belonging to the current project

The export path should not introduce file-system write requirements in this change unless implementation needs a temporary in-memory response. The feature should focus on returning a Markdown payload for one artifact.

### Decision: Keep writing history simple in this phase

The first implementation should support:

- list current project writing artifacts
- view one artifact
- delete one artifact
- export one artifact as Markdown

It should not yet support:

- folders or collections
- version history
- collaborative editing
- multi-artifact composition pipelines

## Skill Mapping

Expected writing-oriented Skills:

- `WritingOutlineSkill`
  - output: overall outline in Markdown
- `IntroductionOutlineSkill`
  - output: introduction framing structure, problem statement, motivation, contribution framing
- `RelatedWorkDraftSkill`
  - output: evidence-grounded related-work draft with unsupported claims marked
- `MethodFrameworkSkill`
  - output: method section structure, subsections, and writing prompts
- `ConclusionDraftSkill`
  - output: conclusion draft with limitations on unsupported extrapolation
- `CitationCheckSkill`
  - output: supported claims, unsupported claims, and source references
- `MarkdownExportSkill`
  - output: export-ready Markdown derived from a persisted artifact

All writing Skills should return a structured result that includes:

- `content_markdown`
- `sources`
- `warnings`
- `unsupported_claims`

## API Shape

Recommended API surface:

- `POST /api/projects/{project_id}/writing/run`
  - authenticated owner-scoped execution
  - accepts topic, research direction, requirements, and optional task type
  - returns saved artifact detail
- `GET /api/projects/{project_id}/writing/artifacts`
  - list current user's writing artifacts for that project
- `GET /api/projects/{project_id}/writing/artifacts/{artifact_id}`
  - return one owner-scoped artifact
- `DELETE /api/projects/{project_id}/writing/artifacts/{artifact_id}`
  - delete one owner-scoped artifact
- `GET /api/projects/{project_id}/writing/artifacts/{artifact_id}/export/markdown`
  - export one owner-scoped artifact as Markdown

## Risks / Trade-offs

- [Writing outputs may appear more authoritative than the evidence justifies] -> mitigated by explicit unsupported-claim sections and manual-confirmation warnings.
- [Related-work drafting may overstate comparative claims] -> mitigated by evidence-first prompt requirements and source-bearing outputs.
- [A dedicated writing API increases surface area relative to only reusing `agent/run`] -> acceptable because persistence, history, and export are first-class product needs here.
- [Markdown export may be mistaken for publication-ready output] -> mitigated by documentation and explicit assistant limitations.
- [Task-type overlap between general Agent and writing assistant may create confusion] -> mitigated by explicit writing task selection in the writing page and bounded router rules.

## Migration Plan

Suggested rollout order:

1. add `writing_artifacts` persistence
2. add writing request and response contracts
3. extend routing and writing-oriented Skill registration
4. add `writing/run` plus artifact history APIs
5. add frontend writing workspace and history views
6. add Markdown export
7. update docs and validate owner-scoped behavior

Rollback path:

- remove writing APIs
- remove writing artifact persistence
- remove writing page
- keep the underlying Agent framework, retrieval, and RAG chat intact

## Open Questions

- Should `CitationCheckSkill` remain distinct from the generic `EvidenceCheckSkill`, or should it wrap the same backend logic with writing-oriented output formatting?
- Should the first writing page expose explicit task selection only, or include a true auto-route mode on day one?
- Should Markdown export return a downloadable text response only, or also store an export timestamp in this change?
