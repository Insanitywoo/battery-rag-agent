from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass

import httpx

from app.core.config import get_settings


class LLMGatewayError(Exception):
    pass


@dataclass(frozen=True)
class PromptChunk:
    document_name: str
    page_number: int | None
    chunk_index: int
    content: str


def _chunk_text(text: str, *, segment_size: int = 240) -> list[str]:
    cleaned = text.strip()
    if not cleaned:
        return []
    return [cleaned[index : index + segment_size] for index in range(0, len(cleaned), segment_size)]


class LLMGateway:
    def __init__(self) -> None:
        self.settings = get_settings()

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if self.settings.llm_provider == "mock":
            return [self._mock_embedding(text) for text in texts]
        return self._remote_embeddings(texts)

    def generate_answer(
        self,
        *,
        system_instruction: str,
        history_messages: list[tuple[str, str]],
        retrieved_chunks: list[PromptChunk],
        question: str,
    ) -> str:
        if self.settings.llm_provider == "mock":
            return self._mock_answer(history_messages=history_messages, retrieved_chunks=retrieved_chunks, question=question)
        return self._remote_chat_completion(
            system_instruction=system_instruction,
            history_messages=history_messages,
            retrieved_chunks=retrieved_chunks,
            question=question,
        )

    def _mock_embedding(self, text: str) -> list[float]:
        tokens = re.findall(r"[a-z0-9]+", text.lower())
        vector = [0.0] * 32
        if not tokens:
            return vector

        for token in tokens:
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            bucket = digest[0] % len(vector)
            sign = 1.0 if digest[1] % 2 == 0 else -1.0
            vector[bucket] += sign * (1.0 + (len(token) / 10.0))
        return vector

    def _mock_answer(
        self,
        *,
        history_messages: list[tuple[str, str]],
        retrieved_chunks: list[PromptChunk],
        question: str,
    ) -> str:
        snippets = []
        for chunk in retrieved_chunks[:2]:
            label = f"{chunk.document_name}"
            if chunk.page_number is not None:
                label = f"{label} p.{chunk.page_number}"
            snippets.append(f"{label}: {chunk.content.strip()}")

        answer_parts = [
            "Based on the current project knowledge base, here is a grounded answer.",
            f"Question: {question.strip()}",
        ]
        if history_messages:
            answer_parts.append(f"Recent context messages considered: {len(history_messages)}.")
        if snippets:
            answer_parts.append("Relevant evidence:")
            answer_parts.extend(snippets)
        return "\n".join(answer_parts)

    def _remote_embeddings(self, texts: list[str]) -> list[list[float]]:
        if not self.settings.llm_api_base_url or not self.settings.llm_api_key:
            raise LLMGatewayError("LLM embedding provider is not configured.")

        try:
            response = httpx.post(
                f"{self.settings.llm_api_base_url.rstrip('/')}/embeddings",
                headers={
                    "Authorization": f"Bearer {self.settings.llm_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.settings.llm_embedding_model,
                    "input": texts,
                },
                timeout=60.0,
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise LLMGatewayError("Embedding generation failed.") from exc

        payload = response.json()
        data = payload.get("data")
        if not isinstance(data, list):
            raise LLMGatewayError("Embedding provider response was invalid.")

        try:
            return [list(item["embedding"]) for item in data]
        except (KeyError, TypeError) as exc:
            raise LLMGatewayError("Embedding provider response was invalid.") from exc

    def _remote_chat_completion(
        self,
        *,
        system_instruction: str,
        history_messages: list[tuple[str, str]],
        retrieved_chunks: list[PromptChunk],
        question: str,
    ) -> str:
        if not self.settings.llm_api_base_url or not self.settings.llm_api_key:
            raise LLMGatewayError("LLM chat provider is not configured.")

        messages = [{"role": "system", "content": system_instruction}]
        for role, content in history_messages:
            messages.append({"role": role, "content": content})

        evidence_blocks = []
        for chunk in retrieved_chunks:
            prefix = f"[{chunk.document_name}"
            if chunk.page_number is not None:
                prefix = f"{prefix} p.{chunk.page_number}"
            prefix = f"{prefix} chunk {chunk.chunk_index}]"
            evidence_blocks.append(f"{prefix}\n{chunk.content}")

        messages.append(
            {
                "role": "user",
                "content": "\n\n".join(
                    [
                        "Use only the provided evidence to answer the question.",
                        "Evidence:",
                        "\n\n".join(evidence_blocks),
                        f"Question: {question}",
                    ]
                ),
            }
        )

        try:
            response = httpx.post(
                f"{self.settings.llm_api_base_url.rstrip('/')}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.settings.llm_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.settings.llm_chat_model,
                    "messages": messages,
                    "stream": False,
                },
                timeout=90.0,
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise LLMGatewayError("LLM chat generation failed.") from exc

        payload = response.json()
        try:
            return str(payload["choices"][0]["message"]["content"]).strip()
        except (KeyError, IndexError, TypeError) as exc:
            raise LLMGatewayError("LLM chat provider response was invalid.") from exc

    def stream_text_chunks(self, text: str) -> list[str]:
        return _chunk_text(text)


def get_llm_gateway() -> LLMGateway:
    return LLMGateway()
