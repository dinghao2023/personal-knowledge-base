"""问答：检索结果经 LangChain 提示词链交给 LLM，并带回引用。"""
from typing import Dict, List

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from .config import settings
from .retrieve import search

_chain = None

SYSTEM_PROMPT = (
    "你是一个个人知识库助手。请仅根据提供的资料回答问题，给出简洁、准确的答案。"
    "回答中引用某条资料时，用 [序号] 标注，例如「根据资料[1]」。"
    "资料中没有的信息，请明确说明无法从知识库中得知，不要编造。"
)

_PROMPT = ChatPromptTemplate.from_messages(
    [
        ("system", SYSTEM_PROMPT),
        MessagesPlaceholder("history"),
        ("human", "资料：\n{context}\n\n问题：{question}"),
    ]
)


def _get_chain():
    global _chain
    if _chain is not None:
        return _chain
    if not settings.llm_api_key:
        raise RuntimeError("未配置 LLM_API_KEY，请在 backend/.env 中填写。")
    from langchain_openai import ChatOpenAI

    llm = ChatOpenAI(
        model=settings.llm_model,
        api_key=settings.llm_api_key,
        base_url=settings.llm_base_url,
        temperature=0.2,
    )
    _chain = _PROMPT | llm
    return _chain


def _message_text(message) -> str:
    content = getattr(message, "content", "")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: List[str] = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict):
                parts.append(str(block.get("text") or ""))
        return "".join(parts)
    return str(content or "")


def ask(question: str, history: List[Dict[str, str]]) -> Dict:
    hits = search(question)
    if not hits:
        return {
            "answer": "知识库中没有找到相关依据。请先上传相关文档，或换一种问法。",
            "citations": [],
        }

    context = "\n\n".join(f"[{i + 1}] {h.chunk}" for i, h in enumerate(hits))
    # 只保留最近若干轮历史，避免上下文超限
    history_msgs = [
        {"role": msg["role"], "content": msg["content"]}
        for msg in history[-settings.history_turns * 2 :]
    ]
    message = _get_chain().invoke(
        {"history": history_msgs, "context": context, "question": question}
    )

    citations = [
        {
            "source": h.source,
            "page": h.page,
            "snippet": h.chunk[:120],
        }
        for h in hits
    ]
    return {"answer": _message_text(message), "citations": citations}
