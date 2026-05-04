## Context

Battery-RAG Agent already provides owner-scoped project documents, project-scoped vector retrieval, backend-only LLM access, and streaming RAG chat with citations. The next increment is not a larger multi-step autonomous agent. It is a bounded Agent plus Skills framework that can identify a supported research intent, execute one structured capability, and persist the task result for the current user's current project.

This change crosses several boundaries:

- The backend must standardize how research tasks are represented and executed.
- Retrieval-backed and synthesis-style tasks must share a common Skill interface.
- The system must route user input to one supported task type safely.
- Agent execution must never bypass existing `user_id + project_id` data isolation.
- Structured task results must preserve evidence, warnings, and unsupported-claim markers.
- The frontend must gain a project Agent page without exposing provider keys or introducing external tools.

Primary constraints:

- Only authenticated users may run Agent tasks.
- Users may only run Agent tasks inside projects they own.
- Agent tasks, sources, and results must remain bound to `user_id` and `project_id`.
- Skills must reuse the existing project-scoped retrieval and backend LLM gateway rather than inventing parallel access paths.
- Outputs must remain evidence-first; unsupported conclusions must not be fabricated.
- If evidence is weak, the result must degrade to warnings, clarification, fallback to `research_qa`, or explicit manual-confirmation language.
- This change must not introduce external web search, bibliographic APIs, async workers, external tool execution, or complex ReAct loops.

## Goals / Non-Goals

**Goals:**

- Define a reusable Skill interface with structured inputs and outputs.
- Define a central Skills Registry.
- Define a lightweight Task Router Agent.
- Define an Agent Executor that validates, routes, invokes, and persists one task run.
- Support the six initial task types in a bounded project scope.
- Reuse existing project vector retrieval for retrieval-backed skills.
- Persist Agent task history in PostgreSQL.
- Add a project-scoped frontend Agent page that can submit a task and display structured results.

**Non-Goals:**

- External web search or scholarly APIs.
- BibTeX generation, LaTeX export, Word export, or publishing workflows.
- Experiment data analysis or Python plotting.
- Multi-step autonomous planning or external tool calling.
- Async queues, Celery, or background worker orchestration.
- Automatic paper ghostwriting or unrestricted long-form generation.

## Decisions

### Decision: Treat Agent execution as single-task routing, not open-ended autonomy

This change should define Agent behavior as:

1. accept a user input inside one owned project
2. classify it into one supported task type
3. select one Skill
4. execute that Skill with structured input
5. return and persist one structured result

This preserves a narrow, inspectable execution model and avoids prematurely building a complex multi-step autonomous agent.

### Decision: Use one shared Skill contract for all initial research workflows

Each Skill should implement a common contract with:

- stable skill name
- supported task type
- structured input model
- structured output model
- execution method

Every Skill output should include at least:

- `result` or `answer`
- `sources`
- `warnings`

Some skills may extend that shape with task-specific fields such as:

- `summary_sections`
- `comparison_rows`
- `outline_sections`
- `unsupported_claims`

This keeps the framework extensible without forcing every task into one flat answer string.

### Decision: Separate routing from execution

The Task Router Agent should determine the best supported task type, but it should not execute the task directly. The Agent Executor should own:

- ownership validation
- project context loading
- router invocation
- skill lookup
- task persistence lifecycle
- error handling

This separation allows later changes to improve routing without rewriting every skill.

### Decision: Start task routing with rules first, then optional LLM assistance

The routing strategy should prefer deterministic rules first:

- explicit task-type selection if the frontend provides it
- strong keyword or pattern cues
- document-count cues for compare vs summary

If the rules remain ambiguous, the router may use the backend-only LLM gateway to classify among the supported task types. For low-confidence results:

- return clarification guidance, or
- fall back to `research_qa`

This keeps behavior predictable while still allowing gradual improvement.

### Decision: Reuse existing retrieval and evidence constraints

