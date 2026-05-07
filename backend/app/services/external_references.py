from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
import html
import re
import xml.etree.ElementTree as ET
from urllib.parse import quote_plus

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.external_reference import ExternalReference


class ExternalToolError(Exception):
    pass


def _clean_text(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = re.sub(r"\s+", " ", html.unescape(value)).strip()
    return cleaned or None


def normalize_doi(value: str | None) -> str | None:
    cleaned = _clean_text(value)
    if not cleaned:
        return None
    lowered = cleaned.lower()
    lowered = lowered.removeprefix("https://doi.org/")
    lowered = lowered.removeprefix("http://doi.org/")
    lowered = lowered.removeprefix("doi:")
    lowered = lowered.strip().strip("/")
    return lowered or None


def normalize_title(value: str | None) -> str:
    cleaned = (_clean_text(value) or "").lower()
    normalized = re.sub(r"[^a-z0-9]+", " ", cleaned)
    return re.sub(r"\s+", " ", normalized).strip()


def build_reference_dedupe_key(*, doi: str | None, title: str) -> str:
    normalized_doi = normalize_doi(doi)
    if normalized_doi:
        return f"doi:{normalized_doi}"
    return f"title:{normalize_title(title)}"


def _truncate(value: str | None, *, limit: int) -> str | None:
    cleaned = _clean_text(value)
    if not cleaned:
        return None
    if len(cleaned) <= limit:
        return cleaned
    return f"{cleaned[: limit - 3].rstrip()}..."


def _build_metadata_warnings(*, source: str, doi: str | None, url: str | None, authors: list[str], year: int | None) -> list[str]:
    warnings: list[str] = []
    if not doi:
        warnings.append(f"{source} result is missing a DOI. Verify the citation manually before reuse.")
    if not url:
        warnings.append(f"{source} result is missing a source URL. Verify the citation manually before reuse.")
    if not authors:
        warnings.append(f"{source} result is missing author metadata. Verify authors before exporting BibTeX.")
    if year is None:
        warnings.append(f"{source} result is missing publication year metadata. Verify the citation manually.")
    return warnings


@dataclass(frozen=True)
class ExternalSearchInput:
    query: str | None
    doi: str | None
    limit: int


@dataclass(frozen=True)
class ExternalReferenceCandidate:
    source: str
    title: str
    authors: list[str] = field(default_factory=list)
    year: int | None = None
    venue: str | None = None
    doi: str | None = None
    url: str | None = None
    abstract: str | None = None
    warnings: list[str] = field(default_factory=list)

    @property
    def dedupe_key(self) -> str:
        return build_reference_dedupe_key(doi=self.doi, title=self.title)


class ExternalTool(ABC):
    tool_name: str

    @abstractmethod
    def search(self, search_input: ExternalSearchInput) -> list[ExternalReferenceCandidate]:
        raise NotImplementedError


class BibTeXTool:
    tool_name = "bibtex"

    def render_candidate(self, candidate: ExternalReferenceCandidate) -> str:
        key_root = normalize_title(candidate.title).replace(" ", "_") or "reference"
        year_suffix = str(candidate.year) if candidate.year is not None else "noyear"
        citation_key = f"{key_root[:48]}_{year_suffix}".strip("_")
        author_text = " and ".join(candidate.authors) if candidate.authors else "Unknown Author"
        lines = [
            "@article{" + citation_key + ",",
            f"  title = {{{candidate.title}}},",
            f"  author = {{{author_text}}},",
        ]
        if candidate.year is not None:
            lines.append(f"  year = {{{candidate.year}}},")
        if candidate.venue:
            lines.append(f"  journal = {{{candidate.venue}}},")
        if candidate.doi:
            lines.append(f"  doi = {{{candidate.doi}}},")
        if candidate.url:
            lines.append(f"  url = {{{candidate.url}}},")
        lines.append(f"  note = {{Draft BibTeX generated from {candidate.source}. Manual verification required.}}")
        lines.append("}")
        return "\n".join(lines)


class CrossRefTool(ExternalTool):
    tool_name = "crossref"

    def __init__(self) -> None:
        self.settings = get_settings()

    def search(self, search_input: ExternalSearchInput) -> list[ExternalReferenceCandidate]:
        params: dict[str, str | int] = {"rows": search_input.limit}
        normalized_doi = normalize_doi(search_input.doi)
        if normalized_doi:
            params["query.bibliographic"] = normalized_doi
        elif search_input.query:
            params["query.bibliographic"] = search_input.query.strip()
        else:
            return []

        if self.settings.crossref_mailto:
            params["mailto"] = self.settings.crossref_mailto

        try:
            response = httpx.get(
                "https://api.crossref.org/works",
                params=params,
                headers={"User-Agent": self.settings.external_tool_user_agent},
                timeout=self.settings.external_search_timeout_seconds,
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise ExternalToolError("Crossref search failed.") from exc

        payload = response.json()
        items = payload.get("message", {}).get("items", [])
        if not isinstance(items, list):
            raise ExternalToolError("Crossref returned an invalid response.")

        results: list[ExternalReferenceCandidate] = []
        for item in items:
            title = _clean_text((item.get("title") or [None])[0] if isinstance(item.get("title"), list) else item.get("title"))
            if not title:
                continue
            doi = normalize_doi(item.get("DOI"))
            authors = [
                " ".join(part for part in [_clean_text(person.get("given")), _clean_text(person.get("family"))] if part)
                for person in (item.get("author") or [])
                if isinstance(person, dict)
            ]
            issued = item.get("issued", {})
            year = None
            if isinstance(issued, dict):
                parts = issued.get("date-parts") or []
                if parts and isinstance(parts[0], list) and parts[0]:
                    try:
                        year = int(parts[0][0])
                    except (TypeError, ValueError):
                        year = None
            venue = _clean_text((item.get("container-title") or [None])[0] if isinstance(item.get("container-title"), list) else item.get("container-title"))
            url = _clean_text(item.get("URL"))
            abstract = _truncate(item.get("abstract"), limit=1200)
            warnings = _build_metadata_warnings(
                source="Crossref",
                doi=doi,
                url=url,
                authors=[author for author in authors if author],
                year=year,
            )
            results.append(
                ExternalReferenceCandidate(
                    source="crossref",
                    title=title,
                    authors=[author for author in authors if author],
                    year=year,
                    venue=venue,
                    doi=doi,
                    url=url,
                    abstract=abstract,
                    warnings=warnings,
                )
            )
        return results


class ArxivTool(ExternalTool):
    tool_name = "arxiv"

    def __init__(self) -> None:
        self.settings = get_settings()

    def search(self, search_input: ExternalSearchInput) -> list[ExternalReferenceCandidate]:
        query = _clean_text(search_input.query) or normalize_doi(search_input.doi)
        if not query:
            return []

        encoded_query = quote_plus(query)
        url = (
            "http://export.arxiv.org/api/query"
            f"?search_query=all:{encoded_query}&start=0&max_results={search_input.limit}"
        )
        try:
            response = httpx.get(
                url,
                headers={"User-Agent": self.settings.external_tool_user_agent},
                timeout=self.settings.external_search_timeout_seconds,
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise ExternalToolError("arXiv search failed.") from exc

        try:
            root = ET.fromstring(response.text)
        except ET.ParseError as exc:
            raise ExternalToolError("arXiv returned an invalid response.") from exc

        namespace = {"atom": "http://www.w3.org/2005/Atom"}
        results: list[ExternalReferenceCandidate] = []
        for entry in root.findall("atom:entry", namespace):
            title = _clean_text(entry.findtext("atom:title", default="", namespaces=namespace))
            if not title:
                continue
            published = _clean_text(entry.findtext("atom:published", default="", namespaces=namespace))
            year = None
            if published:
                try:
                    year = datetime.fromisoformat(published.replace("Z", "+00:00")).year
                except ValueError:
                    year = None
            authors = [
                _clean_text(author.findtext("atom:name", default="", namespaces=namespace)) or ""
                for author in entry.findall("atom:author", namespace)
            ]
            abstract = _truncate(entry.findtext("atom:summary", default="", namespaces=namespace), limit=1200)
            url = _clean_text(entry.findtext("atom:id", default="", namespaces=namespace))
            doi = None
            for link in entry.findall("atom:link", namespace):
                title_attr = link.attrib.get("title", "")
                href = _clean_text(link.attrib.get("href"))
                if title_attr.lower() == "doi" and href:
                    doi = normalize_doi(href)
                    break
            warnings = _build_metadata_warnings(
                source="arXiv",
                doi=doi,
                url=url,
                authors=[author for author in authors if author],
                year=year,
            )
            if doi is None:
                warnings.insert(0, "arXiv results often identify preprints without DOI. Treat them as external references and verify the final citation manually.")
            results.append(
                ExternalReferenceCandidate(
                    source="arxiv",
                    title=title,
                    authors=[author for author in authors if author],
                    year=year,
                    venue="arXiv",
                    doi=doi,
                    url=url,
                    abstract=abstract,
                    warnings=warnings,
                )
            )
        return results


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, ExternalTool] = {}

    def register(self, tool: ExternalTool) -> None:
        self._tools[tool.tool_name] = tool

    def available_tools(self) -> tuple[str, ...]:
        return tuple(self._tools.keys())

    def search(self, *, provider: str, search_input: ExternalSearchInput) -> tuple[list[ExternalReferenceCandidate], list[str]]:
        selected_tools: list[ExternalTool]
        if provider == "all":
            selected_tools = list(self._tools.values())
        else:
            tool = self._tools.get(provider)
            if tool is None:
                raise ExternalToolError("Unsupported external provider.")
            selected_tools = [tool]

        warnings: list[str] = []
        combined_results: list[ExternalReferenceCandidate] = []
        for tool in selected_tools:
            try:
                combined_results.extend(tool.search(search_input))
            except ExternalToolError as exc:
                warnings.append(str(exc))

        deduped = dedupe_candidates(combined_results)[: search_input.limit]
        return deduped, warnings


def dedupe_candidates(candidates: list[ExternalReferenceCandidate]) -> list[ExternalReferenceCandidate]:
    deduped: dict[str, ExternalReferenceCandidate] = {}
    for candidate in candidates:
        key = candidate.dedupe_key
        existing = deduped.get(key)
        if existing is None:
            deduped[key] = candidate
            continue

        existing_score = int(bool(existing.doi)) + len(existing.authors) + int(bool(existing.abstract))
        candidate_score = int(bool(candidate.doi)) + len(candidate.authors) + int(bool(candidate.abstract))
        if candidate_score > existing_score:
            deduped[key] = candidate
    return list(deduped.values())


def get_external_tool_registry() -> ToolRegistry:
    registry = ToolRegistry()
    registry.register(CrossRefTool())
    registry.register(ArxivTool())
    return registry


def get_bibtex_tool() -> BibTeXTool:
    return BibTeXTool()


def persist_external_reference(
    db: Session,
    *,
    user_id: str,
    project_id: str,
    candidate: ExternalReferenceCandidate,
) -> ExternalReference:
    dedupe_key = candidate.dedupe_key
    existing = next(
        (
            reference
            for reference in list_saved_external_references(db, user_id=user_id, project_id=project_id)
            if build_reference_dedupe_key(doi=reference.doi, title=reference.title) == dedupe_key
        ),
        None,
    )

    bibtex = get_bibtex_tool().render_candidate(candidate)
    if existing is not None:
        existing.source = candidate.source
        existing.title = candidate.title
        existing.authors_json = list(candidate.authors)
        existing.year = candidate.year
        existing.venue = candidate.venue
        existing.doi = normalize_doi(candidate.doi)
        existing.url = candidate.url
        existing.abstract = candidate.abstract
        existing.bibtex = bibtex
        db.add(existing)
        db.commit()
        db.refresh(existing)
        return existing

    reference = ExternalReference(
        user_id=user_id,
        project_id=project_id,
        source=candidate.source,
        title=candidate.title,
        authors_json=list(candidate.authors),
        year=candidate.year,
        venue=candidate.venue,
        doi=normalize_doi(candidate.doi),
        url=candidate.url,
        abstract=candidate.abstract,
        bibtex=bibtex,
    )
    db.add(reference)
    db.commit()
    db.refresh(reference)
    return reference


def list_saved_external_references(
    db: Session,
    *,
    user_id: str,
    project_id: str,
    limit: int | None = None,
) -> list[ExternalReference]:
    statement = (
        select(ExternalReference)
        .where(
            ExternalReference.user_id == user_id,
            ExternalReference.project_id == project_id,
        )
        .order_by(ExternalReference.updated_at.desc(), ExternalReference.created_at.desc())
    )
    if limit is not None:
        statement = statement.limit(limit)
    return list(db.scalars(statement))


def get_saved_external_reference(
    db: Session,
    *,
    user_id: str,
    project_id: str,
    reference_id: str,
) -> ExternalReference | None:
    return db.scalar(
        select(ExternalReference).where(
            ExternalReference.id == reference_id,
            ExternalReference.user_id == user_id,
            ExternalReference.project_id == project_id,
        )
    )


def build_reference_warnings(reference: ExternalReference) -> list[str]:
    warnings = _build_metadata_warnings(
        source=reference.source,
        doi=reference.doi,
        url=reference.url,
        authors=list(reference.authors_json or []),
        year=reference.year,
    )
    if not reference.bibtex:
        warnings.append("BibTeX draft is unavailable for this reference. Verify metadata manually.")
    return warnings


def build_external_reference_context(reference: ExternalReference) -> str:
    author_text = ", ".join(reference.authors_json or []) or "Unknown authors"
    year_text = str(reference.year) if reference.year is not None else "Year unavailable"
    venue_text = reference.venue or "Venue unavailable"
    doi_text = reference.doi or "DOI unavailable"
    url_text = reference.url or "URL unavailable"
    abstract_text = reference.abstract or "Abstract unavailable."
    return (
        f"[External Reference] {reference.title}\n"
        f"Source: {reference.source}\n"
        f"Authors: {author_text}\n"
        f"Year: {year_text}\n"
        f"Venue: {venue_text}\n"
        f"DOI: {doi_text}\n"
        f"URL: {url_text}\n"
        f"Abstract: {abstract_text}"
    )


def build_external_reference_markdown(reference: ExternalReference) -> str:
    author_text = ", ".join(reference.authors_json or []) or "Unknown authors"
    year_text = str(reference.year) if reference.year is not None else "Year unavailable"
    venue_text = reference.venue or "Venue unavailable"
    doi_text = reference.doi or "DOI unavailable"
    url_text = reference.url or "URL unavailable"
    return (
        f"- External reference: {reference.title}\n"
        f"  Authors: {author_text}\n"
        f"  Source: {reference.source} | Year: {year_text} | Venue: {venue_text}\n"
        f"  DOI: {doi_text}\n"
        f"  URL: {url_text}"
    )


def build_external_references_export(references: list[ExternalReference]) -> str:
    header = [
        "% Battery-RAG Agent external references BibTeX draft export",
        "% Manual verification required before publication or submission.",
    ]
    body = [reference.bibtex.strip() for reference in references if reference.bibtex.strip()]
    return "\n\n".join(header + body)


def build_search_candidate_response(candidate: ExternalReferenceCandidate) -> dict[str, object]:
    return {
        "source": candidate.source,
        "title": candidate.title,
        "authors": list(candidate.authors),
        "year": candidate.year,
        "venue": candidate.venue,
        "doi": normalize_doi(candidate.doi),
        "url": candidate.url,
        "abstract": candidate.abstract,
        "warnings": list(candidate.warnings),
        "dedupe_key": candidate.dedupe_key,
    }


def build_external_reference_response(reference: ExternalReference) -> dict[str, object]:
    return {
        "id": reference.id,
        "user_id": reference.user_id,
        "project_id": reference.project_id,
        "source": reference.source,
        "title": reference.title,
        "authors": list(reference.authors_json or []),
        "year": reference.year,
        "venue": reference.venue,
        "doi": reference.doi,
        "url": reference.url,
        "abstract": reference.abstract,
        "bibtex": reference.bibtex,
        "warnings": build_reference_warnings(reference),
        "created_at": reference.created_at,
        "updated_at": reference.updated_at,
    }


def build_external_reference_context_response(reference: ExternalReference) -> dict[str, object]:
    return {
        "id": reference.id,
        "label": "external reference",
        "source": reference.source,
        "title": reference.title,
        "authors": list(reference.authors_json or []),
        "year": reference.year,
        "venue": reference.venue,
        "doi": reference.doi,
        "url": reference.url,
        "abstract": reference.abstract,
        "warnings": build_reference_warnings(reference),
    }


def build_external_reference_export_filename(project_id: str) -> str:
    return f"external-references-{project_id}.bib"


def build_external_reference_warning_summary(references: list[ExternalReference]) -> list[str]:
    warnings: list[str] = []
    for reference in references:
        warnings.extend(build_reference_warnings(reference))
    deduped: list[str] = []
    seen: set[str] = set()
    for warning in warnings:
        if warning in seen:
            continue
        seen.add(warning)
        deduped.append(warning)
    return deduped
