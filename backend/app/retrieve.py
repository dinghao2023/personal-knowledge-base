"""检索：LangChain 向量库 Top-K 召回 + 相似度阈值过滤。"""
from typing import List

from .config import settings
from .db import get_vectorstore


class Hit:
    def __init__(self, chunk: str, source: str, page, score: float):
        self.chunk = chunk
        self.source = source
        self.page = page
        self.score = score

# 只做检索。将问题向量化后，在集合里找出最相近的几段，返回Hit列表
def search(query: str, top_k: int | None = None) -> List[Hit]:
    """把问题向量化后，在集合里按余弦相似度取最相近的若干块。"""
    k = top_k or settings.top_k
    pairs = get_vectorstore().similarity_search_with_relevance_scores(query, k=k)

    hits: List[Hit] = []
    for doc, score in pairs:
        if score < settings.similarity_threshold:
            continue
        page = doc.metadata.get("page") or None
        hits.append(
            Hit(
                chunk=doc.page_content,
                source=doc.metadata.get("source", ""),
                page=page,
                score=round(float(score), 3),
            )
        )
    return hits
