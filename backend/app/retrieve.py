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

# 根据问题，进行向量检索
def search(query: str, top_k: int | None = None) -> List[Hit]:
    embedder = get_embedding() # ApiEmbedding，模型BAAI/bge-m3
    collection = get_collection() # 集合knyx，比如共计1503条
    k = top_k or settings.top_k

    q_vec = embedder.embed_query(query) # 问题向量化
    res = collection.query( # 向量化后的问题与集合中的每条文档计算余弦相似度
        query_embeddings=[q_vec], # 两层列表，外层长度1，即问的1个问题，内层长度1024，即这个问题的向量
        n_results=k,
        include=["documents", "metadatas", "distances"],
    )

    docs = (res.get("documents") or [[]])[0] # res是字典，其documents是两层列表，最终docs为一层列表，长度为k，即4
    metas = (res.get("metadatas") or [[]])[0]
    dists = (res.get("distances") or [[]])[0]

    hits: List[Hit] = []
    for chunk, meta, dist in zip(docs, metas, dists):
        sim = 1 - dist  # 余弦相似度，即 1 - 余弦距离
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
