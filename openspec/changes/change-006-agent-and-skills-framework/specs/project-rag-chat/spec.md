## MODIFIED Requirements

### Requirement: Project chat SHALL answer from retrieved project evidence with citations
The system SHALL continue to answer project questions using retrieved project-scoped evidence and SHALL return source information including source document, page number where available, and supporting snippet, and the `research_qa` skill introduced in this change SHALL reuse the same backend-only evidence-grounded answer principles rather than bypassing chat retrieval safeguards.

#### Scenario: Research QA skill reuses bounded RAG answer rules
- **WHEN** the Agent framework executes a `research_qa` task
- **THEN** the resulting answer behavior SHALL remain evidence-grounded, owner-scoped, and citation-bearing under the same project retrieval constraints used by project chat
