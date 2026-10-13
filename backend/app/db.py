"""Chroma 向量库封装（进程内单例）。"""
import chromadb

from .config import settings

_client = None
_collection = None


def get_collection():
    """懒加载并返回向量集合。"""
    global _client, _collection
    if _collection is not None:
        return _collection
    _client = chromadb.PersistentClient(path=settings.chroma_dir)
    _collection = _client.get_or_create_collection(
        name=settings.collection_name,
        metadata={"hnsw:space": "cosine"},
    )
    return _collection


def count() -> int:
    """返回当前知识库分块总数。"""
    try:
        return get_collection().count()
    except Exception:
        return 0
