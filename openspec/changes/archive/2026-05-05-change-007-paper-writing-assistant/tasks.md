## 1. Writing Artifact Foundation

- [x] 1.1 Add backend configuration, schemas, and persistence for `writing_artifacts` with owner and project lineage
- [x] 1.2 Define structured writing request and response contracts including `content_markdown`, `sources`, `warnings`, and `unsupported_claims`
- [x] 1.3 Ensure writing artifact storage binds every record to `user_id` and `project_id`

## 2. Routing and Writing Skills

- [x] 2.1 Extend Task Router support for writing-oriented task types and safe clarification behavior
- [x] 2.2 Implement or extend `WritingOutlineSkill`, `IntroductionOutlineSkill`, `RelatedWorkDraftSkill`, `MethodFrameworkSkill`, `ConclusionDraftSkill`, `CitationCheckSkill`, and `MarkdownExportSkill`
- [x] 2.3 Ensure writing prompts include system instruction, user task, retrieved evidence chunks, source requirements, unsupported-claim requirements, and anti-fabrication rules
- [x] 2.4 Ensure every writing Skill remains evidence-first and marks unsupported conclusions as needing manual confirmation

## 3. Writing APIs

- [x] 3.1 Implement `POST /api/projects/{project_id}/writing/run` as an authenticated owner-scoped execution endpoint
- [x] 3.2 Implement owner-scoped writing artifact list and detail APIs
- [x] 3.3 Implement owner-scoped writing artifact delete API
- [x] 3.4 Implement owner-scoped Markdown export API for one writing artifact
- [x] 3.5 Ensure writing execution and export never bypass existing `user_id + project_id` isolation for chunks, vectors, artifacts, or sources

## 4. Frontend Paper Writing Workspace

- [x] 4.1 Add a project-scoped Paper Writing page and workspace navigation entry
- [x] 4.2 Support entering paper topic, research direction, writing requirements, and selected writing task type
- [x] 4.3 Render saved writing outputs including Markdown content, sources, warnings, and unsupported claims
- [x] 4.4 Support listing, viewing, and deleting the current user's writing artifacts in the current project
- [x] 4.5 Support Markdown export from the frontend using authenticated backend requests with `credentials: "include"`

## 5. Security and Documentation

- [x] 5.1 Verify unauthenticated users cannot use writing APIs
- [x] 5.2 Verify users cannot generate, view, delete, or export another user's writing artifacts
- [x] 5.3 Verify `sources_json` and `unsupported_claims_json` stay bound to the current user's current project evidence
- [x] 5.4 Update `README.md` and `.env.example` with writing-assistant usage, export behavior, and anti-fabrication limitations

## 6. Validation

- [x] 6.1 Add backend tests for owner-scoped writing generation, artifact persistence, delete, export, and unsupported-claim handling
- [x] 6.2 Add frontend validation coverage or run type/build checks for the Paper Writing workspace
- [x] 6.3 Run backend tests or startup checks and frontend type/build checks for the writing assistant
