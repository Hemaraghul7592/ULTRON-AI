from __future__ import annotations

import hashlib
import json
from typing import Any

import numpy as np

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class EmbeddingService:
    def __init__(self) -> None:
        settings = get_settings()
        self._dim = settings.EMBEDDING_DIM
        self._model = None

    async def initialize(self) -> None:
        try:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer("all-MiniLM-L6-v2")
            logger.info("embedding_model_loaded", dim=self._dim)
        except ImportError:
            logger.warning("sentence_transformers_not_available_using_fallback")
            self._model = None

    async def embed(self, text: str) -> list[float]:
        if self._model is not None:
            embedding = self._model.encode(text)
            return embedding.tolist()[: self._dim]
        return self._hash_embed(text)

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        if self._model is not None:
            embeddings = self._model.encode(texts)
            return [e.tolist()[: self._dim] for e in embeddings]
        return [self._hash_embed(t) for t in texts]

    def _hash_embed(self, text: str) -> list[float]:
        h = hashlib.sha256(text.encode()).digest()
        arr = np.frombuffer(h, dtype=np.uint8).astype(np.float32)
        padded = np.zeros(self._dim, dtype=np.float32)
        padded[: len(arr)] = arr[: self._dim]
        norm = np.linalg.norm(padded)
        if norm > 0:
            padded = padded / norm
        return padded.tolist()

    @staticmethod
    def cosine_similarity(a: list[float], b: list[float]) -> float:
        a_arr = np.array(a, dtype=np.float32)
        b_arr = np.array(b, dtype=np.float32)
        dot = float(np.dot(a_arr, b_arr))
        norm_a = float(np.linalg.norm(a_arr))
        norm_b = float(np.linalg.norm(b_arr))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)

    def serialize_vector(self, vector: list[float]) -> str:
        return json.dumps(vector)

    def deserialize_vector(self, data: str) -> list[float]:
        return json.loads(data)
