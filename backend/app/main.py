"""FastAPI 入口：/api 前缀路由，对接前端。"""
import os
from pathlib import Path
from typing import List, Literal

from fastapi import APIRouter, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import chat as chat_service
from .config import settings
from .db import count
from .ingest import SUPPORTED_EXTS, ingest_file, list_saved_files, save_upload

# docs_url=None：默认文档页从 cdn.jsdelivr.net 加载脚本，国内经常打不开
app = FastAPI(
    title="Knyx RAG API",
    version="0.1.0",
    description="个人知识库 RAG Agent 后端",
    docs_url=None,
)

_static_dir = Path(__file__).resolve().parent.parent / "static"
app.mount("/static", StaticFiles(directory=_static_dir), name="static")


@app.get("/docs", include_in_schema=False)
async def swagger_ui():
    """使用本机静态文件渲染 Swagger UI，不依赖外网 CDN。"""
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=f"{app.title} - Swagger UI",
        swagger_js_url="/static/swagger-ui-bundle.js",
        swagger_css_url="/static/swagger-ui.css",
    )

# 开发期允许跨域（前端 5173）；生产环境请收敛为具体来源
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

api = APIRouter(prefix="/api")


class HistoryItem(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    question: str
    history: List[HistoryItem] = []


@api.get("/health")
def health():
    return {"status": "ok", "chunks": count()}


@api.get("/documents")
def documents():
    """返回已落盘的文件列表。"""
    return {"files": list_saved_files()}


@api.post("/upload")
async def upload(file: UploadFile = File(...)):
    name = file.filename or ""
    ext = name.rsplit(".", 1)[-1].lower() if "." in name else ""
    if ext not in SUPPORTED_EXTS:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的格式: .{ext or '未知'}，支持 {sorted(SUPPORTED_EXTS)}",
        )
    saved = save_upload(file, os.path.basename(name))
    try:
        chunks = ingest_file(saved, os.path.basename(name))
    except RuntimeError as e:  # 未配置 embedding key 等
        raise HTTPException(status_code=500, detail=str(e))
    return {"filename": name, "chunks": chunks}


@api.post("/chat")
def chat(payload: ChatRequest):
    question = payload.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="question 不能为空")
    try:
        return chat_service.ask(
            question,
            [{"role": h.role, "content": h.content} for h in payload.history],
        )
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))


app.include_router(api)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
