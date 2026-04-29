# Battery-RAG Agent Security and Privacy Spec

## Purpose

This document defines the baseline security, privacy, and safety requirements for Battery-RAG Agent.

## Security Principles

- Default deny for cross-project and cross-user access.
- Secrets stay server-side only.
- Least privilege across APIs, storage, and background tasks.
- Defense in depth for uploads, retrieval, generation, and exports.
- User-visible AI outputs must not imply certainty when evidence is weak or absent.

## Identity and Access Control

### Authentication

- Users must authenticate before accessing project-scoped resources.
- Session or token design may evolve, but backend must own verification and identity resolution.
- Admin access must be explicit and auditable.

### Authorization

- Every project-scoped request must verify the authenticated user owns the target project.
- Document, chat, export, and agent-task access must derive from project authorization rather than trusting raw object identifiers.
- Background workers must process tasks using persisted ownership metadata and must not bypass ownership checks silently.

## Data Isolation Requirements

- No user may read, retrieve, download, or infer another user's project data through normal product flows.
- Vector retrieval must enforce ownership filters at query time.
- Export artifacts must require backend-mediated download authorization.
- Logs must avoid leaking raw sensitive document content unless explicitly required for debugging and separately protected.

## File Upload Safety

### Allowed File Classes

- PDF
- TXT
- MD
- DOCX
- CSV
- XLSX
- BibTeX

### Required Controls

- Enforce file size limits.
- Normalize stored filenames and avoid using raw user-supplied names as storage keys.
- Reject executable and unsupported file types.
- Track upload status and parsing failures safely.

The MVP must prefer a conservative parser set over broad file-type support.

## Secrets Management

- API keys and provider credentials must exist only in backend environment variables or secret stores.
- Frontend must never embed model provider keys.
- Repository must ship `.env.example` and must not commit real secrets.
- Logs and error messages must redact secrets.

## Privacy Principles

- User uploads are treated as private working materials by default.
- The platform must not expose user documents publicly unless an explicit future sharing feature is introduced.
- Users should be able to delete uploaded documents and derived artifacts within product constraints.
- Generated outputs remain user-owned project artifacts and inherit the same access rules as source documents.

## AI Safety and Research Integrity

- The system must not fabricate citations, papers, or experiment results.
- Unsupported claims should be flagged as unsupported rather than stated as fact.
- Writing assistance must be framed as draft support requiring user verification.
- Citation and evidence checks are part of product safety, not optional polish.

## External Tool Safety

- External tools must be allowlisted and integrated through controlled server-side wrappers.
- End users must not receive arbitrary shell or Python execution capability.
- Python-based analysis must run only through predefined analysis functions with size and timeout limits.
- External web retrieval used in research outputs must preserve source attribution and reliability cues.

## Storage and Download Controls

- Original files and generated exports must be stored outside publicly guessable URLs when possible.
- Download endpoints must check authentication and ownership before streaming files.
- Derived files should carry metadata linking them to `user_id`, `project_id`, and source task identifiers.

## Auditing and Abuse Monitoring

- The platform should record usage logs for key actions such as uploads, chat requests, agent runs, and exports.
- Security-relevant failures should be logged with enough metadata for diagnosis without exposing secrets.
- Admin tooling must prioritize observability over unrestricted data browsing.

## MVP Security Baseline

The MVP must include:

- authenticated access,
- project ownership checks,
- secure secret handling,
- conservative file validation,
- backend-only provider access,
- authorized file download,
- usage logging,
- evidence-aware answer behavior.

The MVP may defer:

- full enterprise audit tooling,
- SSO,
- granular role matrices,
- customer-managed encryption keys,
- formal data residency controls.
