## MODIFIED Requirements

### Requirement: Writing assistant SHALL support bounded reuse of saved external references
The writing assistant in this capability MAY reuse saved project-scoped `external_references` for related-work-oriented and citation-support-oriented writing flows, but it SHALL label them explicitly as external references and SHALL not treat them as uploaded-document evidence.

#### Scenario: Related-work drafting uses saved external references safely
- **WHEN** an authenticated owner generates a related-work-oriented or citation-support-oriented writing artifact
- **THEN** the writing assistant MAY incorporate saved external references with explicit external labeling while preserving the distinction from internal project evidence
