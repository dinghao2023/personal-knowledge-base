"""问答：检索结果经 LangChain 提示词链交给 LLM，并按 token 流式返回。"""
import re
from typing import Dict, Iterator, List

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from .config import settings
from .retrieve import search

_chain = None
_intro_chain = None

# 助手名称只改这里。自我介绍走单独提示，不检索知识库。
_IDENTITY = "你是一个个人知识库助手，名叫小K。"

SYSTEM_PROMPT = (
    _IDENTITY
    + "请仅根据提供的资料回答问题，给出简洁、准确的答案。"
    "回答中引用某条资料时，用 [序号] 标注，例如「根据资料[1]」。"
    "资料中没有的信息，请明确说明无法从知识库中得知，不要编造。"
)

_INTRO_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            _IDENTITY
            + "用户正在让你介绍自己。请用第一人称简短介绍，名称和身份只以这句话为准。"
            "不要使用知识库，不要扮演资料或历史对话里的其他角色。",
        ),
        ("human", "{question}"),
    ]
)

_INTRO_RE = re.compile(
    r"介绍(一下|下)?(你)?自己|自我介绍|你是谁|你叫什么(名字|名)?|你的名字(是什么|叫什么)?"
)

_PROMPT = ChatPromptTemplate.from_messages(
    [
        ("system", SYSTEM_PROMPT),
        MessagesPlaceholder("history"),
        ("human", "资料：\n{context}\n\n问题：{question}"),
    ]
)


def _build_llm():
    if not settings.llm_api_key:
        raise RuntimeError("未配置 LLM_API_KEY，请在 backend/.env 中填写。")
    from langchain_openai import ChatOpenAI

    return ChatOpenAI(
        model=settings.llm_model,
        api_key=settings.llm_api_key,
        base_url=settings.llm_base_url,
        temperature=0.2,
    )

# 问答的模型链
def _get_chain():
    global _chain
    if _chain is not None:
        return _chain
    _chain = _PROMPT | _build_llm()  # | 为管道运算符，表示将 _PROMPT 的结果作为 llm 的输入
    return _chain

# 自我介绍的模型链
def _get_intro_chain():
    global _intro_chain
    if _intro_chain is not None:
        return _intro_chain
    _intro_chain = _INTRO_PROMPT | _build_llm()
    return _intro_chain


# 判断问题是否是自我介绍，是则返回True，否则返回False，若夹着别的问题也返回False
def _is_self_intro(question: str) -> bool:
    """问题本身是在让助手介绍自己时返回 True，附带其他知识库问题时返回 False。"""
    compact = re.sub(r"[\s，。！？、~～,.!?？！\-—：:\"'“”‘’]", "", question.strip())
    compact = re.sub(r"^(请你|请|帮我|你能|能否|可以)+", "", compact)
    if not _INTRO_RE.search(compact):
        return False
    leftover = _INTRO_RE.sub("", compact)
    return len(leftover) <= 2


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


def prepare_answer(question: str, history: List[Dict[str, str]]) -> Dict:
    """检索并建好模型链。配置错误在这里抛出，避免响应已经开始才失败。"""
    if _is_self_intro(question):
        _get_intro_chain()
        return {"mode": "intro", "question": question}

    hits = search(question)
    if not hits:
        return {"mode": "empty"}

    _get_chain()
    context = "\n\n".join(f"[{i + 1}] {h.chunk}" for i, h in enumerate(hits))
    history_msgs = [
        {"role": msg["role"], "content": msg["content"]}
        for msg in history[-settings.history_turns * 2 :]
    ]
    citations = [
        {
            "source": h.source,
            "page": h.page,
            "snippet": h.chunk[:120],
        }
        for h in hits
    ]
    return {
        "mode": "rag",
        "question": question,
        "context": context,
        "history": history_msgs,
        "citations": citations,
    }


def _stream_chain(chain, payload: Dict) -> Iterator[Dict]:
    for chunk in chain.stream(payload):
        text = _message_text(chunk)
        if text:
            yield {"type": "delta", "text": text}
    yield {"type": "done"}


def iter_events(prepared: Dict) -> Iterator[Dict]:
    """产出 SSE 事件：meta（引用）、delta（增量文本）、done。"""
    mode = prepared["mode"]
    if mode == "empty":
        yield {"type": "meta", "citations": []}
        yield {"type": "delta", "text": "知识库中没有找到相关依据。请先上传相关文档，或换一种问法。"}
        yield {"type": "done"}
        return
    if mode == "intro":
        yield {"type": "meta", "citations": []}
        yield from _stream_chain(_get_intro_chain(), {"question": prepared["question"]})
        return

    yield {"type": "meta", "citations": prepared["citations"]}
    yield from _stream_chain(
        _get_chain(),
        {
            "history": prepared["history"],
            "context": prepared["context"],
            "question": prepared["question"],
        },
    )
