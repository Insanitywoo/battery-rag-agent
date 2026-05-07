## Context

Battery-RAG Agent already has:

- authenticated owner-scoped users and projects
- project document upload, ingestion, and vector retrieval
- streaming RAG chat
- a bounded Agent plus Skills framework
- a paper-writing assistant with persisted writing artifacts

The next increment is a bounded external-research layer that lets users search external paper metadata, curate saved references per project, and export BibTeX drafts without conflating external references with private project evidence.

This change crosses several boundaries:

- the backend must call external metadata providers safely
- the system must persist curated external references as project assets
- the Agent and writing layer must reuse external references under explicit source labeling
- the frontend must expose a dedicated external-references workspace
- BibTeX export must remain owner-scoped and clearly labeled as draft output

Primary constraints:

- only authenticated users may use external search or external-reference APIs
- users may only save, view, delete, and export references in projects they own
- all saved external references must be bound to `user_id` and `project_id`
- the frontend must not store or expose external API keys
- external API keys, if needed, must stay in backend environment variables only
- the system must not send private document content to external APIs unless the user explicitly enters the search query
- external references must not masquerade as uploaded-document evidence
- BibTeX output must be presented as draft content that requires manual confirmation
- this change must not download PDFs, scrape full text, bypass copyrights, or introduce large-scale crawling

## Goals / Non-Goals

**Goals:**

- add a bounded external-tool abstraction
- support Crossref metadata search
- support arXiv metadata search
- persist curated project-scoped external references
- support server-side BibTeX draft generation and export
- expose a project-scoped External References page
- allow Agent and writing flows to reuse saved external references with explicit labeling
- keep private document evidence and external references clearly separated

**Non-Goals:**

- automatic PDF download
- full-text scraping or external webpage parsing
- copyright bypass behavior
- large crawler infrastructure
- LaTeX compilation
- Word export
- experimental data analysis or plotting
- automatic full-paper generation
- paid quota logic
- complex multi-step ReAct autonomy

## Decisions

### Decision: Introduce a dedicated External Tool abstraction and Tool Registry

This change should add:

- an `ExternalTool` base interface
- a `ToolRegistry`
- normalized search result structures
- graceful failure contracts so one provider failure does not crash the application

Each tool should return structured metadata records with normalized fields such as:

- `source`
- `title`
- `authors`
- `year`
- `venue`
- `doi`
- `url`
- `abstract`
- provider-specific completeness warnings

### Decision: Implement Crossref and arXiv now, defer Semantic Scholar

This phase should implement:

- `CrossRefTool`
- `ArxivTool`
- `BibTeXTool`

`SemanticScholarTool` should be deferred from this change by default because:

- it expands API-surface complexity
- it may add additional API-key or terms-management overhead
- the current product goal can already be met by Crossref plus arXiv

If later approved, it can be introduced in a follow-up change without blocking the core external-reference workflow here.

### Decision: Search results are ephemeral until explicitly saved

`POST /external-references/search` should return transient candidate metadata only. Search results should not be persisted automatically.

Users should explicitly choose which candidates to save through:

- `POST /api/projects/{project_id}/external-references`

This keeps curation user-controlled and avoids cluttering project state with noisy search output.

### Decision: Persist curated references as `external_references`

This change should add a dedicated `external_references` model with:

- `id`
- `user_id`
- `project_id`
- `source`
- `title`
- `authors_json`
- `year`
- `venue`
- `doi`
- `url`
- `abstract`
- `bibtex`
- `created_at`
- `updated_at`

This keeps curated external metadata durable, project-scoped, exportable, and reusable by Agent or writing flows.

### Decision: Deduplicate search and save flows by DOI first, then normalized title

Search aggregation and save flows should apply basic deduplication rules:

1. prefer DOI when available
2. otherwise compare normalized title

The goal is not perfect citation resolution. The goal is a bounded first-pass dedupe strategy that reduces obvious duplicates without creating heavy matching complexity.

### Decision: Generate BibTeX drafts server-side

`BibTeXTool` should generate draft BibTeX entries from normalized metadata. The generated BibTeX should:

- stay server-side
- be exportable per project
- include warning language in UI and docs that the output requires manual confirmation

If DOI, year, venue, or authors are incomplete, the draft should still be generated when possible, but the result should surface completeness warnings.

