## ADDED Requirements

### Requirement: The system SHALL provide project-scoped experiment CSV dataset upload and preview
The system SHALL provide bounded CSV experiment dataset upload for authenticated owners inside projects they own, and it SHALL parse dataset schema metadata, persist dataset records, and return bounded preview information without executing user code.

#### Scenario: Authenticated owner uploads an experiment CSV dataset
- **WHEN** an authenticated owner uploads a valid CSV file inside a project they own
- **THEN** the system SHALL create an `experiment_datasets` record bound to that owner and project, persist the CSV file safely, and return parsed column metadata plus row count

#### Scenario: Malformed CSV upload fails safely
- **WHEN** an authenticated owner uploads a malformed or unsupported CSV payload for experiment analysis
- **THEN** the system SHALL return a friendly bounded error and SHALL NOT crash or execute any user content

### Requirement: Experiment datasets SHALL be listable, inspectable, and deletable only by the owner
The system SHALL allow the authenticated owner to list, inspect, and delete only their own experiment datasets inside the current project.

#### Scenario: Owner lists project experiment datasets
- **WHEN** an authenticated owner requests experiment datasets for a project they own
- **THEN** the system SHALL return only that owner's datasets for that project

#### Scenario: Cross-user experiment dataset access is blocked
- **WHEN** a user attempts to inspect or delete another user's experiment dataset
- **THEN** the system SHALL reject the request and SHALL NOT expose the other user's dataset metadata, preview rows, or stored file

### Requirement: The system SHALL provide bounded descriptive statistics for experiment datasets
The system SHALL compute bounded descriptive statistics for numeric experiment dataset fields, and this change SHALL include at least `count`, `mean`, `min`, `max`, and `std`.

#### Scenario: Numeric field statistics are generated
- **WHEN** an authenticated owner requests statistics for a valid experiment dataset in a project they own
- **THEN** the system SHALL compute and persist descriptive statistics for supported numeric fields within that owner and project scope

### Requirement: The system SHALL provide backend-controlled chart generation for experiment datasets
The system SHALL generate line and bar charts from bounded field selections through backend-controlled rendering functions only, and chart files SHALL be stored only within a safe configured root.

#### Scenario: Owner generates a line chart
- **WHEN** an authenticated owner submits a valid line-chart request for a dataset they own
- **THEN** the system SHALL render the chart through backend-controlled plotting, persist a project-scoped chart output, and SHALL NOT execute user code

#### Scenario: Invalid chart request is rejected safely
- **WHEN** a chart request references unsupported fields, incompatible field types, or invalid dataset scope
- **THEN** the system SHALL reject the request safely and SHALL NOT create unsafe chart files or outputs

### Requirement: Experiment outputs SHALL be persisted as owner-scoped project records
The system SHALL persist experiment-derived outputs as `experiment_outputs` records bound to `user_id`, `project_id`, and `dataset_id`.

#### Scenario: Experiment output is stored
- **WHEN** an authenticated owner generates statistics, a chart, a result-analysis paragraph, or an exportable table fragment for a dataset they own
- **THEN** the system SHALL store an `experiment_outputs` record with output type, title, chart path or markdown content when relevant, statistics payload, and timestamps for that owner and project

### Requirement: Experiment analysis SHALL remain dataset-grounded and evidence-first
Experiment-result analysis in this capability SHALL be based only on the uploaded CSV dataset, derived statistics, chart metadata, and explicit user framing, and it SHALL NOT fabricate unsupported findings or conclusions.

#### Scenario: Unsupported analysis claims are marked explicitly
- **WHEN** the experiment-analysis flow lacks enough data to support a strong result claim
- **THEN** the output SHALL return an insufficiency response or manual-confirmation warning rather than inventing conclusions

### Requirement: Experiment outputs SHALL be exportable only by the owner
The system SHALL allow the authenticated owner to export only their own experiment outputs inside the current project, and this change SHALL support markdown export plus LaTeX table fragment export only.

#### Scenario: Owner exports markdown experiment output
- **WHEN** an authenticated owner exports a saved experiment output as markdown
- **THEN** the returned markdown SHALL contain only that owner's current project output data

#### Scenario: Owner exports LaTeX fragment
- **WHEN** an authenticated owner exports a saved experiment output as a LaTeX table fragment
- **THEN** the returned LaTeX SHALL contain only that owner's current project output data and SHALL remain a partial fragment rather than a full compiled paper