`RetrievalSkill` should be the shared retrieval foundation for:

- `ResearchQASkill`
- `PaperSummarySkill`
- `MultiPaperCompareSkill`
- `LiteratureReviewSkill`
- `EvidenceCheckSkill`

These skills must reuse the current owner-scoped project retrieval path:

- same `user_id + project_id` vector filters
- same backend-only LLM gateway
- same evidence-first citation rules

This prevents the Agent layer from becoming a second, weaker security boundary.

### Decision: Persist Agent task history in a dedicated `agent_tasks` model

This change should add:

- `id`
- `user_id`
- `project_id`
- `task_type`
- `user_input`
- `status`
- `result_json`
- `error_message`
- `created_at`
- `updated_at`

Suggested status values:

- `queued`
- `running`
- `completed`
- `failed`
- `needs_clarification`

Even if execution remains synchronous in this phase, explicit status values prepare the system for later async evolution without requiring a schema reset.

### Decision: Keep Skill outputs structured and source-bearing

Every Skill should return a structured result object. Examples:

- `ResearchQASkill`:
  - `answer`
  - `sources`
  - `warnings`
- `PaperSummarySkill`:
  - `summary`
  - `document_scope`
  - `sources`
  - `warnings`
- `MultiPaperCompareSkill`:
  - `comparison`
  - `dimensions`
  - `sources`
  - `warnings`
- `EvidenceCheckSkill`:
  - `supported_claims`
  - `unsupported_claims`
  - `sources`
  - `warnings`

If evidence is insufficient, the output should not invent content. It should either:

- state that manual review is needed
- identify unsupported areas
- reduce confidence
- or fallback to a safer task classification

### Decision: Keep document scoping simple for summary and compare tasks

This phase should support:

- single-document summary by explicit document selection if provided
- implicit summary over the most relevant document when safely inferable
- multi-document compare over retrieved or explicitly scoped documents inside the current project

The design should avoid complex document-set management or saved collections in this change.

### Decision: Add a dedicated project Agent route in the frontend

The frontend should add a project-scoped Agent page that supports:

- entering a research task prompt
- optionally selecting a task type
- submitting the task with `credentials: "include"`
- viewing structured results, sources, and warnings

The frontend must not call model providers directly and must not store secrets in browser-accessible state.

## Risks / Trade-offs

- [Rule-based routing may misclassify nuanced research requests] -> mitigated by optional LLM classification plus fallback to `research_qa`.
- [Structured outputs can become inconsistent across skills] -> mitigated by a shared base result contract.
- [Compare and review tasks may over-synthesize from weak evidence] -> mitigated by mandatory warnings and evidence-first output requirements.
- [Synchronous execution may feel slow for heavier tasks] -> acceptable for this bounded framework phase while async workers remain out of scope.
- [Users may expect full autonomy from the word Agent] -> mitigated by a deliberately narrow executor design and explicit non-goals.

## Migration Plan

This is an additive change on top of vector retrieval and streaming RAG chat.

Suggested rollout order:

1. Add Agent task configuration and persistence model.
2. Define the Skill base contract and registry.
3. Implement the Task Router Agent and Agent Executor.
4. Implement retrieval-backed and synthesis skills on top of existing project retrieval.
5. Add owner-scoped Agent run API.
6. Add the frontend project Agent page.
7. Update docs and validate routing, ownership isolation, and evidence-first degradation behavior.

Rollback path:

- remove Agent APIs
- remove Agent task persistence
- remove Skill registry and executor wiring
- keep vector retrieval and project chat intact

## Open Questions

- Should the frontend expose explicit task-type selection first, or should the first UX be prompt-only with router inference?
- For `PaperSummarySkill`, should explicit document targeting be required in the first implementation, or may the system summarize the top relevant document when no document is selected?
- Should `agent_tasks` history be listable immediately in this change, or is synchronous submit-plus-return sufficient while still persisting the records?
