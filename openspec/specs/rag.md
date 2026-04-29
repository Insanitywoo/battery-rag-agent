# Battery-RAG Agent RAG Spec

## Purpose

This document defines how retrieval-augmented generation works in Battery-RAG Agent and establishes the evidence constraints that govern answers.

## RAG Mission

The RAG subsystem exists to answer project-scoped research questions using user-provided evidence and explicitly attributed sources. Its main job is not to maximize fluency. Its main job is to maximize useful, traceable, and bounded assistance.

## RAG Principles

- Retrieval is project-scoped by default.
- Answers should be grounded in retrieved evidence, not free-form speculation.
- Evidence must be presented in a user-inspectable format.
- When evidence is missing or weak, the system should abstain, narrow the claim, or ask for more context.
- Source attribution is part of the output contract, not an optional add-on.

## Inputs

The RAG pipeline may consume:

- project documents that have completed ingestion,
- optional user-selected document filters,
- current user question,
- optional chat history needed for context,
- retrieval parameters controlled by the backend.

## Evidence Units

The primary retrieval unit is a chunk derived from a source document.

Each chunk should preserve or reference:

- `document_id`
- `document_name`
- `project_id`
- `user_id`
- location metadata such as page number, section, row range, or source anchor when available
- source text

## Retrieval Scope

- Default scope is all ready documents in the active project.
- Users may narrow retrieval to selected documents or categories when the UI supports it.
- Cross-project retrieval is forbidden unless a future explicit cross-project feature is specified.

## RAG Output Contract

Every substantive RAG answer must return:

- `answer`
- `sources`

Each source should include, when available:

- `document_id`
- `document_name`
- `chunk_id`
- `score`
- location metadata
- snippet text

## Evidence Constraint Rules

### Hard Rules

- Do not present claims as supported when no retrieved evidence supports them.
- Do not fabricate citations, pages, or source documents.
- Do not blend unrelated retrieved snippets into a falsely specific conclusion.
- Do not answer outside authorized project scope.

### Response Behavior When Evidence Is Weak

When evidence quality is weak, the system should do one or more of the following:

- say that the evidence is insufficient,
- answer only the supported subset of the question,
- suggest which document or data is missing,
- recommend narrowing the question.

### Response Behavior For Research Writing Support

When the output is a draft, summary, or related work note:

- claims should remain tied to source notes,
- ambiguous statements should be marked for user verification,
- unsupported generalizations should be avoided,
- citations should be surfaced as notes or evidence references, not invented inline facts.

## Retrieval Quality Expectations

The MVP should support:

- chunking tuned for technical prose,
- top-k semantic retrieval,
- source snippet display,
- conservative prompt constraints.

Future upgrades may add:

- BM25 or hybrid retrieval,
- reranking,
- layout-aware PDF parsing,
- table-aware extraction,
- query rewriting,
- citation-aware ranking.

## Prompting Constraints

The backend prompt builder must instruct the model to:

- answer from provided context,
- admit uncertainty when context is insufficient,
- avoid fabricated references,
- preserve a concise evidence-grounded style,
- separate supported findings from assumptions when needed.

## Failure Modes To Guard Against

- Answering from model prior knowledge instead of retrieved evidence.
- Returning irrelevant but high-confidence sounding summaries.
- Losing document location metadata during ingestion or retrieval.
- Retrieving across users or projects.
- Treating generated summaries as validated scientific truth.

## MVP RAG Scope

The MVP must deliver:

- document ingestion into a project-scoped vector store,
- project-scoped retrieval,
- answers with source snippets,
- abstention or caution when evidence is insufficient,
- persistent chat history with answer and source metadata.

The MVP may defer:

- multimodal retrieval,
- formula parsing,
- citation graph reasoning,
- automatic internet-grounded synthesis,
- full benchmark-driven retrieval tuning.
