from __future__ import annotations

import re
from abc import ABC, abstractmethod
from collections import Counter
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.agent_task import AgentTask, AgentTaskStatus
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.models.project import Project
from app.schemas.agent import AgentResultPayload, AgentResultSection, AgentTaskType
from app.schemas.chat import SourceReferenceResponse
from app.schemas.external_reference import ExternalReferenceContextResponse
from app.services.external_references import (
    build_external_reference_context,
    build_external_reference_context_response,
    build_external_reference_warning_summary,
    list_saved_external_references,
)
from app.services.llm_gateway import LLMGatewayError, PromptChunk, get_llm_gateway
from app.services.rag import INSUFFICIENT_INFORMATION_TEXT, RetrievedChunk, retrieve_project_chunks


SUPPORTED_AGENT_TASK_TYPES: tuple[AgentTaskType, ...] = (
    "research_qa",
    "paper_summary",
    "multi_paper_compare",
    "literature_review",
    "writing_outline",
    "evidence_check",
)

DEFAULT_MANUAL_CONFIRMATION_WARNING = "Need manual confirmation because the current project evidence is limited."


class AgentExecutionError(Exception):
    pass


class SkillExecutionError(Exception):
    pass


@dataclass(frozen=True)
class RouteDecision:
    task_type: AgentTaskType
    confidence: float
    reason: str
    clarification: str | None = None


@dataclass(frozen=True)
class SkillContext:
    db: Session
    user_id: str
    project_id: str
    user_input: str
    routed_task_type: AgentTaskType
    route_confidence: float
    route_reason: str


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


def _dominant_documents(chunks: list[RetrievedChunk], *, limit: int) -> list[str]:
    counts = Counter(chunk.document_name for chunk in chunks)
    ranked = counts.most_common(limit)
    return [name for name, _ in ranked]


def _sanitize_error_message(message: str) -> str:
    settings = get_settings()
    sanitized = message.replace(str(settings.storage_root), "[storage_root]")
    sanitized = re.sub(r"[A-Za-z]:\\[^\"'\r\n]+", "[path]", sanitized)
    return sanitized[:2000]


def _claim_candidates(text: str) -> list[str]:
    raw_parts = re.split(r"[\r\n]+|(?<=[.!?。！？])\s+", text.strip())
    return [part.strip(" -\t") for part in raw_parts if part.strip(" -\t")]


def _chunks_to_prompt(chunks: list[RetrievedChunk]) -> list[PromptChunk]:
    return [
        PromptChunk(
            document_name=chunk.document_name,
            page_number=chunk.page_number,
            chunk_index=chunk.chunk_index,
            content=chunk.content,
        )
        for chunk in chunks
    ]


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


def _llm_grounded_answer(system_instruction: str, user_input: str, chunks: list[RetrievedChunk]) -> str:
    if not chunks:
        return INSUFFICIENT_INFORMATION_TEXT

    gateway = get_llm_gateway()
    try:
        return gateway.generate_answer(
            system_instruction=system_instruction,
            history_messages=[],
            retrieved_chunks=_chunks_to_prompt(chunks),
            question=user_input,
        )
    except LLMGatewayError as exc:
        raise SkillExecutionError(str(exc)) from exc


def _load_external_reference_context(context: SkillContext, *, limit: int = 4) -> tuple[list[ExternalReferenceContextResponse], list[str], str]:
    references = list_saved_external_references(
        context.db,
        user_id=context.user_id,
        project_id=context.project_id,
        limit=limit,
    )
    payload = [ExternalReferenceContextResponse.model_validate(build_external_reference_context_response(reference)) for reference in references]
    warnings = build_external_reference_warning_summary(references)
    context_text = "\n\n".join(build_external_reference_context(reference) for reference in references)
    return payload, warnings, context_text


class BaseSkill(ABC):
    skill_name: str
    task_type: AgentTaskType

    @abstractmethod
    def execute(self, context: SkillContext) -> AgentResultPayload:
        raise NotImplementedError

    def _insufficient_payload(
        self,
        *,
        context: SkillContext,
        warnings: list[str] | None = None,
        clarification: str | None = None,
    ) -> AgentResultPayload:
        warning_list = list(warnings or [])
        if DEFAULT_MANUAL_CONFIRMATION_WARNING not in warning_list:
            warning_list.append(DEFAULT_MANUAL_CONFIRMATION_WARNING)
        return AgentResultPayload(
            routed_task_type=context.routed_task_type,
            route_confidence=context.route_confidence,
            route_reason=context.route_reason,
            answer=INSUFFICIENT_INFORMATION_TEXT,
            result=INSUFFICIENT_INFORMATION_TEXT,
            warnings=warning_list,
            clarification=clarification,
        )


