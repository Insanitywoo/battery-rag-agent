# project-vector-knowledge-base Specification

## Purpose
Define project-scoped vector indexing and semantic retrieval so each authenticated owner can build and query a vector knowledge base only from their own project chunks.

## Requirements

### Requirement: Authenticated owners SHALL be able to build a project-scoped vector knowledge base from chunks
The system SHALL allow an authenticated project owner to generate embeddings for that project's chunks and persist them to Qdrant, and it SHALL reject unauthenticated or cross-user build requests.

#### Scenario: Owner builds project vector knowledge base
- **WHEN** an authenticated owner triggers vector build for a project they own
- **THEN** the system SHALL generate embeddings from that project's chunks and persist project-scoped vectors

#### Scenario: Non-owner cannot build another user's project vectors
- **WHEN** an authenticated user attempts to build vectors for another user's project
- **THEN** the system SHALL reject the request and SHALL NOT embed or write that project's vectors

### Requirement: Qdrant payloads SHALL carry ownership and chunk lineage metadata
Every vector written for this capability SHALL include payload metadata linking it to the current owner, project, document, and source chunk.

#### Scenario: Vector payload contains source lineage
- **WHEN** a chunk embedding is written to Qdrant
- **THEN** the vector payload SHALL include `user_id`, `project_id`, `document_id`, `chunk_id`, `page_number`, and `chunk_index`

### Requirement: Rebuilding the project knowledge base SHALL replace stale vectors
The system SHALL support rebuilding a project's vector knowledge base, and rebuild behavior SHALL clear or overwrite prior vectors for that same project before persisting the refreshed vector set.

#### Scenario: Rebuild replaces prior project vectors
- **WHEN** an owner rebuilds vectors for a project
- **THEN** the resulting vector state SHALL correspond to the current chunk set rather than accumulating stale duplicates

### Requirement: Semantic retrieval SHALL remain owner-scoped and project-scoped
The system SHALL provide semantic retrieval over project vectors, and retrieval MUST enforce both `user_id` and `project_id` filters at the Qdrant query layer for chat and for all Agent or Skill executions that reuse project retrieval.

#### Scenario: Retrieval returns only current project evidence
- **WHEN** an authenticated owner issues a semantic retrieval query for a project they own
- **THEN** the retrieval results SHALL be limited to vectors belonging to that user and that project

#### Scenario: Cross-user or cross-project retrieval is blocked
- **WHEN** a retrieval request targets another user's project context
- **THEN** the system SHALL reject the request or return no evidence outside the owner's scoped project

#### Scenario: Agent retrieval returns only current project evidence
- **WHEN** an authenticated owner executes an Agent task that requires project retrieval
- **THEN** the retrieval results SHALL be limited to vectors belonging to that user and that project

### Requirement: Vector retrieval payloads SHALL support cited chat answers safely
The system SHALL preserve retrieval payload metadata needed for downstream chat citations, and chat retrieval MUST use the current authenticated owner and active project as mandatory Qdrant filters.

#### Scenario: Chat retrieval uses current owner and project filters
- **WHEN** the RAG chat flow issues a vector search
- **THEN** the Qdrant search SHALL filter on `current_user.id` and the active `project_id`
