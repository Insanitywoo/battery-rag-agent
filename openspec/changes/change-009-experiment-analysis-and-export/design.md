## Context

Battery-RAG Agent already includes:

- authenticated owner-scoped users and projects
- owner-scoped document upload and local storage
- document ingestion, chunk persistence, and vector retrieval
- streaming RAG chat
- a bounded Agent plus Skills framework
- a paper-writing assistant
- external reference curation and BibTeX draft export

The next increment is a bounded experiment-analysis layer that lets users upload CSV experiment datasets, inspect parsed structure, compute descriptive statistics, generate controlled charts, produce Results-style analysis paragraphs, and export markdown or LaTeX fragments without executing arbitrary code.

This change crosses several boundaries:

- the backend must safely accept and parse CSV experiment files
- the system must persist datasets and derived outputs per owner and per project
- the backend must generate charts through controlled functions rather than user code
- the Skill layer must produce grounded analysis from dataset-derived facts only
- the frontend must expose a dedicated Experiment Analysis workspace
- markdown and LaTeX exports must remain owner-scoped and output-scoped

Primary constraints:

- only authenticated owners may upload, inspect, analyze, delete, or export experiment assets inside projects they own
- all `experiment_datasets` and `experiment_outputs` must bind to `user_id` and `project_id`
- CSV upload size must be bounded
- CSV parsing failures must return safe user-facing errors
- chart generation must stay backend-controlled and must not execute user code
- generated chart paths must remain inside configured storage or outputs roots
- experiment analysis must be based only on uploaded CSV data, parsed statistics, and chart metadata
- the frontend must not store or expose model keys
- this change must not introduce arbitrary Python execution, custom scripting, ML training, simulation, device control, or full PDF or Word export

## Goals / Non-Goals

**Goals:**

- add a project-scoped experiment dataset model for CSV uploads
- add a project-scoped experiment output model for saved stats, charts, analysis, and export fragments
- support bounded CSV parsing, preview, and column typing
- support descriptive statistics for numeric fields
- support controlled line-chart and bar-chart generation
- support a bounded Experiment Analysis Skill for Results-style paragraphs
- support markdown report export and LaTeX table fragment export
- expose a project-scoped Experiment Analysis page
- keep experiment assets owner-scoped, project-scoped, and safe from code execution

**Non-Goals:**

- arbitrary Python or notebook execution
- user-defined scripts
- reinforcement learning or model training jobs
- battery simulation or control-system simulation
- external hardware integration
- complex machine-learning pipelines
- full PDF or Word report export
- full LaTeX paper compilation
- cloud-scale compute orchestration
- Celery or queue-based async infrastructure unless a later change explicitly requires it

## Decisions

### Decision: Introduce dedicated experiment dataset and output persistence

This change should add:

- an `experiment_datasets` model
- an `experiment_outputs` model

Suggested `experiment_datasets` fields:

- `id`
- `user_id`
- `project_id`
- `filename`
- `original_filename`
- `file_size`
- `storage_path`
- `columns_json`
- `row_count`
- `created_at`
- `updated_at`

Suggested `experiment_outputs` fields:

- `id`
- `user_id`
- `project_id`
- `dataset_id`
- `output_type`
- `title`
- `content_markdown`
- `chart_path`
- `stats_json`
- `created_at`
- `updated_at`

This keeps raw CSV assets and derived analysis artifacts separate, durable, and owner-scoped.

### Decision: Use a dedicated experiment-analysis upload entry rather than overloading general document records

Although the repository already supports CSV upload in the document workflow, experiment-analysis should use a dedicated dataset model and API surface because:

- experiment CSV files need parsed schema metadata
- experiment outputs need explicit lineage to a dataset
- dataset preview and chart-generation flows are structurally different from literature-document flows
- this separation avoids overloading general document semantics with experiment-specific state

The implementation may reuse storage helpers, auth patterns, and file-validation primitives from the existing document system, but persistence and API contracts should remain dedicated.

### Decision: CSV parsing remains bounded and schema-first

The backend should:

- read CSV files as data only
- parse header names
- infer simple column types such as numeric, categorical, or text
- compute row counts
- retain a bounded preview subset for dataset detail responses

If parsing fails because the file is malformed, the system should return a safe user-facing error and should not crash the application.

### Decision: Statistics generation is limited to descriptive numeric summaries

This phase should support only bounded descriptive statistics for numeric columns:

- `count`
- `mean`
- `min`
- `max`
- `std`

This keeps the feature aligned with paper-ready results summaries without expanding into open-ended analytics or modeling.

### Decision: Chart generation must be backend-controlled and declarative

The API should accept a bounded chart request such as:

- chart type: `line` or `bar`
- x-axis field
- y-axis field
- optional title