class RetrievalSkill:
    skill_name = "retrieval"

    def execute(self, context: SkillContext) -> list[RetrievedChunk]:
        chunks = retrieve_project_chunks(
            context.db,
            user_id=context.user_id,
            project_id=context.project_id,
            question=context.user_input,
        )
        if chunks:
            return chunks
        return self._fallback_keyword_retrieval(context)

    def _fallback_keyword_retrieval(self, context: SkillContext) -> list[RetrievedChunk]:
        terms = _search_terms(context.user_input)
        if not terms:
            return []
        required_overlap = 1 if len(terms) == 1 else 2

        chunk_rows = list(
            context.db.scalars(
                select(DocumentChunk)
                .where(
                    DocumentChunk.user_id == context.user_id,
                    DocumentChunk.project_id == context.project_id,
                )
                .order_by(DocumentChunk.document_id.asc(), DocumentChunk.chunk_index.asc())
            )
        )
        if not chunk_rows:
            return []

        document_ids = {chunk.document_id for chunk in chunk_rows}
        documents = list(
            context.db.scalars(
                select(Document).where(
                    Document.user_id == context.user_id,
                    Document.project_id == context.project_id,
                    Document.id.in_(document_ids),
                )
            )
        )
        document_by_id = {document.id: document for document in documents}

        scored_chunks: list[tuple[int, RetrievedChunk]] = []
        for chunk in chunk_rows:
            lowered = chunk.content.lower()
            overlap = sum(1 for term in terms if term in lowered)
            if overlap < required_overlap:
                continue
            document = document_by_id.get(chunk.document_id)
            if document is None:
                continue
            scored_chunks.append(
                (
                    overlap,
                    RetrievedChunk(
                        document_id=document.id,
                        document_name=document.original_filename,
                        page_number=chunk.page_number,
                        chunk_id=chunk.id,
                        chunk_index=chunk.chunk_index,
                        content=chunk.content,
                        excerpt=chunk.content[:280].strip(),
                        score=float(overlap),
                    ),
                )
            )

        scored_chunks.sort(key=lambda item: (item[0], item[1].chunk_index), reverse=True)
        return [chunk for _, chunk in scored_chunks[: get_settings().rag_top_k]]


class ResearchQASkill(BaseSkill):
    skill_name = "research_qa"
    task_type: AgentTaskType = "research_qa"

    def __init__(self, retrieval_skill: RetrievalSkill) -> None:
        self.retrieval_skill = retrieval_skill

    def execute(self, context: SkillContext) -> AgentResultPayload:
        chunks = self.retrieval_skill.execute(context)
        if not chunks:
            return self._insufficient_payload(context=context)

        answer = _llm_grounded_answer(
            (
                "You are Battery-RAG Agent. Answer the user using only the provided project evidence. "
                "Do not fabricate facts. If the evidence is weak, say so and ask for manual confirmation."
            ),
            context.user_input,
            chunks,
        )
        return AgentResultPayload(
            routed_task_type=context.routed_task_type,
            route_confidence=context.route_confidence,
            route_reason=context.route_reason,
            answer=answer,
            result=answer,
            document_scope=_dominant_documents(chunks, limit=3),
            sources=_dedupe_sources(chunks),
            warnings=[] if answer != INSUFFICIENT_INFORMATION_TEXT else [DEFAULT_MANUAL_CONFIRMATION_WARNING],
        )


