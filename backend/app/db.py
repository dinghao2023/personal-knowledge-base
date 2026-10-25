"""Chroma 向量库封装（进程内单例）。"""
import chromadb

from .config import settings

_client = None
_collection = None
_vectorstore = None


def get_client():
    """懒加载 Chroma 持久化客户端。LangChain 和底层集合共用这一个客户端。"""
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(path=settings.chroma_dir)
    return _client


def get_collection():
    """返回底层集合，供计数、删除和按来源统计。"""
    global _collection
    if _collection is not None:
        return _collection
    _collection = get_client().get_or_create_collection(
        name=settings.collection_name,
        metadata={"hnsw:space": "cosine"},
    )
    return _collection


def get_vectorstore():
    """返回 LangChain Chroma 向量库。入库和检索都通过它调用。"""
    global _vectorstore
    if _vectorstore is not None:
        return _vectorstore
    from langchain_chroma import Chroma

    from .embeddings import get_embedding

    _vectorstore = Chroma(
        client=get_client(),
        collection_name=settings.collection_name,
        embedding_function=get_embedding(),
        collection_metadata={"hnsw:space": "cosine"},
    )
    return _vectorstore


def count() -> int:
    """返回当前知识库分块总数。"""
    try:
        return get_collection().count()
    except Exception:
        return 0
