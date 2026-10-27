import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import type { Citation } from '@/api/client'

export interface Message {
  role: 'user' | 'assistant'
  content: string
  citations?: Citation[]
  loading?: boolean
}

export interface Conversation {
  id: string
  title: string
  draft: string
  messages: Message[]
}

function createConversation(): Conversation {
  return {
    id: crypto.randomUUID(),
    title: '新对话',
    draft: '',
    messages: [],
  }
}

export const useChatStore = defineStore('chat', () => {
  const conversations = ref<Conversation[]>([createConversation()])
  const activeId = ref(conversations.value[0].id)
  const pendingIds = ref<string[]>([])

  const active = computed(() => {
    return conversations.value.find((c) => c.id === activeId.value) ?? conversations.value[0]
  })

  function startNewConversation() {
    const blank = conversations.value.find((c) => c.messages.length === 0)
    if (blank) {
      activeId.value = blank.id
      return
    }
    const conv = createConversation()
    conversations.value.unshift(conv)
    activeId.value = conv.id
  }

  function selectConversation(id: string) {
    if (id === activeId.value) return
    activeId.value = id
  }

  return {
    conversations,
    activeId,
    pendingIds,
    active,
    startNewConversation,
    selectConversation,
  }
})
