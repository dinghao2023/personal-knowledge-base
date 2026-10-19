<script setup lang="ts">
import { useRoute } from 'vue-router'

const route = useRoute()

const navItems = [
  { path: '/chat', label: '对话', icon: '💬' },
  { path: '/documents', label: '知识库', icon: '📚' },
]
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
  flex: 1;
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
