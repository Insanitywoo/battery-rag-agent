## Why

Battery-RAG Agent already supports owner-scoped project retrieval, streaming RAG chat, and a bounded Agent plus Skills framework for research tasks. The next product step is to extend that foundation into a paper-writing assistant that helps researchers structure and draft grounded writing artifacts from their current project evidence without turning the system into an unrestricted paper ghostwriting tool.

Without a dedicated writing layer, writing-oriented outputs such as outline drafts, introduction structure, related-work scaffolds, and conclusion summaries would remain mixed into generic Agent responses with no durable artifact model, no history view, and no export path. This change introduces a writing-assistant capability that persists writing results, keeps evidence and unsupported-claim markers attached to each artifact, and exposes a project-scoped frontend workspace for writing assistance.

## What Changes

- Add a project-scoped Paper Writing page in the frontend.
- Let the user enter a paper topic, research direction, and writing requirements.
- Let the user select or auto-route a writing task type.
- Extend the Task Router so writing-oriented requests can be identified safely.
- Add or extend the following writing-oriented Skills:
  - `WritingOutlineSkill`
  - `IntroductionOutlineSkill`
  - `RelatedWorkDraftSkill`
  - `MethodFrameworkSkill`
  - `ConclusionDraftSkill`
  - `CitationCheckSkill`
  - `MarkdownExportSkill`
- Add `writing_artifacts` persistence for owner-scoped saved writing outputs.
- Save `content_markdown`, `sources_json`, and `unsupported_claims_json` for each writing artifact.
- Add authenticated owner-scoped writing APIs:
  - `POST /api/projects/{project_id}/writing/run`
  - `GET /api/projects/{project_id}/writing/artifacts`
  - `GET /api/projects/{project_id}/writing/artifacts/{artifact_id}`
  - `DELETE /api/projects/{project_id}/writing/artifacts/{artifact_id}`
  - `GET /api/projects/{project_id}/writing/artifacts/{artifact_id}/export/markdown`
- Keep writing generation evidence-first and require unsupported conclusions to be marked as needing manual confirmation.
- Forbid fabricated references, fabricated experiments, fabricated results, and fabricated sources.
- Update `README.md` with writing-assistant usage and limitations.

## Capabilities

### New Capabilities

- `project-paper-writing-assistant`: Defines project-scoped writing artifact generation, persistence, history, deletion, and Markdown export under evidence-first constraints.

### Modified Capabilities

- `project-agent-skills-framework`: Extends the Agent and Skills framework with writing-oriented task routing and writing-focused Skills that still reuse owner-scoped retrieval and evidence constraints.
- `backend-shell`: Expands accepted backend scope to include project-scoped paper-writing assistant APIs and artifact persistence.
- `frontend-auth-workspace`: Expands the authenticated project workspace with a dedicated Paper Writing page and artifact history view.
- `user-project-workspace`: Expands project detail navigation to include a paper-writing entry point.
- `local-dev-infra`: Extends documentation expectations to include writing-assistant usage, limits, and any writing-related configuration or export notes.

## Impact

- Affected code: backend writing services, artifact persistence models, writing APIs, Agent routing rules, writing-oriented Skills, frontend project writing page, artifact history views, and documentation.
- Affected APIs: writing run, list, detail, delete, and Markdown export endpoints; routing logic reused from the Agent framework.
- Affected systems: PostgreSQL writing artifact persistence, backend LLM prompt assembly, owner-scoped retrieval reuse, and Markdown export generation.
- Dependencies likely introduced or activated: structured writing artifact serialization, artifact history views, and backend Markdown export formatting helpers.
