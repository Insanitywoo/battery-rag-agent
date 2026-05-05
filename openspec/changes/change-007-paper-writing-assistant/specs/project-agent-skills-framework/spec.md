## MODIFIED Requirements

### Requirement: The Task Router Agent SHALL classify only supported bounded research tasks
The system SHALL route user inputs only among the supported task types in this capability, and this change SHALL expand the bounded task set to include writing-oriented tasks such as `introduction_outline`, `related_work_draft`, `method_framework`, `conclusion_draft`, `citation_check`, and `markdown_export` in addition to the existing bounded research tasks.

#### Scenario: Writing task type stays within supported set
- **WHEN** the router classifies a writing-oriented user request
- **THEN** the routed task type SHALL be one of the supported bounded writing or research task types for this capability

### Requirement: Agent execution SHALL remain evidence-first
Every Skill in this capability SHALL prefer project evidence over unsupported synthesis, SHALL avoid fabricating conclusions, and SHALL mark unsupported or weakly supported content with warnings or manual-confirmation language, including writing-oriented outputs.

#### Scenario: Writing-oriented Skill avoids fabricated citations
- **WHEN** a writing-oriented Skill lacks enough evidence to support a citation, result, or claim
- **THEN** the system SHALL return unsupported-claim markers or manual-confirmation language rather than inventing references, experiments, or sources
