<script setup lang="ts">
import { computed, nextTick, ref, watch } from 'vue'
import DOMPurify from 'dompurify'
import { marked } from 'marked'
import { sendChat, type HistoryItem } from '@/api/client'
import { useChatStore, type Message } from '@/stores/chat'

const chat = useChatStore()
const listEl = ref<HTMLElement | null>(null)

const active = computed(() => chat.active)
const sending = computed(() => chat.pendingIds.includes(active.value.id))

const input = computed({
  get: () => active.value.draft,
  set: (value: string) => {
    active.value.draft = value
  },
})

function renderMarkdown(source: string): string {
  const html = marked.parse(source, { async: false, gfm: true, breaks: true })
  return DOMPurify.sanitize(html)
}

function scrollToBottom() {
  nextTick(() => {
    if (listEl.value) listEl.value.scrollTop = listEl.value.scrollHeight
  })
}

function startNewConversation() {
  chat.startNewConversation()
  scrollToBottom()
}

watch(() => chat.activeId, () => scrollToBottom())

async function submit() {
  const conv = active.value
  const text = conv.draft.trim()
  if (!text || chat.pendingIds.includes(conv.id)) return

  conv.draft = ''
  conv.messages.push({ role: 'user', content: text })
  if (conv.messages.filter((m) => m.role === 'user').length === 1) {
    conv.title = text.length > 16 ? text.slice(0, 16) + '…' : text
  }
  const loadingMsg: Message = { role: 'assistant', content: '', loading: true }
  conv.messages.push(loadingMsg)
  chat.pendingIds = [...chat.pendingIds, conv.id]
  scrollToBottom()

  const history: HistoryItem[] = conv.messages
    .filter((m) => !m.loading && m.content)
    .slice(0, -1)
    .map((m) => ({ role: m.role, content: m.content }))

  try {
    const res = await sendChat(text, history)
    loadingMsg.content = res.answer
    loadingMsg.citations = res.citations
    loadingMsg.loading = false
  } catch (e) {
    loadingMsg.loading = false
    loadingMsg.content = '请求失败：' + (e instanceof Error ? e.message : String(e))
  } finally {
    chat.pendingIds = chat.pendingIds.filter((id) => id !== conv.id)
    if (chat.activeId === conv.id) scrollToBottom()
  }
}
</script>

<template>
  <div class="chat">
    <header class="chat-head">
      <div>
        <h1>与知识库对话</h1>
        <span class="tip">回答基于已入库文档，支持引用溯源</span>
      </div>
      <button class="new-icon" type="button" title="新建" aria-label="新建" @click="startNewConversation">
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path d="M12 5v14M5 12h14" />
        </svg>
      </button>
    </header>

    <div ref="listEl" class="msg-list">
      <div v-if="active.messages.length === 0" class="empty">
        <p>上传文档后，在这里提问。</p>
        <p class="empty-sub">例如：这个项目的架构是怎样的？</p>
      </div>

      <div
        v-for="(m, i) in active.messages"
        :key="i"
        class="msg-row"
        :class="m.role"
      >
        <div class="avatar">{{ m.role === 'user' ? '我' : 'K' }}</div>
        <div class="bubble">
          <div v-if="m.loading" class="typing">思考中…</div>
          <template v-else>
            <div
              v-if="m.role === 'assistant'"
              class="content markdown"
              v-html="renderMarkdown(m.content)"
            ></div>
            <div v-else class="content">{{ m.content }}</div>
            <div v-if="m.citations && m.citations.length" class="citations">
              <div class="cit-title">引用来源</div>
              <div
                v-for="(c, ci) in m.citations"
                :key="ci"
                class="cit-item"
              >
                <span class="cit-badge">[{{ ci + 1 }}]</span>
                <span class="cit-source">{{ c.source }}</span>
                <span v-if="c.page" class="cit-page">p{{ c.page }}</span>
              </div>
            </div>
          </template>
        </div>
      </div>
    </div>

    <footer class="composer">
      <textarea
        v-model="input"
        rows="1"
        placeholder="输入问题，Enter 发送 / Shift+Enter 换行"
        @keydown.enter.exact.prevent="submit"
      ></textarea>
      <button :disabled="sending || !input.trim()" @click="submit">
        {{ sending ? '…' : '发送' }}
      </button>
    </footer>
  </div>
</template>

<style scoped>
.chat {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-width: 0;
  padding: 20px 24px;
  width: 100%;
}

.chat-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  padding-bottom: 14px;
  border-bottom: 1px solid var(--border);
}

.new-icon {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  color: var(--text);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.new-icon svg {
  width: 18px;
  height: 18px;
  fill: none;
  stroke: currentColor;
  stroke-width: 2;
  stroke-linecap: round;
}

.new-icon:hover {
  background: var(--bg);
  color: var(--accent);
}

.chat-head h1 {
  margin: 0;
  font-size: 20px;
}

.tip {
  font-size: 12px;
  color: var(--muted);
}

.msg-list {
  flex: 1;
  overflow-y: auto;
  padding: 18px 0;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.empty {
  margin: auto;
  text-align: center;
  color: var(--muted);
}

.empty-sub {
  font-size: 13px;
}

.msg-row {
  display: flex;
  gap: 10px;
}

.msg-row.user {
  flex-direction: row-reverse;
}

.avatar {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  font-weight: 600;
  color: #fff;
}

.user .avatar {
  background: #1f2937;
}

.assistant .avatar {
  background: var(--accent);
}

.bubble {
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 10px 14px;
  max-width: 78%;
  box-shadow: var(--shadow);
}

.user .bubble {
  background: var(--accent-soft);
}

.content {
  white-space: pre-wrap;
  word-break: break-word;
}

.markdown {
  white-space: normal;
}

.markdown :deep(p) {
  margin: 0 0 0.65em;
}

.markdown :deep(p:last-child) {
  margin-bottom: 0;
}

.markdown :deep(ul),
.markdown :deep(ol) {
  margin: 0.3em 0 0.7em;
  padding-left: 1.4em;
}

.markdown :deep(li) {
  margin: 0.15em 0;
}

.markdown :deep(strong) {
  font-weight: 650;
}

.markdown :deep(code) {
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  font-size: 0.92em;
  background: var(--bg);
  padding: 0.1em 0.35em;
  border-radius: 4px;
}

.markdown :deep(pre) {
  overflow-x: auto;
  background: var(--bg);
  padding: 10px 12px;
  border-radius: 8px;
  margin: 0.4em 0 0.7em;
}

.markdown :deep(pre code) {
  background: none;
  padding: 0;
}

.typing {
  color: var(--muted);
}

.citations {
  margin-top: 10px;
  padding-top: 8px;
  border-top: 1px dashed var(--border);
}

.cit-title {
  font-size: 12px;
  color: var(--muted);
  margin-bottom: 4px;
}

.cit-item {
  display: flex;
  gap: 6px;
  font-size: 12px;
  align-items: baseline;
}

.cit-badge {
  color: var(--accent);
  font-weight: 600;
}

.cit-source {
  color: var(--text);
  word-break: break-all;
}

.cit-page {
  color: var(--muted);
}

.composer {
  display: flex;
  gap: 10px;
  padding-top: 14px;
}

.composer textarea {
  flex: 1;
  resize: none;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 12px 14px;
  font-size: 14px;
  line-height: 1.5;
  outline: none;
}

.composer textarea:focus {
  border-color: var(--accent);
}

.composer button {
  background: var(--accent);
  color: #fff;
  border-radius: var(--radius);
  padding: 0 22px;
  font-size: 14px;
  font-weight: 600;
}

.composer button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
