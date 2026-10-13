"""向量化抽象：api（远端 OpenAI 兼容 /embeddings）或 local（sentence-transformers）。"""
from abc import ABC, abstractmethod
from typing import List

from .config import settings

_embedder = None


class EmbeddingProvider(ABC):
    @abstractmethod
    def embed_documents(self, texts: List[str]) -> List[List[float]]: ...

    @abstractmethod
    def embed_query(self, text: str) -> List[float]: ...


class ApiEmbedding(EmbeddingProvider):
    def __init__(self):
        from openai import OpenAI

        if not settings.embedding_api_key:
            raise RuntimeError("未配置 EMBEDDING_API_KEY，请在 backend/.env 中填写。")
        self._client = OpenAI(
            base_url=settings.embedding_base_url,
            api_key=settings.embedding_api_key,
        )
        self._model = settings.embedding_model

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        resp = self._client.embeddings.create(model=self._model, input=texts)
        return [d.embedding for d in resp.data]

    def embed_query(self, text: str) -> List[float]:
        return self.embed_documents([text])[0]


class LocalEmbedding(EmbeddingProvider):
    def __init__(self):
        from sentence_transformers import SentenceTransformer

        self._model = SentenceTransformer(settings.embedding_local_model)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return self._model.encode(texts, normalize_embeddings=True).tolist()

    def embed_query(self, text: str) -> List[float]:
        return self._model.encode([text], normalize_embeddings=True).tolist()[0]


def get_embedding() -> EmbeddingProvider:
    """返回向量化器单例。"""
    global _embedder
    if _embedder is None:
        if settings.embedding_provider == "local":
            _embedder = LocalEmbedding()
        else:
            _embedder = ApiEmbedding()
    return _embedder
