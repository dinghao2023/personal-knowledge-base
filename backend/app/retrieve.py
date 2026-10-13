"""检索：Top-K 向量召回 + 相似度阈值过滤。"""
from typing import List

from .config import settings
from .db import get_collection
from .embeddings import get_embedding


class Hit:
    def __init__(self, chunk: str, source: str, page, score: float):
        self.chunk = chunk
        self.source = source
        self.page = page
        self.score = score


def search(query: str, top_k: int | None = None) -> List[Hit]:
    embedder = get_embedding()
    collection = get_collection()
    k = top_k or settings.top_k

    q_vec = embedder.embed_query(query)
    res = collection.query(
        query_embeddings=[q_vec],
        n_results=k,
        include=["documents", "metadatas", "distances"],
    )

    docs = (res.get("documents") or [[]])[0]
    metas = (res.get("metadatas") or [[]])[0]
    dists = (res.get("distances") or [[]])[0]

    hits: List[Hit] = []
    for chunk, meta, dist in zip(docs, metas, dists):
        sim = 1 - dist  # 余弦距离 → 相似度
        if sim < settings.similarity_threshold:
            continue
        hits.append(
            Hit(
                chunk=chunk,
                source=meta.get("source", ""),
                page=meta.get("page") or None,
                score=round(sim, 3),
            )
        )
    return hits
