from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.core.config import get_settings
from app.models.chat_message import ChatMessage
from app.models.chat_session import ChatSession
from app.models.document import Document, DocumentStatus, EmbeddingStatus
from app.models.document_chunk import DocumentChunk
from app.schemas.project import KnowledgeBaseStatusResponse
from app.services.llm_gateway import LLMGatewayError, PromptChunk, get_llm_gateway
from app.services.vector_store import VectorPoint, VectorSearchResult, VectorStoreError, get_vector_store


INSUFFICIENT_INFORMATION_TEXT = "当前知识库中没有足够信息"
RAG_SYSTEM_INSTRUCTION = (
    "You are Battery-RAG Agent. Answer only from the provided project evidence. "
    "Do not invent facts. If the retrieved evidence is insufficient, answer exactly with "
    f"'{INSUFFICIENT_INFORMATION_TEXT}'."
)


class KnowledgeBaseError(Exception):
    pass


class ChatSessionError(Exception):
    pass


@dataclass(frozen=True)
class RetrievedChunk:
    document_id: str
    document_name: str
    page_number: int | None
    chunk_id: str
    chunk_index: int
    content: str
    excerpt: str
    score: float

    def to_source_reference(self) -> dict[str, object]:
        return {
            "document_id": self.document_id,
            "document_name": self.document_name,
            "page_number": self.page_number,
            "chunk_id": self.chunk_id,
            "chunk_index": self.chunk_index,
            "excerpt": self.excerpt,
        }


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _trim_excerpt(text: str, *, limit: int = 280) -> str:
    normalized = " ".join(text.split())
    if len(normalized) <= limit:
        return normalized
    return f"{normalized[: limit - 3].rstrip()}..."


def summarize_knowledge_base_status(db: Session, *, user_id: str, project_id: str) -> KnowledgeBaseStatusResponse:
    documents = list(
        db.scalars(
            select(Document)
            .where(Document.user_id == user_id, Document.project_id == project_id)
            .order_by(Document.created_at.desc())
        )
    )
    total_chunks = int(
        db.scalar(
            select(func.count(DocumentChunk.id)).where(
                DocumentChunk.user_id == user_id,
                DocumentChunk.project_id == project_id,
            )
        )
        or 0
    )

    processed_documents = [document for document in documents if document.status == DocumentStatus.PROCESSED.value]
    embedded_documents = [document for document in processed_documents if document.embedding_status == EmbeddingStatus.INDEXED.value]
    indexed_chunks = sum(document.chunk_count for document in embedded_documents)
    last_embedded_at = max((document.embedded_at for document in embedded_documents if document.embedded_at is not None), default=None)
    needs_rebuild = any(document.embedding_status != EmbeddingStatus.INDEXED.value for document in processed_documents)

    return KnowledgeBaseStatusResponse(
        total_documents=len(documents),
        processed_documents=len(processed_documents),
        embedded_documents=len(embedded_documents),
        total_chunks=total_chunks,
        indexed_chunks=indexed_chunks,
        can_chat=indexed_chunks > 0,
        needs_rebuild=needs_rebuild,
        last_embedded_at=last_embedded_at,
    )