### Decision: Keep external references separate from private uploaded-document evidence

External references must not be treated as uploaded document chunks or project knowledge-base evidence. Specifically:

- do not auto-ingest external references into PostgreSQL chunks
- do not auto-embed them into Qdrant
- do not label them as internal project evidence
- when reused by Agent or writing flows, label them explicitly as `external reference`

This preserves the core product distinction between:

- internal evidence from user-owned uploaded documents
- external metadata gathered from public scholarly sources

### Decision: Do not send private project content to external providers

External search tools should only receive:

- user-entered keywords
- user-entered title strings
- user-entered DOI values

They should not receive:

- raw uploaded-document chunks
- private chat transcripts
- project document abstracts extracted from private uploads

unless a future change introduces explicit user-approved opt-in behavior.

### Decision: Agent integration should prefer saved external references and only use live external search in bounded cases

This phase should let the Agent reuse saved `external_references` by default in:

- `literature_review`
- `related_work_draft` or equivalent writing-oriented flows

If live tool invocation is supported for Agent-assisted literature workflows, it must remain bounded:

- only for literature-review-style tasks
- only from user-provided search terms
- never from private document text
- never auto-save the results without user confirmation

### Decision: Project UI should expose a dedicated External References workspace

The frontend should add:

- an External References entry from project detail
- a project-scoped page for search, candidate review, save, list, delete, and BibTeX export

The page should show:

- source
- title
- authors
- year
- venue
- DOI
- URL
- abstract preview when available
- warnings about incomplete metadata or draft BibTeX quality

## API Shape

Recommended API surface:

- `POST /api/projects/{project_id}/external-references/search`
  - authenticated owner-scoped metadata search
  - accepts query, DOI, provider selection, and result limit
  - returns deduplicated candidate metadata
- `POST /api/projects/{project_id}/external-references`
  - persists one selected candidate to the current owner and current project
- `GET /api/projects/{project_id}/external-references`
  - lists saved references for the current owner and current project
- `DELETE /api/projects/{project_id}/external-references/{reference_id}`
  - deletes one saved project-scoped external reference
- `GET /api/projects/{project_id}/external-references/export/bibtex`
  - exports BibTeX draft content for the current owner and current project

## Tool Contract

Expected external-tool behaviors:

- unified input structure
- unified output structure
- timeout handling
- sanitized error handling
- no unhandled provider exceptions bubbling to the API layer

Suggested input fields:

- `query`
- `doi`
- `limit`

Suggested output fields:

- `source`
- `title`
- `authors`
- `year`
- `venue`
- `doi`
- `url`
- `abstract`
- `warnings`

## Agent / Writing Integration

Expected behavior:

- saved `external_references` may be used in literature-review and related-work-oriented flows
- external references must be labeled as external, not internal evidence
- external references should complement, not overwrite, current project evidence
- if DOI or source completeness is weak, the system should warn the user

## Risks / Trade-offs

- [External metadata quality varies by provider] -> mitigated by source labeling, DOI/title dedupe, and manual-confirmation warnings.
- [Users may assume BibTeX is publication-ready] -> mitigated by explicit draft warnings in UI and docs.
- [Agent use of live external search could leak private information] -> mitigated by restricting live external queries to explicit user-entered search terms only.
- [Provider outages or timeouts could destabilize the app] -> mitigated by graceful tool-level failure handling and bounded API responses.
- [External references could be mistaken for internal evidence] -> mitigated by clear source labeling and no automatic chunk/vector ingestion.

## Migration Plan

Suggested rollout order:

1. add external-tool contracts and registry
2. implement Crossref, arXiv, and BibTeX tooling
3. add `external_references` persistence
4. add search, save, list, delete, and BibTeX export APIs
5. add frontend External References workspace
6. add bounded Agent and writing reuse of saved external references
7. update docs and validate owner-scoped behavior

Rollback path:

- remove external-tool routes and services
- remove `external_references` persistence
- remove the External References page
- keep project RAG, Agent, and writing-assistant foundations intact

## Open Questions

- Should live external-tool invocation from Agent be enabled in this phase, or should the first implementation restrict Agent usage to already saved `external_references` only?
- Should BibTeX export return one combined project-scoped file only, or also support per-reference export in a later change?
- Should a saved external reference keep provider completeness warnings in persistence, or should warnings be regenerated on demand from missing fields?