class PaperSummarySkill(BaseSkill):
    skill_name = "paper_summary"
    task_type: AgentTaskType = "paper_summary"

    def __init__(self, retrieval_skill: RetrievalSkill) -> None:
        self.retrieval_skill = retrieval_skill

    def execute(self, context: SkillContext) -> AgentResultPayload:
        chunks = self.retrieval_skill.execute(context)
        if not chunks:
            return self._insufficient_payload(
                context=context,
                warnings=["No document evidence matched the requested paper summary."],
            )

        dominant_documents = _dominant_documents(chunks, limit=1)
        scoped_chunks = [chunk for chunk in chunks if chunk.document_name in dominant_documents] or chunks
        summary = _llm_grounded_answer(
            (
                "Summarize one project document using only the provided evidence. "
                "Cover topic, method, findings, and limitations only when supported by the evidence."
            ),
            f"Summarize the most relevant document for this request: {context.user_input}",
            scoped_chunks,
        )
        warnings: list[str] = []
        if len({chunk.document_name for chunk in chunks}) > 1:
            warnings.append("Document scope was inferred from the strongest retrieved evidence in the current project.")

        return AgentResultPayload(
            routed_task_type=context.routed_task_type,
            route_confidence=context.route_confidence,
            route_reason=context.route_reason,
            answer=summary,
            result=summary,
            sections=[
                AgentResultSection(title="Summary", content=summary),
                AgentResultSection(
                    title="Document Scope",
                    content=", ".join(dominant_documents) if dominant_documents else "Most relevant project document",
                ),
            ],
            document_scope=dominant_documents,
            sources=_dedupe_sources(scoped_chunks),
            warnings=warnings,
        )


class MultiPaperCompareSkill(BaseSkill):
    skill_name = "multi_paper_compare"
    task_type: AgentTaskType = "multi_paper_compare"

    def __init__(self, retrieval_skill: RetrievalSkill) -> None:
        self.retrieval_skill = retrieval_skill
        self.settings = get_settings()

    def execute(self, context: SkillContext) -> AgentResultPayload:
        chunks = self.retrieval_skill.execute(context)
        if not chunks:
            return self._insufficient_payload(
                context=context,
                warnings=["No project evidence matched the requested comparison."],
            )

        dominant_documents = _dominant_documents(chunks, limit=self.settings.agent_max_comparison_documents)
        if len(dominant_documents) < 2:
            return self._insufficient_payload(
                context=context,
                warnings=["At least two distinct project documents are needed for a grounded multi-paper comparison."],
            )

        scoped_chunks = [chunk for chunk in chunks if chunk.document_name in dominant_documents]
        comparison = _llm_grounded_answer(
            (
                "Compare multiple project documents using only the provided evidence. "
                "Highlight methods, models, constraints, and results when the evidence supports them."
            ),
            f"Compare these project documents for the user request: {context.user_input}",
            scoped_chunks,
        )
        return AgentResultPayload(
            routed_task_type=context.routed_task_type,
            route_confidence=context.route_confidence,
            route_reason=context.route_reason,
            answer=comparison,
            result=comparison,
            sections=[
                AgentResultSection(title="Compared Documents", content=", ".join(dominant_documents)),
                AgentResultSection(title="Comparison", content=comparison),
            ],
            document_scope=dominant_documents,
            sources=_dedupe_sources(scoped_chunks),
            warnings=[],
        )


class LiteratureReviewSkill(BaseSkill):
    skill_name = "literature_review"
    task_type: AgentTaskType = "literature_review"

    def __init__(self, retrieval_skill: RetrievalSkill) -> None:
        self.retrieval_skill = retrieval_skill

    def execute(self, context: SkillContext) -> AgentResultPayload:
        chunks = self.retrieval_skill.execute(context)
        external_references, external_warnings, external_context = _load_external_reference_context(context)
        if not chunks and not external_references:
            return self._insufficient_payload(
                context=context,
                warnings=["No project evidence matched the requested literature review topic."],
            )

        if chunks:
            review = _llm_grounded_answer(
                (
                    "Create a bounded literature review structure using only the provided project evidence. "
                    "Prefer themes, gaps, and technical directions that can be justified from the evidence. "
                    "Any external references included in the user prompt are metadata-only context and must be labeled as external references."
                ),
                (
                    f"Create a literature review structure for: {context.user_input}\n\n"
                    f"Saved external reference context (metadata only, not internal evidence):\n{external_context or 'None'}"
                ),
                chunks,
            )
        else:
            review = (
                "Current project evidence is insufficient for a grounded literature review answer. "
                "Saved external references are listed below as metadata-only leads that require manual confirmation."
            )

        sections = [AgentResultSection(title="Review Structure", content=review)]
        if external_references:
            external_lines = []
            for reference in external_references:
                external_lines.append(
                    f"- {reference.title} | {reference.source} | DOI: {reference.doi or 'Unavailable'} | URL: {reference.url or 'Unavailable'}"
                )
            sections.append(
                AgentResultSection(
                    title="External References",
                    content="\n".join(external_lines),
                )
            )

        warnings = [DEFAULT_MANUAL_CONFIRMATION_WARNING]
        warnings.extend(external_warnings)
        if external_references:
            warnings.append("External references are metadata only and never replace uploaded-document evidence.")
        return AgentResultPayload(
            routed_task_type=context.routed_task_type,
            route_confidence=context.route_confidence,
            route_reason=context.route_reason,
            answer=review,
            result=review,
            sections=sections,
            document_scope=_dominant_documents(chunks, limit=3),
            sources=_dedupe_sources(chunks),
            external_references=external_references,
            warnings=list(dict.fromkeys(warnings)),
        )


