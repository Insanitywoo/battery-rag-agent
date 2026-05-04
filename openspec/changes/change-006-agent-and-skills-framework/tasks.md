## 1. Backend Agent Foundation

- [x] 1.1 Add backend configuration and dependencies needed for Agent task routing and structured Skill execution
- [x] 1.2 Add `agent_tasks` persistence with owner and project lineage plus status, result, and error fields
- [x] 1.3 Add base Skill interfaces, shared input/output contracts, and a central Skills Registry

## 2. Routing and Execution

- [x] 2.1 Implement a Task Router Agent that maps user input to one supported task type using rules plus optional backend-only LLM classification
- [x] 2.2 Implement an Agent Executor that validates ownership, routes the task, invokes one Skill, and persists task lifecycle updates
- [x] 2.3 Ensure uncertain or high-risk routing can return clarification guidance or safely fall back to `research_qa`

## 3. Skills

- [x] 3.1 Implement `RetrievalSkill` by reusing the existing owner-scoped project vector retrieval path
- [x] 3.2 Implement `ResearchQASkill` for evidence-grounded project question answering
- [x] 3.3 Implement `PaperSummarySkill` for single-document or bounded document summary inside the current project
- [x] 3.4 Implement `MultiPaperCompareSkill` for multi-document comparison of methods, models, constraints, and results
- [x] 3.5 Implement `LiteratureReviewSkill`, `OutlineSkill`, and `EvidenceCheckSkill` with structured outputs, warnings, and evidence-first degradation behavior
- [x] 3.6 Ensure every Skill output includes structured result content plus `sources` and `warnings`, and ensure `EvidenceCheckSkill` returns `unsupported_claims`

## 4. Agent APIs

- [x] 4.1 Implement `POST /api/projects/{project_id}/agent/run` as an authenticated owner-scoped execution endpoint
- [x] 4.2 Return structured Agent task results and persist input, task type, status, result payload, and sanitized error state
- [x] 4.3 Ensure Agent execution never bypasses existing `user_id + project_id` isolation for documents, chunks, vectors, chats, or sources

## 5. Frontend Project Agent Workspace

- [x] 5.1 Add a project-scoped Agent page and workspace navigation entry
- [x] 5.2 Support entering a research task prompt and optionally selecting or displaying the routed task type
- [x] 5.3 Render structured Agent results including task type, answer or result sections, sources, warnings, and unsupported claims where applicable
- [x] 5.4 Ensure frontend Agent requests continue to use `credentials: "include"` and never expose model secrets

## 6. Security and Documentation

- [x] 6.1 Verify Agent task execution, records, and result sources remain owner-scoped and project-scoped
- [x] 6.2 Verify no Agent or Skill path can access another user's project, chat history, document metadata, chunk content, or vector results
- [x] 6.3 Update `README.md` and `.env.example` with Agent and Skills framework usage notes and backend-only provider guidance

## 7. Validation

- [x] 7.1 Add backend tests for task routing, owner-scoped Agent execution, evidence-first degradation, and structured Skill outputs
- [x] 7.2 Add frontend validation coverage or run type/build checks for the Agent workspace
- [x] 7.3 Run backend tests or startup checks and frontend type/build checks for the Agent and Skills framework
