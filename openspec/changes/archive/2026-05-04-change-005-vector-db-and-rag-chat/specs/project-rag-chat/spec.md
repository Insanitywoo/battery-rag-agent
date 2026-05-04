## ADDED Requirements

### Requirement: The system SHALL provide project-scoped chat sessions and message persistence
The system SHALL persist chat sessions and chat messages for authenticated users within the current project scope.

#### Scenario: User creates or continues a project chat session
- **WHEN** an authenticated owner opens or uses project chat
- **THEN** the system SHALL be able to persist session metadata and ordered chat messages for that user and project

### Requirement: Chat history SHALL remain account-scoped and owner-scoped
The system SHALL ensure each user can see, continue, and delete only their own chat sessions inside the current project, and chat sessions plus messages MUST always remain bound to `user_id`, `project_id`, and `session_id` as applicable.

#### Scenario: User lists project chat sessions
- **WHEN** an authenticated user requests chat sessions for a project they own
- **THEN** the system SHALL return only that user's sessions for that project

#### Scenario: User continues a historical chat session
- **WHEN** an authenticated owner opens a prior session in their project and asks a follow-up question
- **THEN** the system SHALL append messages only within that owner-scoped session

#### Scenario: User deletes a chat session
- **WHEN** an authenticated owner deletes one of their project chat sessions
- **THEN** the system SHALL delete that session and its messages

#### Scenario: Cross-user chat access is blocked
- **WHEN** a user attempts to read, append to, or delete another user's session
- **THEN** the system SHALL reject the request and SHALL NOT expose the other user's messages or sources

### Requirement: RAG answers SHALL be generated only through a backend LLM Gateway
The system SHALL call embedding and chat models only from the backend using environment-backed provider configuration, and the frontend MUST NOT call the model provider directly or hold provider secrets.

#### Scenario: Frontend never exposes provider secrets
- **WHEN** the project chat feature is reviewed
- **THEN** model API keys or provider secrets SHALL not be present in frontend code or browser-exposed configuration

### Requirement: Project chat SHALL assemble prompt context from history and retrieved project evidence
The system SHALL implement chat as a RAG flow where the current user question is combined with the most recent chat history and retrieved project-scoped chunks before the LLM is called.

#### Scenario: Prompt includes bounded recent history and retrieved chunks
- **WHEN** an authenticated owner asks a project question
- **THEN** the backend prompt SHALL include a system instruction, the most recent `N` chat history messages with default `N = 6`, the retrieved top-k project chunks, and the current user question

### Requirement: Project chat SHALL stream generated answers to the frontend
The system SHALL provide a streaming chat endpoint so cited assistant answers are rendered incrementally in the authenticated frontend, and the completed assistant message SHALL be persisted after stream completion.

#### Scenario: Streaming answer is displayed and then persisted
- **WHEN** an authenticated owner submits a question in project chat
- **THEN** the backend SHALL stream the answer response to the frontend and SHALL save the finalized assistant message after the stream finishes successfully

### Requirement: Project chat SHALL answer from retrieved project evidence with citations
The system SHALL answer project questions using retrieved project-scoped evidence and SHALL return source information including source document, page number where available, and supporting snippet.

#### Scenario: Cited answer is returned
- **WHEN** retrieval returns sufficient evidence for a project question
- **THEN** the system SHALL generate an answer accompanied by source document, page, and snippet information

### Requirement: RAG answers SHALL explicitly acknowledge insufficient evidence
If retrieval evidence is absent or insufficient, the system SHALL answer that the current knowledge base does not contain enough information rather than fabricating unsupported claims.

#### Scenario: Insufficient evidence produces explicit fallback
- **WHEN** retrieval does not produce enough evidence to support an answer
- **THEN** the system SHALL respond with `当前知识库中没有足够信息`

### Requirement: Persisted source references SHALL remain owner-scoped and project-scoped
Any `sources_json` or equivalent saved with chat messages SHALL include only source information from the current authenticated user's current project and SHALL preserve structured citation fields needed by the frontend.

#### Scenario: Stored sources stay within current project scope
- **WHEN** a cited answer is persisted in chat history
- **THEN** the saved source metadata SHALL reference only chunks, documents, and pages belonging to that user and project

#### Scenario: Stored sources keep required citation fields
- **WHEN** an assistant answer is saved
- **THEN** each saved source entry SHALL include `document_id`, `document_name`, `page_number`, `chunk_id`, `chunk_index`, and `excerpt`
