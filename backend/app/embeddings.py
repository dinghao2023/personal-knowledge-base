"""向量化：LangChain Embeddings。默认走 OpenAI 兼容接口，也可切到本地模型。"""
from langchain_core.embeddings import Embeddings

from .config import settings

_embedder: Embeddings | None = None


def get_embedding() -> Embeddings:
    """返回向量化器单例。入库和检索共用同一个模型，保证向量空间一致。"""
    global _embedder
    if _embedder is not None:
        return _embedder
    if settings.embedding_provider == "local":
        _embedder = _local_embedding()
    else:
        _embedder = _api_embedding()
    return _embedder


def _api_embedding() -> Embeddings:
    if not settings.embedding_api_key:
        raise RuntimeError("未配置 EMBEDDING_API_KEY，请在 backend/.env 中填写。")
    from langchain_openai import OpenAIEmbeddings

    # bge-m3 不是 OpenAI 模型，关掉 tiktoken 分词，把原文直接发给 /embeddings
    return OpenAIEmbeddings(
        model=settings.embedding_model,
        api_key=settings.embedding_api_key,
        base_url=settings.embedding_base_url,
        check_embedding_ctx_length=False,
        tiktoken_enabled=False,
    )


def _local_embedding() -> Embeddings:
    try:
        from langchain_huggingface import HuggingFaceEmbeddings
    except ImportError as exc:
        raise RuntimeError(
            "本地向量化需要额外安装：pip install sentence-transformers langchain-huggingface"
        ) from exc
    return HuggingFaceEmbeddings(
        model_name=settings.embedding_local_model,
        encode_kwargs={"normalize_embeddings": True},
    )
