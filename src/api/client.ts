import axios from 'axios'

/** 引用溯源：命中的片段与其原始来源 */
export interface Citation {
  source: string
  page?: number
  snippet: string
}

export interface ChatResponse {
  answer: string
  citations: Citation[]
}

export interface HistoryItem {
  role: 'user' | 'assistant'
  content: string
}

const client = axios.create({
  baseURL: '/api',
  timeout: 120000, // 问答耗时较长，放宽超时
})

/** 上传文档入库，返回已分块数量（对接 FastAPI /api/upload） */
export async function uploadDocument(file: File): Promise<{ chunks: number }> {
  const form = new FormData()
  form.append('file', file)
  const { data } = await client.post('/upload', form)
  return data
}

/** 多轮问答，返回答案与引用（对接 FastAPI /api/chat） */
export async function sendChat(
  question: string,
  history: HistoryItem[],
): Promise<ChatResponse> {
  const { data } = await client.post('/chat', { question, history })
  return data
}
