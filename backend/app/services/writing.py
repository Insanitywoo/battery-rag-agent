from __future__ import annotations

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from email.utils import format_datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.project import Project
from app.models.writing_artifact import WritingArtifact
from app.schemas.chat import SourceReferenceResponse
from app.schemas.writing import WritingArtifactResponse, WritingArtifactType
from app.services.agent_framework import DEFAULT_MANUAL_CONFIRMATION_WARNING
from app.services.llm_gateway import LLMGatewayError, PromptChunk, get_llm_gateway
from app.services.rag import INSUFFICIENT_INFORMATION_TEXT, RetrievedChunk, retrieve_project_chunks


SUPPORTED_WRITING_TASK_TYPES: tuple[WritingArtifactType, ...] = (
    "outline",
    "introduction_outline",
    "related_work",
    "method_framework",
    "conclusion",
    "citation_check",
)


class WritingExecutionError(Exception):
    pass


@dataclass(frozen=True)
class WritingRouteDecision:
    task_type: WritingArtifactType
    reason: str
    clarification: str | None = None


@dataclass(frozen=True)
class WritingContext:
    db: Session
    user_id: str
    project_id: str
    topic: str
    research_direction: str | None
    requirements: str | None
    task_type: WritingArtifactType
    route_reason: str

    @property
    def query_text(self) -> str:
        parts = [self.topic]
        if self.research_direction:
            parts.append(self.research_direction)
        if self.requirements:
            parts.append(self.requirements)
        return "\n".join(part.strip() for part in parts if part and part.strip())


@dataclass(frozen=True)
class WritingSkillResult:
    title: str
    content_markdown: str
    sources: list[SourceReferenceResponse]
    warnings: list[str]
    unsupported_claims: list[str]


def _dedupe_sources(chunks: list[RetrievedChunk]) -> list[SourceReferenceResponse]:
    seen: set[tuple[str, int, str]] = set()
    sources: list[SourceReferenceResponse] = []
    for chunk in chunks:
        key = (chunk.chunk_id, chunk.chunk_index, chunk.document_id)
        if key in seen:
            continue
        seen.add(key)
        sources.append(SourceReferenceResponse(**chunk.to_source_reference()))
    return sources


def _search_terms(text: str) -> list[str]:
    return [token for token in re.findall(r"[a-z0-9]{3,}", text.lower()) if token]


def _has_claim_support(claim: str, chunks: list[RetrievedChunk]) -> bool:
    terms = _search_terms(claim)
    if not terms:
        return False
    required_overlap = 1 if len(terms) == 1 else 2
    for chunk in chunks:
        lowered = chunk.content.lower()
        overlap = sum(1 for term in terms if term in lowered)
        if overlap >= required_overlap:
            return True
    return False


def _claim_candidates(text: str) -> list[str]:
    raw_parts = re.split(r"[\r\n]+|(?<=[.!?])\s+", text.strip())
    return [part.strip(" -\t") for part in raw_parts if part.strip(" -\t")]


def _to_prompt_chunks(chunks: list[RetrievedChunk]) -> list[PromptChunk]:
    return [
        PromptChunk(
            document_name=chunk.document_name,
            page_number=chunk.page_number,
            chunk_index=chunk.chunk_index,
            content=chunk.content,
        )
        for chunk in chunks
    ]


def _format_sources_markdown(sources: list[SourceReferenceResponse]) -> str:
    if not sources:
        return "- No project evidence was available."
    return "\n".join(
        (
            f"- {source.document_name}"
            + (f" (page {source.page_number})" if source.page_number is not None else "")
            + f", chunk {source.chunk_index}: {source.excerpt}"
        )
        for source in sources
    )


