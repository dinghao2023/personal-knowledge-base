# Knyx — 个人知识库 RAG Agent（前端）

Vue 3 + Vite + TypeScript 前端，配套 FastAPI 后端。
后端代码位于backend文件夹内。

## 技术栈

- Vue 3（Composition API / `<script setup>`）
- Vite 6
- TypeScript
- Vue Router 4
- Pinia 2
- Axios

## 目录结构

```
src/
├── api/client.ts        # 后端接口封装（上传 / 多轮问答 / 引用）
├── router/index.ts      # 路由：/chat 对话、/documents 知识库
├── views/
│   ├── ChatView.vue     # 对话页（多轮 + 引用溯源展示）
│   └── DocumentsView.vue# 知识库页（文档上传与列表）
├── App.vue              # 侧边栏布局
└── style.css            # 全局样式
```

## 开发

```bash
npm install
npm run dev      # http://localhost:5173
```

## 构建

```bash
npm run build
```

## 后端联调

Vite 开发代理将 `/api` 转发到 `http://localhost:8000`（FastAPI）。后端需提供：

- `POST /api/upload`：上传文档（multipart，字段名 `file`），返回 `{ chunks: number }`
- `POST /api/chat`：多轮问答，请求 `{ question, history }`，返回 `{ answer, citations }`
  - `citations: [{ source, page?, snippet }]`