The backend should render charts through a controlled plotting layer and save the chart file to a project-scoped output path. The system must not execute user code, user formulas, or user scripts.

### Decision: Experiment analysis paragraphs must be generated from dataset-derived facts only

This change should add a bounded Experiment Analysis Skill that uses:

- parsed dataset metadata
- computed statistics
- chart descriptions
- user-provided framing or analysis request

It should not use unrelated private project documents as experiment evidence unless a later change explicitly composes them. The paragraph should:

- stay suitable for Results or Experiments writing
- avoid fabricating trends or conclusions that are not supported by the dataset
- mark aggressive conclusions with `Need manual confirmation`
- return a clear insufficiency response when the data is too sparse

### Decision: Exports remain output-scoped and partial

This phase should support:

- markdown export for a saved experiment output
- LaTeX table fragment export for a saved experiment output

It should not support:

- full PDF report generation
- full paper compilation
- Word export

Markdown export should package the output title, dataset lineage, stored markdown, and selected stats or chart notes. LaTeX export should focus on tabular fragments derived from bounded statistics or preview rows.

### Decision: Frontend should expose a dedicated Experiment Analysis workspace

The frontend should add:

- an Experiment Analysis entry from project detail
- a project-scoped Experiment Analysis page

The page should support:

- CSV dataset upload
- dataset list and detail selection
- preview table display
- descriptive-statistics generation
- controlled chart-generation controls
- result-analysis generation
- output history display
- markdown and LaTeX export actions

### Decision: Chart and output storage paths must stay inside configured roots

Generated chart paths should be derived server-side and stored under a dedicated outputs root or a safe subdirectory under the existing storage root. Path construction must not use unsanitized user-controlled filenames directly.

## API Shape

Recommended API surface:

- `POST /api/projects/{project_id}/experiments/datasets`
  - authenticated owner-scoped CSV upload
- `GET /api/projects/{project_id}/experiments/datasets`
  - owner-scoped dataset list
- `GET /api/projects/{project_id}/experiments/datasets/{dataset_id}`
  - owner-scoped dataset detail including columns and preview
- `DELETE /api/projects/{project_id}/experiments/datasets/{dataset_id}`
  - owner-scoped dataset delete

- `POST /api/projects/{project_id}/experiments/datasets/{dataset_id}/stats`
  - compute and persist descriptive statistics output
- `POST /api/projects/{project_id}/experiments/datasets/{dataset_id}/charts`
  - generate and persist line or bar chart output
- `POST /api/projects/{project_id}/experiments/datasets/{dataset_id}/analysis`
  - generate and persist result-analysis markdown from dataset-derived facts
- `GET /api/projects/{project_id}/experiments/outputs`
  - list saved outputs for the current owner and project
- `DELETE /api/projects/{project_id}/experiments/outputs/{output_id}`
  - delete a saved output
- `GET /api/projects/{project_id}/experiments/outputs/{output_id}/export/markdown`
  - export one output as markdown
- `GET /api/projects/{project_id}/experiments/outputs/{output_id}/export/latex`
  - export one output as a LaTeX fragment

## Skill Contract

Expected Experiment Analysis Skill behavior:

- structured input from dataset identity, optional analysis prompt, bounded stats, and chart metadata
- structured output containing result paragraph, warnings, and optional dataset facts used
- no claims beyond dataset-derived evidence
- insufficiency fallback when row counts or numeric fields are inadequate

## Risks / Trade-offs

- [CSV type inference may be imperfect] -> mitigated by keeping inference simple and surfacing parsed column metadata to the user.
- [Users may assume analysis text is stronger than the data supports] -> mitigated by explicit evidence-only prompting and manual-confirmation warnings.
- [Charts could become an arbitrary code vector] -> mitigated by declarative chart requests and backend-controlled rendering only.
- [Large CSV files could destabilize local development] -> mitigated by bounded file-size limits and preview truncation.
- [Experiment datasets could be confused with literature documents] -> mitigated by using dedicated dataset and output models plus a dedicated UI workspace.

## Migration Plan

Suggested rollout order:

1. add experiment dataset and output models plus safe storage configuration
2. add CSV parsing, preview, and statistics helpers
3. add controlled chart-generation service and persisted chart outputs
4. add experiment-analysis Skill and result-output persistence
5. add frontend Experiment Analysis workspace
6. add markdown and LaTeX export flows
7. update docs and validate owner-scoped behavior

Rollback path:

- remove experiment dataset and output routes and services
- remove chart rendering and export helpers
- remove the Experiment Analysis page
- keep document, chat, Agent, writing, and external-reference capabilities intact

## Open Questions

- Should experiment dataset detail responses return only a bounded preview row set, or should preview pagination be introduced in a later change?
- Should the first LaTeX export focus only on descriptive-statistics tables, or also support bounded preview-row tables when explicitly requested?
