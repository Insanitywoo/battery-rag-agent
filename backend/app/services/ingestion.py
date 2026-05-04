from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import re

from fastapi import HTTPException
from pypdf import PdfReader
from sqlalchemy import delete as sa_delete
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.document import Document, DocumentStatus, EmbeddingStatus
from app.models.document_chunk import DocumentChunk
from app.services.storage import resolve_storage_path


class DocumentProcessingError(Exception):
    pass


@dataclass(frozen=True)
class ParsedSegment:
    page_number: int | None
    content: str


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _read_text_file(document: Document) -> str:
    path = _resolve_document_path(document)
    try:
        return path.read_text(encoding="utf-8-sig", errors="ignore")
    except OSError as exc:
        raise DocumentProcessingError("Stored document could not be read.") from exc


def _resolve_document_path(document: Document):
    try:
        path = resolve_storage_path(document.storage_path)
    except HTTPException as exc:
        raise DocumentProcessingError("Stored document path is invalid.") from exc

    if not path.exists():
        raise DocumentProcessingError("Stored document file was not found.")
    if not path.is_file():
        raise DocumentProcessingError("Stored document path is invalid.")
    return path


def _parse_pdf(document: Document) -> list[ParsedSegment]:
    path = _resolve_document_path(document)
    try:
        reader = PdfReader(str(path))
    except Exception as exc:
        raise DocumentProcessingError("PDF text extraction failed.") from exc

    segments: list[ParsedSegment] = []
    for page_number, page in enumerate(reader.pages, start=1):
        try:
            text = page.extract_text() or ""
        except Exception as exc:
            raise DocumentProcessingError("PDF text extraction failed.") from exc
        if text.strip():
            segments.append(ParsedSegment(page_number=page_number, content=text))

    if not segments:
        raise DocumentProcessingError("No extractable text was found in the PDF.")
    return segments


def _parse_txt_or_markdown(document: Document) -> list[ParsedSegment]:
    text = _read_text_file(document)
    if not text.strip():
        raise DocumentProcessingError("The document does not contain readable text.")
    return [ParsedSegment(page_number=None, content=text)]


def _parse_csv(document: Document) -> list[ParsedSegment]:
    settings = get_settings()
    text = _read_text_file(document)
    preview = text[: settings.csv_preview_char_limit].strip()
    if not preview:
        raise DocumentProcessingError("The CSV file does not contain readable text.")
    return [ParsedSegment(page_number=None, content=preview)]


def parse_document(document: Document) -> list[ParsedSegment]:
    if document.file_type == "pdf":
        return _parse_pdf(document)
    if document.file_type in {"txt", "md"}:
        return _parse_txt_or_markdown(document)
    if document.file_type == "csv":
        return _parse_csv(document)
    raise DocumentProcessingError("Unsupported document type for processing.")


def clean_text(text: str) -> str:
    normalized = text.replace("\x00", "").replace("\r\n", "\n").replace("\r", "\n")
    cleaned_lines: list[str] = []
    previous_blank = False

    for raw_line in normalized.split("\n"):
        line = re.sub(r"[ \t]+", " ", raw_line).strip()
        if not line:
            if not previous_blank:
                cleaned_lines.append("")
            previous_blank = True
            continue

        cleaned_lines.append(line)
        previous_blank = False

    return "\n".join(cleaned_lines).strip()


def split_text_into_chunks(text: str) -> list[str]:
    settings = get_settings()
    if settings.chunk_overlap >= settings.chunk_size:
        raise DocumentProcessingError("Chunk configuration is invalid.")

    chunks: list[str] = []
    start = 0
    text_length = len(text)

    while start < text_length:
        target_end = min(text_length, start + settings.chunk_size)
        end = target_end

        if target_end < text_length:
            split_window_start = min(text_length - 1, start + max(settings.chunk_size // 2, 1))
            newline_break = text.rfind("\n", split_window_start, target_end)
            space_break = text.rfind(" ", split_window_start, target_end)
            candidate_break = max(newline_break, space_break)
            if candidate_break > start:
                end = candidate_break

        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        if end >= text_length:
            break

        next_start = max(end - settings.chunk_overlap, start + 1)
        while next_start < text_length and text[next_start].isspace():
            next_start += 1
        start = next_start

    return chunks


def build_document_chunks(document: Document) -> list[DocumentChunk]:
    parsed_segments = parse_document(document)
    chunks: list[DocumentChunk] = []
    chunk_index = 0

    for segment in parsed_segments:
        cleaned = clean_text(segment.content)
        if not cleaned:
            continue

        for chunk_text in split_text_into_chunks(cleaned):
            chunks.append(
                DocumentChunk(
                    user_id=document.user_id,
                    project_id=document.project_id,
                    document_id=document.id,
                    page_number=segment.page_number,
                    chunk_index=chunk_index,
                    content=chunk_text,
                    char_count=len(chunk_text),
                )
            )
            chunk_index += 1

    if not chunks:
        raise DocumentProcessingError("No readable text was available after document cleaning.")
    return chunks


def _mark_document_failed(db: Session, document: Document, message: str) -> Document:
    document.status = DocumentStatus.FAILED.value
    document.embedding_status = EmbeddingStatus.NOT_INDEXED.value
    document.error_message = message
    document.processed_at = None
    document.embedded_at = None
    document.chunk_count = 0
    db.add(document)
    db.commit()
    db.refresh(document)
    return document


def process_document_ingestion(db: Session, document: Document) -> Document:
    document.status = DocumentStatus.PROCESSING.value
    document.embedding_status = EmbeddingStatus.NOT_INDEXED.value
    document.error_message = None
    document.processed_at = None
    document.embedded_at = None
    document.chunk_count = 0
    db.add(document)
    db.execute(sa_delete(DocumentChunk).where(DocumentChunk.document_id == document.id))
    db.commit()
    db.refresh(document)

    try:
        chunks = build_document_chunks(document)
        db.add_all(chunks)
        document.status = DocumentStatus.PROCESSED.value
        document.embedding_status = EmbeddingStatus.NOT_INDEXED.value
        document.error_message = None
        document.processed_at = _utc_now()
        document.embedded_at = None
        document.chunk_count = len(chunks)
        db.add(document)
        db.commit()
        db.refresh(document)
        return document
    except DocumentProcessingError as exc:
        db.rollback()
        return _mark_document_failed(db, document, str(exc))
    except Exception:
        db.rollback()
        return _mark_document_failed(db, document, "Document processing failed.")