def build_project_knowledge_base(db: Session, *, user_id: str, project_id: str) -> KnowledgeBaseStatusResponse:
    documents = list(
        db.scalars(
            select(Document)
            .where(Document.user_id == user_id, Document.project_id == project_id)
            .order_by(Document.created_at.asc())
        )
    )
    processed_documents = [document for document in documents if document.status == DocumentStatus.PROCESSED.value]
    if not processed_documents:
        raise KnowledgeBaseError("No processed project documents are available for vector build.")

    chunks = list(
        db.scalars(
            select(DocumentChunk)
            .where(DocumentChunk.user_id == user_id, DocumentChunk.project_id == project_id)
            .order_by(DocumentChunk.document_id.asc(), DocumentChunk.chunk_index.asc())
        )
    )
    if not chunks:
        raise KnowledgeBaseError("No processed project chunks are available for vector build.")

    for document in processed_documents:
        document.embedding_status = EmbeddingStatus.INDEXING.value
        document.embedded_at = None
        db.add(document)
    db.commit()

    llm_gateway = get_llm_gateway()
    vector_store = get_vector_store()

    try:
        embeddings = llm_gateway.embed_texts([chunk.content for chunk in chunks])
        points = [
            VectorPoint(
                id=chunk.id,
                vector=embedding,
                payload={
                    "user_id": chunk.user_id,
                    "project_id": chunk.project_id,
                    "document_id": chunk.document_id,
                    "chunk_id": chunk.id,
                    "page_number": chunk.page_number,
                    "chunk_index": chunk.chunk_index,
                },
            )
            for chunk, embedding in zip(chunks, embeddings, strict=True)
        ]
        vector_store.replace_project_vectors(user_id=user_id, project_id=project_id, points=points)
    except (LLMGatewayError, VectorStoreError) as exc:
        db.rollback()
        for document in processed_documents:
            document.embedding_status = EmbeddingStatus.FAILED.value
            document.embedded_at = None
            db.add(document)
        db.commit()
        raise KnowledgeBaseError(str(exc)) from exc

    chunk_document_ids = {chunk.document_id for chunk in chunks}
    embedded_at = _utc_now()
    for document in documents:
        if document.id in chunk_document_ids and document.status == DocumentStatus.PROCESSED.value:
            document.embedding_status = EmbeddingStatus.INDEXED.value
            document.embedded_at = embedded_at
        else:
            document.embedding_status = EmbeddingStatus.NOT_INDEXED.value
            document.embedded_at = None
        db.add(document)
    db.commit()

    return summarize_knowledge_base_status(db, user_id=user_id, project_id=project_id)


def get_owned_chat_session(db: Session, *, user_id: str, project_id: str, session_id: str) -> ChatSession:
    session = db.scalar(
        select(ChatSession)
        .where(
            ChatSession.id == session_id,
            ChatSession.user_id == user_id,
            ChatSession.project_id == project_id,
        )
        .options(selectinload(ChatSession.messages))
    )
    if session is None:
        raise ChatSessionError("Chat session not found.")
    return session


def list_project_chat_sessions(db: Session, *, user_id: str, project_id: str) -> list[ChatSession]:
    return list(
        db.scalars(
            select(ChatSession)
            .where(ChatSession.user_id == user_id, ChatSession.project_id == project_id)
            .order_by(ChatSession.updated_at.desc(), ChatSession.created_at.desc())
        )
    )


