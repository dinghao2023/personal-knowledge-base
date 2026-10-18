<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { listDocuments, uploadDocument } from '@/api/client'

interface DocItem {
  name: string
  size: string
  chunks?: number
  uploadedAt: string
}

const docs = ref<DocItem[]>([])
const uploading = ref(false)
const loading = ref(true)
const error = ref('')

function toDocItem(file: { filename: string; size: number; chunks: number; uploaded_at: string }): DocItem {
  const uploaded = new Date(file.uploaded_at)
  return {
    name: file.filename,
    size: formatSize(file.size),
    chunks: file.chunks,
    uploadedAt: Number.isNaN(uploaded.getTime()) ? file.uploaded_at : uploaded.toLocaleString(),
  }
}

async function loadDocuments() {
  const res = await listDocuments()
  docs.value = res.files.map(toDocItem)
}

function formatSize(bytes: number): string {
  if (bytes >= 1024 * 1024) return (bytes / 1024 / 1024).toFixed(1) + ' MB'
  if (bytes >= 1024) return (bytes / 1024).toFixed(0) + ' KB'
  return bytes + ' B'
}

async function onFileChange(e: Event) {
  const target = e.target as HTMLInputElement
  const file = target.files?.[0]
  if (!file) return

  uploading.value = true
  error.value = ''
  try {
    await uploadDocument(file)
    await loadDocuments()
  } catch (err) {
    error.value = '上传失败：' + (err instanceof Error ? err.message : String(err))
  } finally {
    uploading.value = false
    target.value = ''
  }
}

onMounted(async () => {
  try {
    await loadDocuments()
  } catch (err) {
    error.value = '读取文档列表失败：' + (err instanceof Error ? err.message : String(err))
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="docs">
    <header class="docs-head">
      <h1>知识库文档</h1>
      <label class="upload-btn" :class="{ disabled: uploading }">
        {{ uploading ? '入库中…' : '上传文档' }}
        <input
          type="file"
          accept=".pdf,.docx,.md,.txt"
          :disabled="uploading"
          @change="onFileChange"
        />
      </label>
    </header>

    <p v-if="error" class="error">{{ error }}</p>
    <p class="hint">支持 PDF / DOCX / Markdown / TXT，上传后自动解析、分块并入库。</p>

    <div v-if="loading" class="empty">正在读取已有文档…</div>
    <div v-else-if="docs.length === 0" class="empty">
      还没有文档。上传第一份资料开始构建你的知识库。
    </div>

    <ul v-else class="doc-list">
      <li v-for="(d, i) in docs" :key="i" class="doc-item">
        <div class="doc-icon">📄</div>
        <div class="doc-info">
          <div class="doc-name">{{ d.name }}</div>
          <div class="doc-meta">
            {{ d.size }}
            <template v-if="d.chunks !== undefined"> · {{ d.chunks }} 个分块</template>
            · {{ d.uploadedAt }}
          </div>
        </div>
      </li>
    </ul>
  </div>
</template>

<style scoped>
.docs {
  height: 100%;
  max-width: 860px;
  margin: 0 auto;
  padding: 20px 24px;
}

.docs-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-bottom: 14px;
  border-bottom: 1px solid var(--border);
}

.docs-head h1 {
  margin: 0;
  font-size: 20px;
}

.upload-btn {
  background: var(--accent);
  color: #fff;
  padding: 9px 18px;
  border-radius: var(--radius);
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
}

.upload-btn.disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.upload-btn input {
  display: none;
}

.hint {
  font-size: 13px;
  color: var(--muted);
}

.error {
  color: var(--danger);
  font-size: 13px;
}

.empty {
  margin-top: 60px;
  text-align: center;
  color: var(--muted);
}

.doc-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.doc-item {
  display: flex;
  align-items: center;
  gap: 12px;
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 12px 14px;
  box-shadow: var(--shadow);
}

.doc-icon {
  font-size: 22px;
}

.doc-name {
  font-weight: 600;
}

.doc-meta {
  font-size: 12px;
  color: var(--muted);
}
</style>
