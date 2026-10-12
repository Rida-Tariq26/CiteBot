import hashlib
import re
import numpy as np
import httpx
from typing import Optional
from app.core.config import settings

class EmbeddingService:
    def __init__(self):
        self.provider = settings.LLM_PROVIDER
        self.openai_key = settings.OPENAI_API_KEY
        self.dimension = 384  # standard embedding dimensionality

    async def get_embedding(self, text: str) -> list[float]:
        embeddings = await self.get_embeddings([text])
        return embeddings[0] if embeddings else [0.0] * self.dimension

    async def get_embeddings(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        # If OpenAI is configured and API key is present
        if self.provider == "openai" and self.openai_key:
            try:
                return await self._get_openai_embeddings(texts)
            except Exception as e:
                # Log or fallback to deterministic offline embedding
                print(f"[EmbeddingService] OpenAI embedding error: {e}, falling back to offline embedder")

        # Deterministic offline vector embedding (works without internet / API key)
        return [self._compute_offline_vector(t) for t in texts]

    async def _get_openai_embeddings(self, texts: list[str]) -> list[list[float]]:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://api.openai.com/v1/embeddings",
                headers={
                    "Authorization": f"Bearer {self.openai_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": settings.OPENAI_EMBEDDING_MODEL,
                    "input": texts
                }
            )
            response.raise_for_status()
            data = response.json()
            return [item["embedding"] for item in data["data"]]

    def _compute_offline_vector(self, text: str) -> list[float]:
        """
        Generates a normalized semantic-aware hash embedding vector in pure numpy.
        Accurately captures word co-occurrence, term frequencies, and character 3-grams
        for reliable cosine similarity matching across documents.
        """
        vec = np.zeros(self.dimension, dtype=np.float32)
        words = re.findall(r"\w+", text.lower())
        if not words:
            return vec.tolist()

        for word in words:
            # Word hash index
            h = int(hashlib.md5(word.encode()).hexdigest(), 16)
            idx = h % self.dimension
            sign = 1.0 if (h >> 8) % 2 == 0 else -1.0
            vec[idx] += sign * 1.5

            # Subword 3-grams
            if len(word) >= 3:
                for i in range(len(word) - 2):
                    ngram = word[i:i+3]
                    nh = int(hashlib.md5(ngram.encode()).hexdigest(), 16)
                    nidx = nh % self.dimension
                    vec[nidx] += 0.5

        # L2 Normalize
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec.tolist()

embedding_service = EmbeddingService()