def _sanitize_filename(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "writing-artifact"


def _artifact_warnings(artifact: WritingArtifact) -> list[str]:
    warnings: list[str] = []
    if artifact.unsupported_claims_json:
        warnings.append(DEFAULT_MANUAL_CONFIRMATION_WARNING)
    if not artifact.sources_json:
        warnings.append("No supporting project evidence was available for this saved result.")
    return warnings


def build_writing_artifact_response(
    artifact: WritingArtifact,
    *,
    warnings: list[str] | None = None,
) -> WritingArtifactResponse:
    source_rows = artifact.sources_json or []
    sources = [SourceReferenceResponse.model_validate(row) for row in source_rows]
    return WritingArtifactResponse(
        id=artifact.id,
        user_id=artifact.user_id,
        project_id=artifact.project_id,
        artifact_type=artifact.artifact_type,  # type: ignore[arg-type]
        title=artifact.title,
        content_markdown=artifact.content_markdown,
        sources=sources,
        warnings=warnings if warnings is not None else _artifact_warnings(artifact),
        unsupported_claims=list(artifact.unsupported_claims_json or []),
        created_at=artifact.created_at,
        updated_at=artifact.updated_at,
    )


def get_owned_writing_artifact(db: Session, *, user_id: str, project_id: str, artifact_id: str) -> WritingArtifact:
    artifact = db.scalar(
        select(WritingArtifact).where(
            WritingArtifact.id == artifact_id,
            WritingArtifact.user_id == user_id,
            WritingArtifact.project_id == project_id,
        )
    )
    if artifact is None:
        raise WritingExecutionError("Writing artifact not found.")
    return artifact


def list_writing_artifacts(db: Session, *, user_id: str, project_id: str) -> list[WritingArtifact]:
    return list(
        db.scalars(
            select(WritingArtifact)
            .where(
                WritingArtifact.user_id == user_id,
                WritingArtifact.project_id == project_id,
            )
            .order_by(WritingArtifact.updated_at.desc(), WritingArtifact.created_at.desc())
        )
    )


class BaseWritingSkill(ABC):
    skill_name: str
    task_type: WritingArtifactType
    heading: str

    @abstractmethod
    def execute(self, context: WritingContext) -> WritingSkillResult:
        raise NotImplementedError

    def _generate_markdown_body(
        self,
        *,
        context: WritingContext,
        chunks: list[RetrievedChunk],
        task_line: str,
    ) -> str:
        gateway = get_llm_gateway()
        try:
            return gateway.generate_answer(
                system_instruction=(
                    "You are Battery-RAG Agent. Produce markdown only. "
                    "Use only the provided project evidence. "
                    "Do not fabricate citations, experiments, or unsupported conclusions. "
                    "Any weak claim must be marked as 'Need manual confirmation'."
                ),
                history_messages=[],
                retrieved_chunks=_to_prompt_chunks(chunks),
                question=(
                    f"{task_line}\n"
                    f"Paper topic: {context.topic}\n"
                    f"Research direction: {context.research_direction or 'Not specified'}\n"
                    f"Writing requirements: {context.requirements or 'Not specified'}\n"
                    "Return markdown headings and concise evidence-grounded paragraphs."
                ),
            )
        except LLMGatewayError as exc:
            raise WritingExecutionError(str(exc)) from exc

    def _insufficient_result(self, *, context: WritingContext, title: str) -> WritingSkillResult:
        unsupported = [context.topic]
        if context.requirements:
            unsupported.extend(_claim_candidates(context.requirements)[:3])
        return WritingSkillResult(
            title=title,
            content_markdown=INSUFFICIENT_INFORMATION_TEXT,
            sources=[],
            warnings=[DEFAULT_MANUAL_CONFIRMATION_WARNING, INSUFFICIENT_INFORMATION_TEXT],
            unsupported_claims=unsupported[:6],
        )

    def _default_result(
        self,
        *,
        context: WritingContext,
        title: str,
        chunks: list[RetrievedChunk],
        task_line: str,
        template_sections: list[str],
        extra_warnings: list[str] | None = None,
        unsupported_claims: list[str] | None = None,
    ) -> WritingSkillResult:
        if not chunks:
            return self._insufficient_result(context=context, title=title)

        body = self._generate_markdown_body(context=context, chunks=chunks, task_line=task_line)
        sources = _dedupe_sources(chunks)
        warnings = list(extra_warnings or [])
        if DEFAULT_MANUAL_CONFIRMATION_WARNING not in warnings:
            warnings.append(DEFAULT_MANUAL_CONFIRMATION_WARNING)

        section_block = "\n".join(f"- {section}" for section in template_sections)
        content_markdown = "\n\n".join(
            [
                f"# {title}",
                f"## Purpose\n{task_line}",
                f"## Suggested Structure\n{section_block}",
                f"## Draft\n{body}",
                f"## Evidence Notes\n{_format_sources_markdown(sources)}",
            ]
        )
        return WritingSkillResult(
            title=title,
            content_markdown=content_markdown,
            sources=sources,
            warnings=warnings,
            unsupported_claims=list(unsupported_claims or []),
        )


class WritingOutlineSkill(BaseWritingSkill):
    skill_name = "writing_outline"
    task_type: WritingArtifactType = "outline"
    heading = "Paper Outline"

    def execute(self, context: WritingContext) -> WritingSkillResult:
        return self._default_result(
            context=context,
            title=f"{self.heading}: {context.topic}",
            chunks=retrieve_project_chunks(
                context.db,
                user_id=context.user_id,
                project_id=context.project_id,
                question=context.query_text,
            ),
            task_line="Create a paper or report outline grounded in the current project evidence.",
            template_sections=["Introduction", "Related Work", "Method", "Experiments", "Conclusion"],
        )


class IntroductionOutlineSkill(BaseWritingSkill):
    skill_name = "introduction_outline"
    task_type: WritingArtifactType = "introduction_outline"
    heading = "Introduction Outline"

    def execute(self, context: WritingContext) -> WritingSkillResult:
        return self._default_result(
            context=context,
            title=f"{self.heading}: {context.topic}",
            chunks=retrieve_project_chunks(
                context.db,
                user_id=context.user_id,
                project_id=context.project_id,
                question=context.query_text,
            ),
            task_line="Draft an introduction-writing framework with background, gap, motivation, and contributions.",
            template_sections=["Background", "Research Gap", "Motivation", "Contributions", "Scope"],
        )


class RelatedWorkDraftSkill(BaseWritingSkill):
    skill_name = "related_work"
    task_type: WritingArtifactType = "related_work"
    heading = "Related Work Draft"

    def execute(self, context: WritingContext) -> WritingSkillResult:
        return self._default_result(
            context=context,
            title=f"{self.heading}: {context.topic}",
            chunks=retrieve_project_chunks(
                context.db,
                user_id=context.user_id,
                project_id=context.project_id,
                question=context.query_text,
            ),
            task_line="Generate a related-work draft that compares themes, methods, and limitations from current project evidence.",
            template_sections=["Theme Overview", "Method Comparison", "Limitations and Gaps", "Positioning"],
        )


class MethodFrameworkSkill(BaseWritingSkill):
    skill_name = "method_framework"
    task_type: WritingArtifactType = "method_framework"
    heading = "Method Framework"

    def execute(self, context: WritingContext) -> WritingSkillResult:
        return self._default_result(
            context=context,
            title=f"{self.heading}: {context.topic}",
            chunks=retrieve_project_chunks(
                context.db,
                user_id=context.user_id,
                project_id=context.project_id,
                question=context.query_text,
            ),
            task_line="Generate a method section framework using only the current project evidence.",
            template_sections=["Problem Definition", "System Inputs", "Method Pipeline", "Algorithm Details", "Evaluation Plan"],
        )


class ConclusionDraftSkill(BaseWritingSkill):
    skill_name = "conclusion"
    task_type: WritingArtifactType = "conclusion"
    heading = "Conclusion Draft"

    def execute(self, context: WritingContext) -> WritingSkillResult:
        return self._default_result(
            context=context,
            title=f"{self.heading}: {context.topic}",
            chunks=retrieve_project_chunks(
                context.db,
                user_id=context.user_id,
                project_id=context.project_id,
                question=context.query_text,
            ),
            task_line="Generate a concise conclusion draft grounded in current project evidence.",
            template_sections=["Main Findings", "Practical Implications", "Limitations", "Next Steps"],
        )


class CitationCheckSkill(BaseWritingSkill):
    skill_name = "citation_check"
    task_type: WritingArtifactType = "citation_check"
    heading = "Citation Check"

    def execute(self, context: WritingContext) -> WritingSkillResult:
        claims = _claim_candidates(context.requirements or context.topic)
        title = f"{self.heading}: {context.topic}"
        if not claims:
            return WritingSkillResult(
                title=title,
                content_markdown=INSUFFICIENT_INFORMATION_TEXT,
                sources=[],
                warnings=["Add one or more concrete claims to check against the current project evidence."],
                unsupported_claims=[context.topic],
            )

        supported_claims: list[str] = []
        unsupported_claims: list[str] = []
        support_chunks: list[RetrievedChunk] = []

        for claim in claims[:6]:
            claim_chunks = retrieve_project_chunks(
                context.db,
                user_id=context.user_id,
                project_id=context.project_id,
                question=claim,
            )
            if claim_chunks and _has_claim_support(claim, claim_chunks):
                supported_claims.append(claim)
                support_chunks.extend(claim_chunks[:2])
            else:
                unsupported_claims.append(claim)

        sources = _dedupe_sources(support_chunks)
        warnings: list[str] = []
        if unsupported_claims:
            warnings.append(DEFAULT_MANUAL_CONFIRMATION_WARNING)
        if not supported_claims and not sources:
            warnings.append(INSUFFICIENT_INFORMATION_TEXT)

        content_markdown = "\n\n".join(
            [
                f"# {title}",
                "## Supported Claims",
                "\n".join(f"- {claim}" for claim in supported_claims) or "- None",
                "## Unsupported Claims",
                "\n".join(f"- {claim}" for claim in unsupported_claims) or "- None",
                "## Evidence Notes",
                _format_sources_markdown(sources),
            ]
        )
        return WritingSkillResult(
            title=title,
            content_markdown=content_markdown,
            sources=sources,
            warnings=warnings,
            unsupported_claims=unsupported_claims,
        )


class MarkdownExportSkill:
    skill_name = "markdown_export"

    def render(self, artifact: WritingArtifactResponse) -> str:
        source_lines = _format_sources_markdown(artifact.sources)
        unsupported_lines = "\n".join(f"- {claim}" for claim in artifact.unsupported_claims) or "- None"
        warning_lines = "\n".join(f"- {warning}" for warning in artifact.warnings) or "- None"
        return "\n\n".join(
            [
                f"# {artifact.title}",
                f"- Artifact type: `{artifact.artifact_type}`\n- Updated at: {format_datetime(artifact.updated_at)}",
                artifact.content_markdown,
                f"## Sources\n{source_lines}",
                f"## Warnings\n{warning_lines}",
                f"## Unsupported Claims\n{unsupported_lines}",
            ]
        )

    def build_filename(self, artifact: WritingArtifactResponse) -> str:
        return f"{_sanitize_filename(artifact.title)}.md"


class WritingSkillsRegistry:
    def __init__(self) -> None:
        self._skills: dict[WritingArtifactType, BaseWritingSkill] = {}

    def register(self, skill: BaseWritingSkill) -> None:
        self._skills[skill.task_type] = skill

    def get(self, task_type: WritingArtifactType) -> BaseWritingSkill | None:
        return self._skills.get(task_type)


class WritingTaskRouter:
    def route(
        self,
        *,
        topic: str,
        research_direction: str | None,
        requirements: str | None,
        requested_task_type: WritingArtifactType | None,
    ) -> WritingRouteDecision:
        if requested_task_type is not None:
            return WritingRouteDecision(task_type=requested_task_type, reason="User explicitly selected the writing task type.")

        normalized = " ".join(
            part.lower()
            for part in (topic, research_direction or "", requirements or "")
            if part.strip()
        )
        if "related work" in normalized or "literature review" in normalized:
            return WritingRouteDecision(task_type="related_work", reason="Detected related-work intent.")
        if "introduction" in normalized:
            return WritingRouteDecision(task_type="introduction_outline", reason="Detected introduction-writing intent.")
        if "method" in normalized:
            return WritingRouteDecision(task_type="method_framework", reason="Detected method-writing intent.")
        if "conclusion" in normalized:
            return WritingRouteDecision(task_type="conclusion", reason="Detected conclusion-writing intent.")
        if "citation" in normalized or "evidence check" in normalized or "support this claim" in normalized:
            return WritingRouteDecision(task_type="citation_check", reason="Detected citation-check intent.")
        if len(normalized) < 12:
            return WritingRouteDecision(
                task_type="outline",
                reason="Prompt was too short for finer routing, defaulting to a safe outline request.",
                clarification="Please add more paper topic detail or choose a specific writing task type.",
            )
        return WritingRouteDecision(task_type="outline", reason="Defaulted to a grounded outline-writing task.")


class WritingExecutor:
    def __init__(self, *, router: WritingTaskRouter, registry: WritingSkillsRegistry) -> None:
        self.router = router
        self.registry = registry

    def run(
        self,
        db: Session,
        *,
        user_id: str,
        project_id: str,
        topic: str,
        research_direction: str | None,
        requirements: str | None,
        requested_task_type: WritingArtifactType | None,
    ) -> tuple[WritingArtifact, list[str]]:
        project = db.scalar(select(Project).where(Project.id == project_id, Project.owner_id == user_id))
        if project is None:
            raise WritingExecutionError("Project not found.")

        cleaned_topic = topic.strip()
        cleaned_direction = research_direction.strip() if research_direction else None
        cleaned_requirements = requirements.strip() if requirements else None
        route = self.router.route(
            topic=cleaned_topic,
            research_direction=cleaned_direction,
            requirements=cleaned_requirements,
            requested_task_type=requested_task_type,
        )

        skill = self.registry.get(route.task_type)
        if skill is None:
            raise WritingExecutionError("Unsupported writing task type.")

        context = WritingContext(
            db=db,
            user_id=user_id,
            project_id=project_id,
            topic=cleaned_topic,
            research_direction=cleaned_direction,
            requirements=cleaned_requirements,
            task_type=route.task_type,
            route_reason=route.reason,
        )
        result = skill.execute(context)
        warnings = list(result.warnings)
        if route.clarification:
            warnings.append(route.clarification)

        artifact = WritingArtifact(
            user_id=user_id,
            project_id=project_id,
            artifact_type=route.task_type,
            title=result.title,
            content_markdown=result.content_markdown,
            sources_json=[source.model_dump(mode="json") for source in result.sources],
            unsupported_claims_json=list(result.unsupported_claims),
        )
        db.add(artifact)
        db.commit()
        db.refresh(artifact)
        return artifact, warnings


def get_writing_executor() -> WritingExecutor:
    registry = WritingSkillsRegistry()
    registry.register(WritingOutlineSkill())
    registry.register(IntroductionOutlineSkill())
    registry.register(RelatedWorkDraftSkill())
    registry.register(MethodFrameworkSkill())
    registry.register(ConclusionDraftSkill())
    registry.register(CitationCheckSkill())
    return WritingExecutor(router=WritingTaskRouter(), registry=registry)
