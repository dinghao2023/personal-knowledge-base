"""问答：多轮历史 + 拼装 Prompt + LLM 生成 + 引用溯源。"""
from typing import Dict, List

from .config import settings
from .retrieve import search

_llm_client = None


def _get_llm():
    global _llm_client
    if _llm_client is None:
        if not settings.llm_api_key:
            raise RuntimeError("未配置 LLM_API_KEY，请在 backend/.env 中填写。")
        from openai import OpenAI

        _llm_client = OpenAI(
            base_url=settings.llm_base_url,
            api_key=settings.llm_api_key,
        )
    return _llm_client


SYSTEM_PROMPT = (
    "你是一个个人知识库助手。请仅根据提供的资料回答问题，给出简洁、准确的答案。"
    "回答中引用某条资料时，用 [序号] 标注，例如「根据资料[1]」。"
    "资料中没有的信息，请明确说明无法从知识库中得知，不要编造。"
)

# 根据检索结果，调用模型
def ask(question: str, history: List[Dict[str, str]]) -> Dict:
    hits = search(question)
    if not hits:
        return {
            "answer": "知识库中没有找到相关依据。请先上传相关文档，或换一种问法。",
            "citations": [],
        }

    context = "\n\n".join(f"[{i + 1}] {h.chunk}" for i, h in enumerate(hits))
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    # 只保留最近若干轮历史，避免上下文超限
    for msg in history[-settings.history_turns * 2:]:
        messages.append(msg)
    messages.append(
        {"role": "user", "content": f"资料：\n{context}\n\n问题：{question}"}
    )

    resp = _get_llm().chat.completions.create(
        model=settings.llm_model,
        messages=messages,
        temperature=0.2,
    )
    answer = resp.choices[0].message.content or ""

    citations = [
        {
            "source": h.source,
            "page": h.page,
            "snippet": h.chunk[:120],
        }
        for h in hits
    ]
    return {"answer": answer, "citations": citations}
