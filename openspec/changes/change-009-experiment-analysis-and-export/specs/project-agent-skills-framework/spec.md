## MODIFIED Requirements

### Requirement: Agent execution SHALL support bounded experiment-result analysis workflows
The system SHALL allow experiment-analysis-oriented flows in this capability to use owner-scoped experiment dataset metadata, descriptive statistics, and controlled chart outputs, and the Agent or Skill layer SHALL remain bounded to dataset-grounded analysis rather than open-ended modeling or arbitrary code execution.

#### Scenario: Experiment analysis uses saved dataset-derived facts safely
- **WHEN** an authenticated owner runs an experiment-analysis-oriented task for a dataset in a project they own
- **THEN** the Agent or bounded Skill layer MAY use saved experiment dataset facts, statistics, and chart descriptions while preserving owner and project isolation
