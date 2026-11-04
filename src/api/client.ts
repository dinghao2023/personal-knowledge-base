import axios from 'axios'

/** 引用溯源：命中的片段与其原始来源 */
export interface Citation {
  source: string
  page?: number
  snippet: string
}

export interface HistoryItem {
  role: 'user' | 'assistant'
  content: string
}

const client = axios.create({
  baseURL: '/api',
  timeout: 120000, // 问答耗时较长，放宽超时
})

export interface SavedFile {
  filename: string
  size: number
  chunks: number
  uploaded_at: string
}

/** 获取已上传的文件（对接 FastAPI /api/documents） */
export async function listDocuments(): Promise<{ files: SavedFile[] }> {
  const { data } = await client.get('/documents')
  return data
}

/** 删除已上传文档及其向量分块（对接 FastAPI DELETE /api/documents/{filename}） */
export async function deleteDocument(filename: string): Promise<void> {
  await client.delete(`/documents/${encodeURIComponent(filename)}`)
}

/** 取出 FastAPI 返回的 detail，没有时退回通用错误信息。 */
export function getApiErrorMessage(err: unknown): string {
  if (axios.isAxiosError(err)) {
    const detail = (err.response?.data as { detail?: unknown } | undefined)?.detail
    if (typeof detail === 'string' && detail.trim()) return detail
  }
  if (err instanceof Error) return err.message
  return String(err)
}

/** 上传文档入库，返回已分块数量（对接 FastAPI /api/upload） */
export async function uploadDocument(file: File): Promise<{ chunks: number }> {
  const form = new FormData()
  form.append('file', file)
  const { data } = await client.post('/upload', form)
  return data
}

export type ChatStreamEvent =
  | { type: 'meta'; citations: Citation[] }
  | { type: 'delta'; text: string }
  | { type: 'done' }
  | { type: 'error'; message: string }

/** 多轮问答，以 SSE 流式返回答案与引用（对接 FastAPI /api/chat） */
export async function streamChat(
  question: string,
  history: HistoryItem[],
  onEvent: (event: ChatStreamEvent) => void,
): Promise<void> {
  const res = await fetch('/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Accept: 'text/event-stream' },
    body: JSON.stringify({ question, history }),
  })
  if (!res.ok) {
    let detail = res.statusText || '请求失败'
    try {
      const data = (await res.json()) as { detail?: unknown }
      if (typeof data.detail === 'string' && data.detail.trim()) detail = data.detail
    } catch {
      /* 非 JSON 错误体时沿用状态文本 */
    }
    throw new Error(detail)
  }
  if (!res.body) throw new Error('浏览器不支持流式响应')

  const reader = res.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  try {
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true }).replace(/\r\n/g, '\n')
      const parts = buffer.split('\n\n')
      buffer = parts.pop() ?? ''
      for (const part of parts) {
        const data = part
          .split('\n')
          .filter((line) => line.startsWith('data:'))
          .map((line) => line.slice(5).trim())
          .join('\n')
        if (!data) continue
        onEvent(JSON.parse(data) as ChatStreamEvent)
      }
    }
  } finally {
    reader.releaseLock()
  }
}
