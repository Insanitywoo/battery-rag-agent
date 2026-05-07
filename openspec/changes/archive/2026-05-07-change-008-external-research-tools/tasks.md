## 1. External Tool Foundation

- [x] 1.1 Add backend configuration, schemas, and persistence for `external_references` with owner and project lineage
- [x] 1.2 Define a shared External Tool contract and Tool Registry with structured request and result shapes
- [x] 1.3 Ensure every saved external reference binds to `user_id` and `project_id`

## 2. External Metadata Tools

- [x] 2.1 Implement `CrossRefTool` for title, keyword, and DOI metadata lookup
- [x] 2.2 Implement `ArxivTool` for keyword-based arXiv metadata lookup
- [x] 2.3 Implement `BibTeXTool` for draft BibTeX generation from normalized metadata
- [x] 2.4 Ensure provider failures and timeouts are handled safely without crashing the app
- [x] 2.5 Deduplicate search candidates and saved references by DOI first and normalized title second

## 3. External Reference APIs

- [x] 3.1 Implement `POST /api/projects/{project_id}/external-references/search` as an authenticated owner-scoped search endpoint
- [x] 3.2 Implement `POST /api/projects/{project_id}/external-references` to save one curated external reference into the current project
- [x] 3.3 Implement owner-scoped external-reference list and delete APIs
- [x] 3.4 Implement owner-scoped project BibTeX export API
- [x] 3.5 Ensure external-reference APIs never send private project document content to external providers unless the user explicitly supplied the search query

## 4. Agent and Writing Integration

- [x] 4.1 Extend Agent or related writing flows so literature-review-oriented tasks can reuse saved `external_references`
- [x] 4.2 Ensure external references remain explicitly labeled as `external reference` and never masquerade as uploaded-document evidence
- [x] 4.3 Ensure Agent integration does not auto-ingest external results into chunks, embeddings, or the vector knowledge base
- [x] 4.4 Ensure incomplete DOI or source metadata produces user-facing confirmation warnings

## 5. Frontend External References Workspace

- [x] 5.1 Add a project-scoped External References page and workspace navigation entry
- [x] 5.2 Support entering keyword, title, or DOI searches and viewing candidate results
- [x] 5.3 Support saving selected candidates to the current user's current project
- [x] 5.4 Support listing and deleting saved external references in the current project
- [x] 5.5 Support project-scoped BibTeX export using authenticated backend requests with `credentials: "include"`

## 6. Security and Documentation

- [x] 6.1 Verify unauthenticated users cannot use external search or external-reference APIs
- [x] 6.2 Verify users cannot save, view, delete, or export another user's project external references
- [x] 6.3 Verify frontend code never stores external API keys and backend-only key handling is documented
- [x] 6.4 Update `README.md` and `.env.example` with external-tool configuration, BibTeX draft limitations, and manual-verification warnings

## 7. Validation

- [x] 7.1 Add backend tests for external search normalization, owner-scoped persistence, delete, export, and deduplication behavior
- [x] 7.2 Add frontend validation coverage or run type/build checks for the External References workspace
- [x] 7.3 Run backend tests or startup checks, frontend type/build checks, and `openspec validate change-008-external-research-tools`
