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
