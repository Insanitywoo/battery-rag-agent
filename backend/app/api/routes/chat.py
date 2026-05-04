from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_owned_project
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import MessageResponse
from app.schemas.chat import (
    ChatQuestionRequest,
    ChatSessionCreateRequest,
    ChatSessionDetailResponse,
    ChatSessionSummaryResponse,
)
from app.services.rag import (
    ChatSessionError,
    KnowledgeBaseError,
    build_assistant_answer,
    create_chat_session,
    delete_chat_session,
    get_owned_chat_session,
    list_project_chat_sessions,
    load_recent_session_history,
    retrieve_project_chunks,
    save_assistant_message,
    save_user_message,
    stream_answer_chunks,
)

router = APIRouter(prefix="/projects/{project_id}/chat", tags=["chat"])


@router.get("/sessions", response_model=list[ChatSessionSummaryResponse])
def list_sessions(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[ChatSessionSummaryResponse]:
    get_owned_project(db, current_user.id, project_id)
    return list_project_chat_sessions(db, user_id=current_user.id, project_id=project_id)


@router.post("/sessions", response_model=ChatSessionSummaryResponse, status_code=status.HTTP_201_CREATED)
def create_session(
    project_id: str,
    payload: ChatSessionCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ChatSessionSummaryResponse:
    get_owned_project(db, current_user.id, project_id)
    return create_chat_session(db, user_id=current_user.id, project_id=project_id, title=payload.title)


@router.get("/sessions/{session_id}", response_model=ChatSessionDetailResponse)
def get_session(
    project_id: str,
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ChatSessionDetailResponse:
    get_owned_project(db, current_user.id, project_id)
    try:
        session = get_owned_chat_session(db, user_id=current_user.id, project_id=project_id, session_id=session_id)
    except ChatSessionError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    session.messages.sort(key=lambda message: message.created_at)
    return session


@router.delete("/sessions/{session_id}", response_model=MessageResponse)
def remove_session(
    project_id: str,
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MessageResponse:
    get_owned_project(db, current_user.id, project_id)
    try:
        delete_chat_session(db, user_id=current_user.id, project_id=project_id, session_id=session_id)
    except ChatSessionError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return MessageResponse(message="Chat session deleted.")


@router.post("/sessions/{session_id}/messages/stream")
def stream_session_message(
    project_id: str,
    session_id: str,
    payload: ChatQuestionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StreamingResponse:
    get_owned_project(db, current_user.id, project_id)
    try:
        session = get_owned_chat_session(db, user_id=current_user.id, project_id=project_id, session_id=session_id)
    except ChatSessionError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    question = payload.question.strip()
    if not question:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Question is required.")

    history_messages = load_recent_session_history(
        db,
        user_id=current_user.id,
        project_id=project_id,
        session_id=session_id,
    )
    save_user_message(db, user_id=current_user.id, project_id=project_id, session=session, question=question)

    try:
        retrieved_chunks = retrieve_project_chunks(db, user_id=current_user.id, project_id=project_id, question=question)
        answer = build_assistant_answer(
            history_messages=history_messages,
            retrieved_chunks=retrieved_chunks,
            question=question,
        )
    except KnowledgeBaseError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    sources = [chunk.to_source_reference() for chunk in retrieved_chunks] if answer != "当前知识库中没有足够信息" else []

    def content_stream():
        emitted_parts: list[str] = []
        for part in stream_answer_chunks(answer):
            emitted_parts.append(part)
            yield part
        final_answer = "".join(emitted_parts).strip() or answer
        save_assistant_message(
            db,
            user_id=current_user.id,
            project_id=project_id,
            session=session,
            content=final_answer,
            sources=sources,
        )

    return StreamingResponse(content_stream(), media_type="text/plain; charset=utf-8")
