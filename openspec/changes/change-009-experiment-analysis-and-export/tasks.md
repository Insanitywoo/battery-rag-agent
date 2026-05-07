## 1. Experiment Dataset Foundation

- [x] 1.1 Add backend configuration, schemas, and persistence for `experiment_datasets` with owner and project lineage
- [x] 1.2 Add backend configuration, schemas, and persistence for `experiment_outputs` with dataset lineage and output typing
- [x] 1.3 Ensure every dataset and output binds to `user_id` and `project_id`

## 2. CSV Parsing and Preview

- [x] 2.1 Implement authenticated owner-scoped CSV dataset upload for experiment analysis
- [x] 2.2 Parse CSV headers, infer bounded column types, and persist `columns_json` plus `row_count`
- [x] 2.3 Implement owner-scoped dataset list and detail APIs with bounded preview rows
- [x] 2.4 Ensure CSV size limits and friendly parsing errors are enforced safely
- [x] 2.5 Ensure experiment dataset deletion removes both metadata and stored file safely

## 3. Statistics and Chart Outputs

- [x] 3.1 Implement descriptive statistics generation for numeric fields including `count`, `mean`, `min`, `max`, and `std`
- [x] 3.2 Persist statistics outputs as owner-scoped `experiment_outputs`
- [x] 3.3 Implement backend-controlled line-chart generation from bounded x/y field selections
- [x] 3.4 Implement backend-controlled bar-chart generation from bounded field selections
- [x] 3.5 Save generated chart files only within a safe storage or outputs root and persist chart outputs

## 4. Experiment Analysis Skill and Exports

- [x] 4.1 Add a bounded Experiment Analysis Skill with structured input and output contracts
- [x] 4.2 Ensure experiment analysis uses only CSV-derived facts, statistics, chart metadata, and explicit user framing
- [x] 4.3 Ensure unsupported or overly strong conclusions are marked with manual-confirmation warnings
- [x] 4.4 Persist result-analysis outputs as owner-scoped `experiment_outputs`
- [x] 4.5 Implement owner-scoped Markdown export for experiment outputs
- [x] 4.6 Implement owner-scoped LaTeX table fragment export for experiment outputs

## 5. Frontend Experiment Workspace

- [x] 5.1 Add a project-scoped Experiment Analysis page and workspace navigation entry
- [x] 5.2 Support CSV dataset upload and dataset list selection
- [x] 5.3 Display parsed dataset columns, row count, and bounded preview rows
- [x] 5.4 Support stats generation and saved output display
- [x] 5.5 Support line-chart and bar-chart generation through authenticated backend requests with `credentials: "include"`
- [x] 5.6 Support result-analysis generation and output history display
- [x] 5.7 Support Markdown and LaTeX export actions for saved outputs

## 6. Security and Documentation

- [x] 6.1 Verify unauthenticated users cannot upload, inspect, analyze, delete, or export experiment assets
- [x] 6.2 Verify users cannot access another user's project experiment datasets or outputs
- [x] 6.3 Verify frontend code never stores model keys or executes provider calls directly for experiment analysis
- [x] 6.4 Update `README.md` and `.env.example` with experiment-analysis configuration, storage, export limitations, and no-code-execution constraints

## 7. Validation

- [x] 7.1 Add backend tests for owner-scoped dataset upload, CSV parsing, stats generation, chart output creation, analysis persistence, and export behavior
- [x] 7.2 Add frontend validation coverage or run type/build checks for the Experiment Analysis workspace
- [x] 7.3 Run backend tests or startup checks, frontend type/build checks, and `openspec validate change-009-experiment-analysis-and-export`
