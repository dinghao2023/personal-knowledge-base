# Knyx 后端 — FastAPI RAG Agent

个人知识库 RAG 后端：文档解析 → 分块 → 向量化 → 检索 → LLM 生成 → 引用溯源。

## 快速开始

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate            # Windows
pip install -r requirements.txt
copy .env.example .env            # Windows；macOS/Linux 用 cp
# 编辑 .env 填入 LLM 与 Embedding 的 API Key
uvicorn app.main:app --reload --port 8000
```

服务地址 `http://localhost:8000`，接口文档 `http://localhost:8000/docs`。

前端已通过 Vite 代理将 `/api` 转发到本服务，直接 `npm run dev` 即可联调。

## 接口

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| POST | `/api/upload` | 上传文档（multipart，字段 `file`），返回 `{ chunks }` |
| GET | `/api/documents` | 已落盘文件列表，含大小、分块数、修改时间 |
| POST | `/api/chat` | 多轮问答，入参 `{ question, history }`，返回 `{ answer, citations }` |
| GET | `/api/health` | 健康检查，返回知识库分块数量 |

支持格式：PDF / DOCX / Markdown / TXT。

## 配置（.env）

核心项见 `.env.example`。要点：

- **LLM**：任意 OpenAI 兼容服务（DeepSeek / 智谱 / 通义 / 豆包），填 `LLM_*`。
- **Embedding**：默认 `EMBEDDING_PROVIDER=api`（轻量，远端向量化，需支持 `/embeddings` 的服务）；
  如要完全本地、免费，改为 `local` 并 `pip install sentence-transformers`（体积较大）。

## 目录

```
app/
├── main.py        # FastAPI 入口 + 路由
├── config.py      # .env 配置
├── db.py          # Chroma 向量库封装
├── embeddings.py  # 向量化抽象（api / local）
├── ingest.py      # 入库：解析、分块、写库
├── retrieve.py    # 检索（Top-K + 相似度阈值）
└── chat.py        # 问答：多轮、拼装、LLM、溯源
```

## Chroma 里存什么

Chroma 是本地向量库，数据目录为 `backend/chroma_db`（配置项 `CHROMA_DIR`）。本项目只使用其中的一个集合，名字是 `knyx`（配置项 `COLLECTION_NAME`）。打开方式在 `app/db.py`：`PersistentClient` 指向数据目录，再按集合名 `get_or_create_collection`。

上传一份文件会留下两份数据：

| 位置 | 内容 |
| --- | --- |
| `backend/docs/` | 原始文件本身。`app/ingest.py` 的 `save_upload` 按文件名覆盖写入 |
| 集合 `knyx` | 切块后的文本、向量和来源。`ingest_file` 写入 |

原始文件不进 Chroma。问答检索只用集合里的分块。

### 存放位置

`knyx` 是集合，不是一张表。集合名单和分块内容都在 `backend/chroma_db/chroma.sqlite3`，由 Chroma 拆进自己的内部表。用 DB Browser for SQLite 或 DBeaver 打开这个文件时，看不到名为 `knyx` 的表。

| 位置 | 存什么 |
| --- | --- |
| 目录 `backend/docs/` | 上传的原始文件 |
| 集合 `knyx` | 程序通过 `upsert` / `get` 看到的全部分块。当前只有这一个集合 |
| 表 `collections` | 集合名单。现在只有一行，`name` 为 `knyx`，并带一个内部 id。分块记录不在这张表里 |
| 表 `embeddings` | 每条分块的内部编号，对应 `文件名_序号` 这种 id |
| 表 `embedding_metadata` | 正文和来源。`chroma:document` 是原文，`source` 是文件名，`page` 是页码 |
| `backend/chroma_db` 里的索引文件 | 1024 维向量。`segments` 表记录这些索引分段，向量本身不是 `embedding_metadata` 的普通文本列 |

服务运行期间只用客户端查看 `chroma.sqlite3`，不要在里面改行或删行。

### 写入过程

`POST /api/upload`（`app/main.py`）校验扩展名后调用 `save_upload`，再调用 `ingest_file`。支持 PDF、DOCX、Markdown、TXT。

`ingest_file` 的顺序是：

1. `extract_pages` 抽出文字。PDF 按页保留从 1 开始的页码；DOCX、Markdown、TXT 整篇作为一页，页码记为 `0`。
2. `chunk_text` 按约 500 字切块，相邻块重叠约 80 字，断点优先落在换行或句号。
3. `embed_documents` 把每块发给向量模型。默认是硅基流动上的 `BAAI/bge-m3`，每块得到 1024 维向量。
4. `collection.upsert` 写入集合 `knyx`。

抽不出文字时，原文件仍留在 `docs/`，接口返回 `chunks: 0`，集合不增加记录。

### 每条记录的四个字段

`upsert` 一次写入四份等长列表，相同下标组成一条记录：

| 字段 | 含义 | 例子 |
| --- | --- | --- |
| `id` | 文件名加下划线，再加从 0 开始的序号。序号按该文件的分块连续递增，不按页重置 | `TypeScript 极速梳理.pdf_0` |
| `document` | 这一块的原文 | 约 500 字的一段正文 |
| `embedding` | 这段原文的向量 | 1024 个浮点数 |
| `metadata` | 来源 | `{"source": "TypeScript 极速梳理.pdf", "page": 1}` |

同一 `id` 再次上传会被覆盖。新文件比旧文件更短时，多出来的旧序号不会自动删除，那些旧分块仍可能被检索到。

### 如何查看

知识库页面的 `GET /api/documents` 只列出 `docs/` 中的文件名、字节大小、分块数和修改时间，不返回每一块正文。

查看集合里的记录：在 `backend` 目录激活 `.venv` 后执行

```powershell
python -c "from app.db import get_collection; c=get_collection(); print(c.name, c.count()); d=c.get(limit=3, include=['documents','metadatas']); [print(i, m, (doc or '')[:60]) for i,m,doc in zip(d['ids'], d['metadatas'], d['documents'])]"
```

第一行是集合名和分块总数。后面每条是记录 `id`、元数据，以及正文的前 60 个字符。这条命令不打印向量。

用 SQLite 客户端查看时，到表 `collections` 确认集合名，到表 `embedding_metadata` 看正文和来源。按一条完整记录查看时，仍用上面的 `collection.get()`。
