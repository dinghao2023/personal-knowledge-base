"""入库链路：文档解析 → 分块 → 向量化 → 写入向量库。"""
import os
from datetime import datetime
from typing import List, Optional, Tuple

from .config import settings
from .db import get_collection
from .embeddings import get_embedding

SUPPORTED_EXTS = {"pdf", "docx", "md", "txt"}


def extract_pages(path: str) -> List[Tuple[str, Optional[int]]]:
    """返回 [(页面文本, 页码或 None)]。PDF 保留页码用于溯源，其余格式页码为 None。"""
    ext = path.rsplit(".", 1)[-1].lower()
    if ext == "pdf":
        import fitz

        doc = fitz.open(path)
        return [(page.get_text(), i + 1) for i, page in enumerate(doc)]
    if ext == "docx":
        import docx

        paras = [p.text for p in docx.Document(path).paragraphs if p.text]
        return [("\n".join(paras), None)]
    if ext == "md":
        with open(path, encoding="utf-8") as f:
            return [(f.read(), None)]
    if ext == "txt":
        with open(path, encoding="utf-8") as f:
            return [(f.read(), None)]
    raise ValueError(f"不支持的文件类型: .{ext}")


def _find_split(text: str, start: int, hard_end: int) -> int:
    """在 [start, hard_end] 内找最优断点，优先换行/句号。"""
    if hard_end >= len(text):
        return len(text)
    seg = text[start:hard_end]
    for ch in ["\n\n", "\n", "。", "！", "？", ".", "!", "；"]:
        idx = seg.rfind(ch)
        if idx > len(seg) * 0.5:
            return start + idx + len(ch)
    return hard_end


def chunk_text(text: str, size: int, overlap: int) -> List[str]:
    """递归分块，带 overlap 保留上下文。"""
    chunks: List[str] = []
    start = 0
    n = len(text)
    while start < n:
        end = _find_split(text, start, min(start + size, n))
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= n:
            break
        start = max(end - overlap, start + 1)
    return chunks


def ingest_file(file_path: str, filename: str) -> int:
    """解析文档并写入向量库，返回分块数量。"""
    pages = extract_pages(file_path)
    embedder = get_embedding()
    collection = get_collection()

    texts: List[str] = []
    metas: List[dict] = []
    ids: List[str] = []
    idx = 0
    for page_text, page_no in pages:
        for chunk in chunk_text(page_text, settings.chunk_size, settings.chunk_overlap):
            texts.append(chunk)
            metas.append({"source": filename, "page": page_no or 0})
            ids.append(f"{filename}_{idx}")
            idx += 1

    if not texts:
        return 0

    # 向量化，将文本转换为向量。默认模型 BAAI/bge-m3 的稠密向量长度为1024
    embeddings = embedder.embed_documents(texts)
    # 写入向量库
    collection.upsert(ids=ids, embeddings=embeddings, documents=texts, metadatas=metas)
    return len(texts)


def _chunk_counts() -> dict:
    """按文件名统计向量库中的分块数量。"""
    counts: dict = {}
    try:
        data = get_collection().get(include=["metadatas"])
    except Exception:
        return counts
    for meta in data.get("metadatas") or []:
        source = (meta or {}).get("source")
        if source:
            counts[source] = counts.get(source, 0) + 1
    return counts


def list_saved_files() -> List[dict]:
    """列出 docs 目录中已保存的文件，并附上分块数与修改时间。"""
    os.makedirs(settings.docs_dir, exist_ok=True)
    counts = _chunk_counts()
    files: List[dict] = []
    for name in os.listdir(settings.docs_dir):
        if name.startswith("."):
            continue
        path = os.path.join(settings.docs_dir, name)
        if not os.path.isfile(path):
            continue
        stat = os.stat(path)
        uploaded_at = datetime.fromtimestamp(stat.st_mtime).astimezone().isoformat(timespec="seconds")
        files.append(
            {
                "filename": name,
                "size": stat.st_size,
                "chunks": counts.get(name, 0),
                "uploaded_at": uploaded_at,
            }
        )
    files.sort(key=lambda item: item["uploaded_at"], reverse=True)
    return files


def delete_saved_file(filename: str) -> None:
    """删除 docs 目录中的文件，并清除向量库里该文件的全部分块。"""
    name = os.path.basename(filename)
    if not name or name != filename or name.startswith("."):
        raise ValueError("非法文件名")

    os.makedirs(settings.docs_dir, exist_ok=True)
    docs_root = os.path.realpath(settings.docs_dir)
    path = os.path.realpath(os.path.join(docs_root, name))
    if os.path.commonpath([docs_root, path]) != docs_root:
        raise ValueError("非法文件名")
    if not os.path.isfile(path):
        raise FileNotFoundError(name)

    get_collection().delete(where={"source": name})
    os.remove(path)


def save_upload(upload_file, filename: str) -> str:
    """保存上传文件到 docs 目录，返回落盘路径。"""
    os.makedirs(settings.docs_dir, exist_ok=True)
    dest = os.path.join(settings.docs_dir, filename)
    with open(dest, "wb") as f:
        f.write(upload_file.file.read())
    return dest