class OutlineSkill(BaseSkill):
    skill_name = "writing_outline"
    task_type: AgentTaskType = "writing_outline"

    def __init__(self, retrieval_skill: RetrievalSkill) -> None:
        self.retrieval_skill = retrieval_skill

    def execute(self, context: SkillContext) -> AgentResultPayload:
        chunks = self.retrieval_skill.execute(context)
        if not chunks:
            return self._insufficient_payload(
                context=context,
                warnings=["No project evidence matched the requested outline topic."],
            )

        outline = _llm_grounded_answer(
            (
                "Produce a concise outline for a paper or technical report using only the provided project evidence. "
                "Do not write the paper itself, and mark weak evidence as needing manual confirmation."
            ),
            f"Create a writing outline for: {context.user_input}",
            chunks,
        )
        outline_sections = [
            AgentResultSection(title=f"Outline Part {index + 1}", content=line.strip("- ").strip())
            for index, line in enumerate(outline.splitlines())
            if line.strip()
        ]
        if not outline_sections:
            outline_sections = [AgentResultSection(title="Outline", content=outline)]

        return AgentResultPayload(
            routed_task_type=context.routed_task_type,
            route_confidence=context.route_confidence,
            route_reason=context.route_reason,
            answer=outline,
            result=outline,
            sections=outline_sections,
            document_scope=_dominant_documents(chunks, limit=3),
            sources=_dedupe_sources(chunks),
            warnings=[DEFAULT_MANUAL_CONFIRMATION_WARNING],
        )


class EvidenceCheckSkill(BaseSkill):
    skill_name = "evidence_check"
    task_type: AgentTaskType = "evidence_check"

    def __init__(self, retrieval_skill: RetrievalSkill) -> None:
        self.retrieval_skill = retrieval_skill
        self.settings = get_settings()

    def execute(self, context: SkillContext) -> AgentResultPayload:
        claims = _claim_candidates(context.user_input)
        if not claims:
            return self._insufficient_payload(
                context=context,
                warnings=["Provide one or more concrete claims to check against the current project evidence."],
                clarification="Add specific claims or bullet points that you want the system to verify.",
            )

        supported_claims: list[str] = []
        unsupported_claims: list[str] = []
        supporting_chunks: list[RetrievedChunk] = []
        warnings: list[str] = []

        limited_claims = claims[: self.settings.agent_max_claims]
        if len(claims) > len(limited_claims):
            warnings.append(f"Only the first {self.settings.agent_max_claims} claims were checked in this run.")

        for claim in limited_claims:
            claim_context = SkillContext(
                db=context.db,
                user_id=context.user_id,
                project_id=context.project_id,
                user_input=claim,
                routed_task_type=context.routed_task_type,
                route_confidence=context.route_confidence,
                route_reason=context.route_reason,
            )
            claim_chunks = self.retrieval_skill.execute(claim_context)
            if claim_chunks and _has_claim_support(claim, claim_chunks):
                supported_claims.append(claim)
                supporting_chunks.extend(claim_chunks[:2])
            else:
                unsupported_claims.append(claim)

        if not supported_claims and not unsupported_claims:
            return self._insufficient_payload(context=context)

        result_lines = [
            f"Supported claims: {len(supported_claims)}",
            f"Unsupported claims: {len(unsupported_claims)}",
        ]
        if unsupported_claims:
            warnings.append(DEFAULT_MANUAL_CONFIRMATION_WARNING)

        sections: list[AgentResultSection] = []
        if supported_claims:
            sections.append(
                AgentResultSection(title="Supported Claims", content="\n".join(f"- {claim}" for claim in supported_claims))
            )
        if unsupported_claims:
            sections.append(
                AgentResultSection(
                    title="Unsupported Claims",
                    content="\n".join(f"- {claim}" for claim in unsupported_claims),
                )
            )

        return AgentResultPayload(
            routed_task_type=context.routed_task_type,
            route_confidence=context.route_confidence,
            route_reason=context.route_reason,
            result="\n".join(result_lines),
            sections=sections,
            document_scope=_dominant_documents(supporting_chunks, limit=3),
            sources=_dedupe_sources(supporting_chunks),
            warnings=warnings,
            supported_claims=supported_claims,
            unsupported_claims=unsupported_claims,
        )