def create_chat_session(db: Session, *, user_id: str, project_id: str, title: str | None) -> ChatSession:
    session = ChatSession(
        user_id=user_id,
        project_id=project_id,
        title=(title or "New chat").strip()[:255] or "New chat",
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def delete_chat_session(db: Session, *, user_id: str, project_id: str, session_id: str) -> None:
    session = get_owned_chat_session(db, user_id=user_id, project_id=project_id, session_id=session_id)
    db.delete(session)
    db.commit()


def load_recent_session_history(
    db: Session,
    *,
    user_id: str,
    project_id: str,
    session_id: str,
) -> list[tuple[str, str]]:
    limit = get_settings().chat_history_limit
    messages = list(
        db.scalars(
            select(ChatMessage)
            .where(
                ChatMessage.user_id == user_id,
                ChatMessage.project_id == project_id,
                ChatMessage.session_id == session_id,
            )
            .order_by(ChatMessage.created_at.desc())
            .limit(limit)
        )
    )
    messages.reverse()
    return [(message.role, message.content) for message in messages]


def save_user_message(
    db: Session,
    *,
    user_id: str,
    project_id: str,
    session: ChatSession,
    question: str,
) -> ChatMessage:
    message = ChatMessage(
        user_id=user_id,
        project_id=project_id,
        session_id=session.id,
        role="user",
        content=question.strip(),
        sources_json=None,
    )
    session.updated_at = _utc_now()
    db.add(message)
    db.add(session)
    db.commit()
    db.refresh(message)
    return message


def save_assistant_message(
    db: Session,
    *,
    user_id: str,
    project_id: str,
    session: ChatSession,
    content: str,
    sources: list[dict[str, object]],
) -> ChatMessage:
    message = ChatMessage(
        user_id=user_id,
        project_id=project_id,
        session_id=session.id,
        role="assistant",
        content=content,
        sources_json=sources,
    )
    session.updated_at = _utc_now()
    db.add(message)
    db.add(session)
    db.commit()
    db.refresh(message)
    return message


def retrieve_project_chunks(
    db: Session,
    *,
    user_id: str,
    project_id: str,
    question: str,
) -> list[RetrievedChunk]:
    settings = get_settings()
    llm_gateway = get_llm_gateway()
    vector_store = get_vector_store()

    try:
        question_embedding = llm_gateway.embed_texts([question.strip()])[0]
        search_results = vector_store.search(
            vector=question_embedding,
            user_id=user_id,
            project_id=project_id,
            limit=settings.rag_top_k,
            score_threshold=settings.rag_min_similarity,
        )
    except (LLMGatewayError, VectorStoreError) as exc:
        raise KnowledgeBaseError(str(exc)) from exc

    if not search_results:
        return []

    chunk_ids = [str(result.payload.get("chunk_id") or result.id) for result in search_results]
    chunks = list(
        db.scalars(
            select(DocumentChunk)
            .where(
                DocumentChunk.user_id == user_id,
                DocumentChunk.project_id == project_id,
                DocumentChunk.id.in_(chunk_ids),
            )
        )
    )
    if not chunks:
        return []

    documents = list(
        db.scalars(
            select(Document).where(
                Document.user_id == user_id,
                Document.project_id == project_id,
                Document.id.in_({chunk.document_id for chunk in chunks}),
            )
        )
    )
    chunk_by_id = {chunk.id: chunk for chunk in chunks}
    document_by_id = {document.id: document for document in documents}

    results_by_chunk_id: dict[str, VectorSearchResult] = {
        str(result.payload.get("chunk_id") or result.id): result for result in search_results
    }
    retrieved: list[RetrievedChunk] = []
    for chunk_id in chunk_ids:
        chunk = chunk_by_id.get(chunk_id)
        if chunk is None:
            continue
        document = document_by_id.get(chunk.document_id)
        if document is None:
            continue
        result = results_by_chunk_id.get(chunk_id)
        if result is None:
            continue
        retrieved.append(
            RetrievedChunk(
                document_id=document.id,
                document_name=document.original_filename,
                page_number=chunk.page_number,
                chunk_id=chunk.id,
                chunk_index=chunk.chunk_index,
                content=chunk.content,
                excerpt=_trim_excerpt(chunk.content),
                score=result.score,
            )
        )
    return retrieved


def build_assistant_answer(
    *,
    history_messages: list[tuple[str, str]],
    retrieved_chunks: list[RetrievedChunk],
    question: str,
) -> str:
    if not retrieved_chunks:
        return INSUFFICIENT_INFORMATION_TEXT

    llm_gateway = get_llm_gateway()
    prompt_chunks = [
        PromptChunk(
            document_name=chunk.document_name,
            page_number=chunk.page_number,
            chunk_index=chunk.chunk_index,
            content=chunk.content,
        )
        for chunk in retrieved_chunks
    ]
    try:
        return llm_gateway.generate_answer(
            system_instruction=RAG_SYSTEM_INSTRUCTION,
            history_messages=history_messages,
            retrieved_chunks=prompt_chunks,
            question=question.strip(),
        )
    except LLMGatewayError as exc:
        raise KnowledgeBaseError(str(exc)) from exc


def stream_answer_chunks(answer: str) -> list[str]:
    return get_llm_gateway().stream_text_chunks(answer)
