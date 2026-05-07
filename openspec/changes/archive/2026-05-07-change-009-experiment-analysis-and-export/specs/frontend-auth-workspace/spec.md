## MODIFIED Requirements

### Requirement: Frontend MAY provide only bounded experiment-analysis workspace extensions in this change
The frontend SHALL provide a functional project-detail route for the authenticated owner that includes an Experiment Analysis entry point, and it SHALL provide a project-scoped Experiment Analysis page for CSV upload, preview, statistics, chart generation, saved outputs, and markdown or LaTeX export flows, but it MUST remain limited to bounded experiment-analysis scope and MUST NOT implement arbitrary code execution or unrestricted computation workflows.

#### Scenario: Project workspace includes experiment-analysis controls
- **WHEN** an authenticated owner uses the project workspace after this change
- **THEN** the frontend SHALL provide an Experiment Analysis workspace with dataset upload, preview, stats, chart, analysis, and export controls, and SHALL exclude unrelated arbitrary compute workflows

### Requirement: Frontend experiment-analysis flows SHALL use authenticated backend-only execution
The frontend SHALL call backend experiment-analysis endpoints with `credentials: "include"` and SHALL render parsed CSV, chart, and analysis outputs without exposing model secrets, plotting internals, or browser-stored tokens.

#### Scenario: Experiment-analysis request uses cookie-authenticated fetch
- **WHEN** the frontend sends a project experiment-analysis request
- **THEN** the request SHALL use authenticated backend calls with `credentials: "include"`

#### Scenario: Frontend never exposes provider secrets or code execution for experiment analysis
- **WHEN** the experiment-analysis implementation is reviewed
- **THEN** it SHALL not store model API keys in the browser, SHALL not call model providers directly from the frontend, and SHALL not expose arbitrary script execution controls