class SkillsRegistry:
    def __init__(self) -> None:
        self._skills: dict[AgentTaskType, BaseSkill] = {}

    def register(self, skill: BaseSkill) -> None:
        self._skills[skill.task_type] = skill

    def get(self, task_type: AgentTaskType) -> BaseSkill | None:
        return self._skills.get(task_type)

    def supported_task_types(self) -> tuple[AgentTaskType, ...]:
        return tuple(self._skills.keys())


class TaskRouterAgent:
    def __init__(self) -> None:
        self.settings = get_settings()

    def route(self, *, user_input: str, requested_task_type: AgentTaskType | None = None) -> RouteDecision:
        normalized = " ".join(user_input.lower().split())
        if requested_task_type is not None:
            return RouteDecision(
                task_type=requested_task_type,
                confidence=1.0,
                reason="User explicitly selected the task type.",
            )

        if len(normalized) < self.settings.agent_min_prompt_characters:
            return RouteDecision(
                task_type="research_qa",
                confidence=0.32,
                reason="Prompt was too short for reliable task routing.",
                clarification="Please add more detail about the research objective, target documents, or expected output.",
            )

        if any(keyword in normalized for keyword in ("evidence check", "fact check", "verify", "support this claim", "证据核查", "核查", "验证论断")):
            return RouteDecision(task_type="evidence_check", confidence=0.92, reason="Detected explicit evidence-check intent.")

        if any(keyword in normalized for keyword in ("compare", "comparison", "versus", " vs ", "对比", "比较")):
            return RouteDecision(task_type="multi_paper_compare", confidence=0.88, reason="Detected multi-document comparison intent.")

        if any(keyword in normalized for keyword in ("literature review", "survey", "related work", "综述", "文献综述", "技术路线")):
            return RouteDecision(task_type="literature_review", confidence=0.9, reason="Detected literature review intent.")

        if any(keyword in normalized for keyword in ("outline", "提纲", "大纲", "structure a paper", "report structure")):
            return RouteDecision(task_type="writing_outline", confidence=0.9, reason="Detected writing-outline intent.")

        if any(keyword in normalized for keyword in ("summarize", "summary", "paper summary", "总结", "概述", "摘要")):
            return RouteDecision(task_type="paper_summary", confidence=0.84, reason="Detected paper-summary intent.")

        if any(keyword in normalized for keyword in ("write the full paper", "代写", "ghostwrite")):
            return RouteDecision(
                task_type="writing_outline",
                confidence=0.72,
                reason="Full paper drafting is out of scope, so the request was narrowed to a grounded outline.",
            )

        llm_routed = self._route_with_optional_llm(normalized)
        if llm_routed is not None:
            return llm_routed

        if len(normalized.split()) <= 4:
            return RouteDecision(
                task_type="research_qa",
                confidence=0.42,
                reason="The request was ambiguous, so it is safer to ask for clarification first.",
                clarification="Please clarify whether you want a question answered, a summary, a comparison, a review, an outline, or an evidence check.",
            )

        return RouteDecision(
            task_type="research_qa",
            confidence=0.7,
            reason="Defaulted to bounded project question answering.",
        )

    def _route_with_optional_llm(self, normalized_input: str) -> RouteDecision | None:
        if not self.settings.agent_enable_llm_routing or self.settings.llm_provider == "mock":
            return None

        gateway = get_llm_gateway()
        try:
            raw_label = gateway.complete_text(
                system_instruction=(
                    "Classify the request into exactly one label from: "
                    "research_qa, paper_summary, multi_paper_compare, literature_review, writing_outline, evidence_check, needs_clarification. "
                    "Return only the label."
                ),
                user_prompt=normalized_input,
            ).strip().lower()
        except LLMGatewayError:
            return None

        if raw_label == "needs_clarification":
            return RouteDecision(
                task_type="research_qa",
                confidence=0.35,
                reason="LLM-assisted routing reported low confidence.",
                clarification="Please clarify the desired research output so the system can route the task safely.",
            )

        if raw_label in SUPPORTED_AGENT_TASK_TYPES:
            return RouteDecision(
                task_type=raw_label,
                confidence=0.66,
                reason="Used optional backend-only LLM assistance for task routing.",
            )
        return None


