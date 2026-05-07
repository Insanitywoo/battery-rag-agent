## Why

Battery-RAG Agent already supports owner-scoped project knowledge bases, streaming RAG chat, a bounded Agent plus Skills framework, and a paper-writing assistant. The next product step is to let researchers bring in external paper metadata safely so they can broaden related-work preparation, shortlist candidate references, and draft BibTeX without mixing external literature with user-uploaded evidence.

Today the system has no first-class external-research layer. Users cannot search Crossref or arXiv from inside a project, cannot save curated reference metadata as project assets, cannot export project-scoped BibTeX drafts, and cannot let the Agent or writing layer reuse curated external references under explicit labeling. This change adds a bounded external-research tools layer that remains owner-scoped, source-labeled, and separate from the private document knowledge base.

## What Changes

- Add an External Tool base contract and Tool Registry.
- Implement `CrossRefTool` for title, keyword, or DOI metadata search.
- Implement `ArxivTool` for keyword-based arXiv metadata search.
- Defer `SemanticScholarTool` from this phase unless later approved in a narrower follow-up change.
- Implement a server-side `BibTeXTool` that generates BibTeX drafts from structured metadata.
- Add owner-scoped `external_references` persistence for curated saved references.
- Add authenticated owner-scoped external-reference APIs:
  - `POST /api/projects/{project_id}/external-references/search`
  - `POST /api/projects/{project_id}/external-references`
  - `GET /api/projects/{project_id}/external-references`
  - `DELETE /api/projects/{project_id}/external-references/{reference_id}`
  - `GET /api/projects/{project_id}/external-references/export/bibtex`
- Add a project-scoped External References page in the frontend.
- Let users search external literature by title, keyword, or DOI and review candidate results.
- Let users save selected candidates into the current project and delete saved references later.
- Let users export project-scoped BibTeX drafts with clear manual-verification warnings.
- Let the Agent and writing assistant reuse saved `external_references` for literature-review and related-work assistance with explicit `external reference` labeling.
- Keep external results separate from user-uploaded document evidence and do not auto-ingest external results into the local vector knowledge base.
- Update `README.md` and `.env.example` with external-tool configuration and usage constraints.

## Capabilities

### New Capabilities

- `project-external-references`: Defines external metadata search, curated save, list, delete, and BibTeX export for owner-scoped project references.

### Modified Capabilities

- `project-agent-skills-framework`: Extends Agent behavior so literature-review or related-work flows may reuse saved external references and, when explicitly appropriate, bounded external search tools.
- `project-paper-writing-assistant`: Extends writing-assistant behavior so related-work and citation-support flows may use saved external references with explicit external labeling.
- `backend-shell`: Expands accepted backend scope to include bounded external metadata tools and project-scoped external-reference APIs.
- `frontend-auth-workspace`: Expands the authenticated project workspace with an External References page and BibTeX export flow.
- `user-project-workspace`: Expands project detail navigation to include an external-references entry point.
- `local-dev-infra`: Extends documentation expectations to include external-tool configuration, rate-limit considerations, and backend-only key handling.

## Impact

- Affected code: backend external-tool services, API routes, persistence models, BibTeX formatting helpers, Agent integration points, frontend external-reference workspace, and documentation.
- Affected APIs: external-reference search, save, list, delete, and BibTeX export endpoints.
- Affected systems: PostgreSQL project reference persistence, outbound scholarly metadata requests, Agent/writing integration boundaries, and owner-scoped export generation.
- Dependencies likely introduced or activated: HTTP clients for external metadata services, metadata normalization helpers, DOI/title deduplication logic, and server-side BibTeX draft rendering.
