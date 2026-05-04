from __future__ import annotations

import math
from dataclasses import dataclass
from threading import Lock

import httpx

from app.core.config import get_settings


class VectorStoreError(Exception):
    pass


@dataclass(frozen=True)
class VectorPoint:
    id: str
    vector: list[float]
    payload: dict[str, object]


@dataclass(frozen=True)
class VectorSearchResult:
    id: str
    score: float
    payload: dict[str, object]


_MEMORY_STORE: dict[str, dict[str, VectorPoint]] = {}
_MEMORY_LOCK = Lock()


def _cosine_similarity(left: list[float], right: list[float]) -> float:
    numerator = sum(a * b for a, b in zip(left, right, strict=False))
    left_norm = math.sqrt(sum(a * a for a in left))
    right_norm = math.sqrt(sum(b * b for b in right))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return numerator / (left_norm * right_norm)


class VectorStore:
    def __init__(self) -> None:
        self.settings = get_settings()

    @property
    def _use_memory(self) -> bool:
        return self.settings.qdrant_url.startswith("memory://")

    def ensure_collection(self, vector_size: int) -> None:
        if self._use_memory:
            with _MEMORY_LOCK:
                _MEMORY_STORE.setdefault(self.settings.qdrant_collection_name, {})
            return

        headers = self._headers()
        try:
            response = httpx.get(self._collection_url(), headers=headers, timeout=15.0)
            if response.status_code == 200:
                return
            if response.status_code != 404:
                response.raise_for_status()

            create_response = httpx.put(
                self._collection_url(),
                headers=headers,
                json={"vectors": {"size": vector_size, "distance": "Cosine"}},
                timeout=30.0,
            )
            if create_response.status_code not in {200, 201}:
                create_response.raise_for_status()
        except httpx.HTTPError as exc:
            raise VectorStoreError("Vector collection is unavailable.") from exc

    def replace_project_vectors(self, *, user_id: str, project_id: str, points: list[VectorPoint]) -> None:
        vector_size = len(points[0].vector) if points else 16
        self.ensure_collection(vector_size)
        self.delete_project_vectors(user_id=user_id, project_id=project_id)
        if points:
            self.upsert_points(points)

    def upsert_points(self, points: list[VectorPoint]) -> None:
        if self._use_memory:
            with _MEMORY_LOCK:
                collection = _MEMORY_STORE.setdefault(self.settings.qdrant_collection_name, {})
                for point in points:
                    collection[point.id] = point
            return

        payload = {
            "points": [
                {
                    "id": point.id,
                    "vector": point.vector,
                    "payload": point.payload,
                }
                for point in points
            ]
        }
        try:
            response = httpx.put(
                f"{self._collection_url()}/points?wait=true",
                headers=self._headers(),
                json=payload,
                timeout=60.0,
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise VectorStoreError("Vector write failed.") from exc

    def delete_project_vectors(self, *, user_id: str, project_id: str) -> None:
        self._delete_by_filters(user_id=user_id, project_id=project_id)

    def delete_document_vectors(self, *, user_id: str, project_id: str, document_id: str) -> None:
        self._delete_by_filters(user_id=user_id, project_id=project_id, document_id=document_id)

    def _delete_by_filters(self, **filters: str) -> None:
        if self._use_memory:
            with _MEMORY_LOCK:
                collection = _MEMORY_STORE.setdefault(self.settings.qdrant_collection_name, {})
                to_delete = [
                    point_id
                    for point_id, point in collection.items()
                    if all(point.payload.get(key) == value for key, value in filters.items())
                ]
                for point_id in to_delete:
                    collection.pop(point_id, None)
            return

        try:
            response = httpx.post(
                f"{self._collection_url()}/points/delete?wait=true",
                headers=self._headers(),
                json={"filter": self._qdrant_filter(filters)},
                timeout=60.0,
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise VectorStoreError("Vector delete failed.") from exc

    def search(
        self,
        *,
        vector: list[float],
        user_id: str,
        project_id: str,
        limit: int,
        score_threshold: float,
    ) -> list[VectorSearchResult]:
        if self._use_memory:
            with _MEMORY_LOCK:
                collection = list(_MEMORY_STORE.setdefault(self.settings.qdrant_collection_name, {}).values())
            results = []
            for point in collection:
                if point.payload.get("user_id") != user_id or point.payload.get("project_id") != project_id:
                    continue
                score = _cosine_similarity(vector, point.vector)
                if score < score_threshold:
                    continue
                results.append(VectorSearchResult(id=point.id, score=score, payload=point.payload))
            return sorted(results, key=lambda item: item.score, reverse=True)[:limit]

        try:
            response = httpx.post(
                f"{self._collection_url()}/points/search",
                headers=self._headers(),
                json={
                    "vector": vector,
                    "limit": limit,
                    "score_threshold": score_threshold,
                    "with_payload": True,
                    "filter": self._qdrant_filter({"user_id": user_id, "project_id": project_id}),
                },
                timeout=60.0,
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise VectorStoreError("Vector retrieval failed.") from exc

        payload = response.json()
        raw_results = payload.get("result", [])
        results: list[VectorSearchResult] = []
        for item in raw_results:
            try:
                results.append(
                    VectorSearchResult(
                        id=str(item["id"]),
                        score=float(item["score"]),
                        payload=dict(item.get("payload") or {}),
                    )
                )
            except (KeyError, TypeError, ValueError) as exc:
                raise VectorStoreError("Vector retrieval response was invalid.") from exc
        return results

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.settings.qdrant_api_key:
            headers["api-key"] = self.settings.qdrant_api_key
        return headers

    def _collection_url(self) -> str:
        return f"{self.settings.qdrant_url.rstrip('/')}/collections/{self.settings.qdrant_collection_name}"

    @staticmethod
    def _qdrant_filter(filters: dict[str, str]) -> dict[str, object]:
        return {
            "must": [
                {
                    "key": key,
                    "match": {"value": value},
                }
                for key, value in filters.items()
            ]
        }


def get_vector_store() -> VectorStore:
    return VectorStore()
