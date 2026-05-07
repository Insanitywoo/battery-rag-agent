## Why

Battery-RAG Agent already supports owner-scoped document upload, retrieval, RAG chat, Agent workflows, paper-writing assistance, and external references. The next practical research need is a bounded experiment-analysis workflow so users can work with CSV experiment data inside the same project, inspect results, generate controlled charts, and produce exportable Results or Experiments fragments without leaving the platform.

Today the system has no first-class experiment-analysis layer. Users cannot upload project-scoped experiment CSV files as structured datasets, preview parsed columns and row counts, compute descriptive statistics, generate backend-controlled charts, save experiment outputs, or export markdown and LaTeX fragments for paper writing. This change adds a project-scoped experiment-analysis capability that remains owner-scoped, dataset-grounded, and safe from arbitrary code execution.

## What Changes

- Add a dedicated project-scoped experiment-analysis capability for CSV datasets and derived outputs.
- Add `experiment_datasets` persistence for uploaded CSV experiment files bound to `user_id` and `project_id`.
- Add `experiment_outputs` persistence for statistics, charts, result-analysis paragraphs, and export fragments.
- Add authenticated owner-scoped experiment dataset APIs:
  - `POST /api/projects/{project_id}/experiments/datasets`
  - `GET /api/projects/{project_id}/experiments/datasets`
  - `GET /api/projects/{project_id}/experiments/datasets/{dataset_id}`
  - `DELETE /api/projects/{project_id}/experiments/datasets/{dataset_id}`
- Add authenticated owner-scoped experiment output APIs:
  - `POST /api/projects/{project_id}/experiments/datasets/{dataset_id}/stats`
  - `POST /api/projects/{project_id}/experiments/datasets/{dataset_id}/charts`
  - `POST /api/projects/{project_id}/experiments/datasets/{dataset_id}/analysis`
  - `GET /api/projects/{project_id}/experiments/outputs`
  - `DELETE /api/projects/{project_id}/experiments/outputs/{output_id}`
  - `GET /api/projects/{project_id}/experiments/outputs/{output_id}/export/markdown`
  - `GET /api/projects/{project_id}/experiments/outputs/{output_id}/export/latex`
- Parse CSV headers and infer bounded column metadata for preview and chart configuration.
- Compute descriptive statistics for numeric fields including `count`, `mean`, `min`, `max`, and `std`.
- Generate line and bar charts using backend-controlled functions only.
- Save generated chart files under project-scoped output storage.
- Add a bounded Experiment Analysis Skill for Results-style paragraph generation from dataset-derived facts only.
- Add a project-scoped Experiment Analysis frontend page with dataset upload, preview, stats, charts, outputs, and export controls.
- Update `README.md` and `.env.example` with experiment-analysis configuration and limitations.

## Capabilities

### New Capabilities

- `project-experiment-analysis`: Defines owner-scoped experiment dataset upload, CSV preview, statistics, controlled chart generation, result-analysis persistence, and markdown or LaTeX fragment export.

### Modified Capabilities

- `project-agent-skills-framework`: Extends bounded Skills to include experiment-result analysis from project-scoped CSV-derived statistics and chart descriptions.
- `frontend-auth-workspace`: Expands the authenticated project workspace with an Experiment Analysis page and export actions.
- `user-project-workspace`: Expands project detail navigation to include an experiment-analysis entry point.
- `backend-shell`: Expands accepted backend scope to include bounded CSV experiment-analysis APIs and controlled chart generation.
- `local-dev-infra`: Extends documentation expectations to include experiment-analysis configuration, chart-output storage, and backend-only analysis settings.

## Impact

- Affected code: backend experiment dataset and output models, CSV parsing services, statistics helpers, controlled chart rendering helpers, experiment-analysis Skill logic, frontend experiment workspace, and documentation.
- Affected APIs: experiment dataset upload, list, detail, delete, statistics generation, chart generation, result analysis, output list, output delete, markdown export, and LaTeX export endpoints.
- Affected systems: PostgreSQL owner-scoped dataset and output persistence, local storage for CSV and generated charts, backend-only analysis prompt assembly, and project-scoped report export.
- Dependencies likely introduced or activated: CSV parsing helpers, numeric statistics helpers, safe plotting libraries, and backend-side export formatting utilities.
