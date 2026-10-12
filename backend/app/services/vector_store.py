import json
import os
from pathlib import Path
from typing import Optional
import numpy as np
from app.core.config import settings

class VectorRecord:
    def __init__(
        self,
        chunk_id: str,
        document_id: str,
        deployment_id: str,
        text: str,
        page_number: Optional[int],
        section_heading: Optional[str],
        embedding: list[float]
    ):
        self.chunk_id = chunk_id
        self.document_id = document_id
        self.deployment_id = deployment_id
        self.text = text
        self.page_number = page_number
        self.section_heading = section_heading
        self.embedding = embedding

class ScoredChunk:
    def __init__(
        self,
        chunk_id: str,
        document_id: str,
        deployment_id: str,
        text: str,
        page_number: Optional[int],
        section_heading: Optional[str],
        score: float
    ):
        self.chunk_id = chunk_id
        self.document_id = document_id
        self.deployment_id = deployment_id
        self.text = text
        self.page_number = page_number
        self.section_heading = section_heading
        self.score = score

class LocalVectorStore:
    def __init__(self, storage_dir: Optional[str] = None):
        self.storage_dir = Path(storage_dir or settings.STORAGE_DIR)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.persist_path = self.storage_dir / "vector_store.json"
        # deployment_id -> list of VectorRecord
        self._records: dict[str, list[VectorRecord]] = {}
        self._load()

    def _load(self):
        if self.persist_path.exists():
            try:
                with open(self.persist_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for dep_id, items in data.items():
                        self._records[dep_id] = [
                            VectorRecord(
                                chunk_id=item["chunk_id"],
                                document_id=item["document_id"],
                                deployment_id=item["deployment_id"],
                                text=item["text"],
                                page_number=item.get("page_number"),
                                section_heading=item.get("section_heading"),
                                embedding=item["embedding"]
                            )
                            for item in items
                        ]
            except Exception as e:
                print(f"[VectorStore] Failed to load persisted vectors: {e}")

    def _save(self):
        try:
            data = {}
            for dep_id, items in self._records.items():
                data[dep_id] = [
                    {
                        "chunk_id": r.chunk_id,
                        "document_id": r.document_id,
                        "deployment_id": r.deployment_id,
                        "text": r.text,
                        "page_number": r.page_number,
                        "section_heading": r.section_heading,
                        "embedding": r.embedding
                    }
                    for r in items
                ]
            with open(self.persist_path, "w", encoding="utf-8") as f:
                json.dump(data, f)
        except Exception as e:
            print(f"[VectorStore] Failed to save vector store: {e}")

    def add_records(self, deployment_id: str, records: list[VectorRecord]):
        if deployment_id not in self._records:
            self._records[deployment_id] = []
        self._records[deployment_id].extend(records)
        self._save()

    def delete_document(self, deployment_id: str, document_id: str):
        if deployment_id in self._records:
            self._records[deployment_id] = [
                r for r in self._records[deployment_id] if r.document_id != document_id
            ]
            self._save()

    def delete_deployment(self, deployment_id: str):
        if deployment_id in self._records:
            del self._records[deployment_id]
            self._save()

    def search(
        self,
        deployment_id: str,
        query_vector: list[float],
        top_k: int = 6,
        active_document_ids: Optional[set[str]] = None
    ) -> list[ScoredChunk]:
        records = self._records.get(deployment_id, [])
        if not records:
            return []

        # Filter by active document IDs if provided
        filtered = [
            r for r in records
            if active_document_ids is None or r.document_id in active_document_ids
        ]
        if not filtered:
            return []

        query_arr = np.array(query_vector, dtype=np.float32)
        q_norm = np.linalg.norm(query_arr)
        if q_norm == 0:
            return []
        query_arr = query_arr / q_norm

        matrix = np.array([r.embedding for r in filtered], dtype=np.float32)
        # Normalize rows
        norms = np.linalg.norm(matrix, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        matrix_norm = matrix / norms

        # Cosine similarities
        scores = np.dot(matrix_norm, query_arr)

        # Get top-k indices
        k = min(top_k, len(filtered))
        top_indices = np.argsort(scores)[::-1][:k]

        results = []
        for idx in top_indices:
            r = filtered[idx]
            results.append(ScoredChunk(
                chunk_id=r.chunk_id,
                document_id=r.document_id,
                deployment_id=r.deployment_id,
                text=r.text,
                page_number=r.page_number,
                section_heading=r.section_heading,
                score=float(scores[idx])
            ))

        return results

vector_store = LocalVectorStore()