class AgentExecutor:
    def __init__(self, *, router: TaskRouterAgent, registry: SkillsRegistry) -> None:
        self.router = router
        self.registry = registry

    def run(
        self,
        db: Session,
        *,
        user_id: str,
        project_id: str,
        user_input: str,
        requested_task_type: AgentTaskType | None,
    ) -> AgentTask:
        project = db.scalar(select(Project).where(Project.id == project_id, Project.owner_id == user_id))
        if project is None:
            raise AgentExecutionError("Project not found.")

        cleaned_input = user_input.strip()
        route = self.router.route(user_input=cleaned_input, requested_task_type=requested_task_type)
        task = AgentTask(
            user_id=user_id,
            project_id=project_id,
            task_type=route.task_type,
            user_input=cleaned_input,
            status=AgentTaskStatus.QUEUED.value,
            result_json=None,
            error_message=None,
        )
        db.add(task)
        db.commit()
        db.refresh(task)

        if route.clarification:
            task.status = AgentTaskStatus.NEEDS_CLARIFICATION.value
            task.result_json = AgentResultPayload(
                routed_task_type=route.task_type,
                route_confidence=route.confidence,
                route_reason=route.reason,
                answer=INSUFFICIENT_INFORMATION_TEXT,
                result=INSUFFICIENT_INFORMATION_TEXT,
                warnings=[DEFAULT_MANUAL_CONFIRMATION_WARNING],
                clarification=route.clarification,
            ).model_dump(mode="json")
            db.add(task)
            db.commit()
            db.refresh(task)
            return task

        task.status = AgentTaskStatus.RUNNING.value
        db.add(task)
        db.commit()

        skill = self.registry.get(route.task_type)
        if skill is None:
            task.status = AgentTaskStatus.FAILED.value
            task.error_message = "Unsupported agent task type."
            db.add(task)
            db.commit()
            db.refresh(task)
            return task

        context = SkillContext(
            db=db,
            user_id=user_id,
            project_id=project_id,
            user_input=cleaned_input,
            routed_task_type=route.task_type,
            route_confidence=route.confidence,
            route_reason=route.reason,
        )

        try:
            result = skill.execute(context)
        except (SkillExecutionError, AgentExecutionError) as exc:
            task.status = AgentTaskStatus.FAILED.value
            task.error_message = _sanitize_error_message(str(exc) or "Agent task execution failed.")
            db.add(task)
            db.commit()
            db.refresh(task)
            return task
        except Exception:
            task.status = AgentTaskStatus.FAILED.value
            task.error_message = "Agent task execution failed."
            db.add(task)
            db.commit()
            db.refresh(task)
            return task

        task.status = AgentTaskStatus.COMPLETED.value
        task.result_json = result.model_dump(mode="json")
        task.error_message = None
        db.add(task)
        db.commit()
        db.refresh(task)
        return task


def get_agent_executor() -> AgentExecutor:
    retrieval_skill = RetrievalSkill()
    registry = SkillsRegistry()
    registry.register(ResearchQASkill(retrieval_skill))
    registry.register(PaperSummarySkill(retrieval_skill))
    registry.register(MultiPaperCompareSkill(retrieval_skill))
    registry.register(LiteratureReviewSkill(retrieval_skill))
    registry.register(OutlineSkill(retrieval_skill))
    registry.register(EvidenceCheckSkill(retrieval_skill))
    return AgentExecutor(router=TaskRouterAgent(), registry=registry)
