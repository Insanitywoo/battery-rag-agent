# Battery-RAG Agent Product Spec

## Purpose

This document is the project-level source of truth for the Battery-RAG Agent product scope. It defines what the product is, who it serves, which business objects matter, and what is included in the initial MVP.

## Product Positioning

Battery-RAG Agent is an online research copilot for lithium-ion battery, energy storage, BMS, control engineering, and AI research workflows.

It is not a generic chatbot and not a paper-writing autopilot. Its primary value is combining:

- project-scoped knowledge bases built from user documents,
- evidence-grounded RAG question answering,
- agent-orchestrated research workflows,
- structured skills for repeatable research tasks,
- exportable research outputs with traceable sources.

## Product Goals

- Help researchers read and reuse technical literature faster.
- Reduce time spent on manual note-taking, comparison, and draft structuring.
- Keep generated answers tied to user-provided or explicitly cited sources.
- Provide a project-based workspace where documents, chats, reports, and outputs stay organized.

## Non-Goals

- Fully autonomous paper writing without human review.
- Fabrication of claims, citations, references, or experimental results.
- Broad enterprise document management outside the battery/engineering research use case in the MVP.
- Real-time collaboration, billing, or public marketplace features in the MVP.

## User Roles

### Primary Users

- Graduate students researching batteries, BMS, energy storage, control, or applied AI.
- Academic researchers building topic-specific literature collections and technical reports.
- Engineering practitioners querying internal technical documents, standards, and test reports.

### System Roles

- End User: owns projects, uploads documents, runs chat and agent tasks, exports outputs.
- Admin: monitors platform health, user activity, task failures, and abuse signals. Admin access must not bypass data ownership without explicit privileged workflows.

## Core User Jobs

- Create a research project around a topic or task.
- Upload papers, notes, datasets, and bibliography files.
- Ask evidence-grounded questions over a project knowledge base.
- Summarize a paper or compare multiple papers.
- Generate draft research artifacts such as outlines or related work notes.
- Analyze experiment tables and export structured outputs.

## Core Business Objects

The product must treat the following as first-class objects:

- User: authenticated account and platform owner identity.
- Project: isolated workspace for a research topic or deliverable.
- Document: uploaded source artifact such as PDF, Markdown, TXT, DOCX, CSV, XLSX, or BibTeX.
- Knowledge Base: project-scoped indexed representation derived from documents.
- Chunk: retrievable evidence unit linked to a source document and location metadata.
- Chat Session: conversational history within a project.
- Message: user or assistant turn within a chat session.
- Agent Task: long-running task routed to one or more skills.
- Skill Result: structured output produced by a skill with provenance metadata.
- Report / Export Artifact: generated markdown, LaTeX, DOCX, BibTeX, charts, or packaged output.
- Usage Record: meter of user actions for quota, cost, and abuse monitoring.

## System Boundary

The platform is responsible for:

- authentication and project ownership,
- document ingestion and indexing,
- retrieval and evidence-grounded generation,
- agent orchestration over approved skills,
- export of user-requested outputs,
- logging, quotas, and administrative observability.

The platform is not responsible for:

- guaranteeing scientific correctness without user review,
- acting as a source of truth when evidence is absent,
- training custom foundation models in the MVP,
- publishing or sharing user documents publicly by default.

## MVP Scope

The MVP is a web product focused on a single-user workflow inside a multi-user system.

### Included

- User registration and login.
- Project creation and project list.
- Document upload and processing status.
- Project-scoped knowledge base build.
- RAG chat with source snippets.
- Chat history persistence.
- Agent entry points for:
  - single-paper summary,
  - multi-paper comparison,
  - related work drafting,
  - outline drafting,
  - basic experiment analysis.
- Export to Markdown as the required MVP output format.

### Deferred Beyond MVP

- Payments and subscription checkout.
- Team collaboration and shared workspaces.
- Fine-grained RBAC beyond user/admin roles.
- External search as a mandatory capability.
- Fully automated LaTeX compilation pipeline.
- Word export, public APIs for third parties, and plugin ecosystems.

## Product Quality Bar

- Every substantive answer should expose usable evidence or explicitly say evidence is insufficient.
- Every user-visible artifact should be project-scoped and recoverable later.
- Long-running tasks should have observable status.
- The interface should make it clear which outputs are assistant-generated and require user validation.

## Success Criteria For MVP

- A user can create a project, upload documents, and complete project-scoped Q&A.
- Answers show document name, location metadata, and source snippet.
- At least one agent task can produce a saved markdown artifact with source notes.
- Users cannot access other users' projects, documents, chats, or exports.
