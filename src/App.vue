<script setup lang="ts">
import { useRoute, useRouter } from 'vue-router'
import { useChatStore } from '@/stores/chat'

const route = useRoute()
const router = useRouter()
const chat = useChatStore()

const navItems = [
  { path: '/chat', label: '对话', icon: '💬' },
  { path: '/documents', label: '知识库', icon: '📚' },
]

function openConversation(id: string) {
  chat.selectConversation(id)
  if (route.path !== '/chat') router.push('/chat')
}
</script>

<template>
  <div class="shell">
    <aside class="sidebar">
      <div class="brand">
        <span class="logo">K</span>
        <div>
          <div class="brand-name">Knyx</div>
          <div class="brand-sub">个人知识库</div>
        </div>
      </div>
      <nav class="nav">
        <router-link
          v-for="item in navItems"
          :key="item.path"
          :to="item.path"
          class="nav-item"
          :class="{ active: route.path === item.path }"
        >
          <span class="nav-icon">{{ item.icon }}</span>
          {{ item.label }}
        </router-link>
      </nav>
      <div class="conv-list">
        <button
          v-for="c in chat.conversations"
          :key="c.id"
          type="button"
          class="conv-item"
          :class="{ active: c.id === chat.activeId && route.path === '/chat' }"
          @click="openConversation(c.id)"
        >
          <span class="conv-title">{{ c.title }}</span>
          <span v-if="chat.pendingIds.includes(c.id)" class="conv-pending">思考中</span>
        </button>
      </div>
      <div class="sidebar-foot">RAG Agent · v0.1</div>
    </aside>

    <main class="main">
      <router-view v-slot="{ Component }">
        <KeepAlive>
          <component :is="Component" />
        </KeepAlive>
      </router-view>
    </main>
  </div>
</template>

<style scoped>
.shell {
  display: flex;
  height: 100%;
}

.sidebar {
  width: 220px;
  flex-shrink: 0;
  background: #ffffff;
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  padding: 18px 14px;
  min-height: 0;
}

.brand {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 0 6px 18px;
}

.logo {
  width: 36px;
  height: 36px;
  border-radius: 9px;
  background: var(--accent);
  color: #fff;
  font-weight: 700;
  font-size: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.brand-name {
  font-weight: 700;
  font-size: 16px;
}

.brand-sub {
  font-size: 12px;
  color: var(--muted);
}

.nav {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.conv-list {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-top: 14px;
}

.conv-item {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  text-align: left;
  padding: 8px 12px;
  border-radius: 8px;
  color: var(--text);
  font-size: 13px;
}

.conv-item:hover {
  background: var(--bg);
}

.conv-item.active {
  background: var(--accent-soft);
  color: var(--accent);
}

.conv-title {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.conv-pending {
  flex-shrink: 0;
  font-size: 11px;
  color: var(--muted);
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 8px;
  color: var(--text);
  font-weight: 500;
  transition: background 0.15s, color 0.15s;
}

.nav-item:hover {
  background: var(--bg);
}

.nav-item.active {
  background: var(--accent-soft);
  color: var(--accent);
}

.nav-icon {
  font-size: 15px;
}

.sidebar-foot {
  font-size: 11px;
  color: var(--muted);
  padding: 0 6px;
}

.main {
  flex: 1;
  min-width: 0;
  overflow: hidden;
}
</style>
