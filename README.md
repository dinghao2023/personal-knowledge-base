# Knyx — 个人知识库 RAG Agent（前端）

Vue 3 前端负责上传和多轮对话。FastAPI 后端负责解析、分块、向量检索和带引用的生成。知识存在本地 Chroma 的集合 `knyx`，没有账号，也没有多库隔离。后端说明见 [backend/README.md](backend/README.md)。

开发时两个进程一起开：Vite `http://localhost:5173`，FastAPI `http://localhost:8000`。页面只请求 `/api`，由 Vite 代理转到后端。

## 技术栈

- Vue 3（Composition API / `<script setup>`）
- Vite 6
- TypeScript
- Vue Router 4
- Pinia 2（已在 `main.ts` 挂载，当前没有 store）
- Axios
- marked + DOMPurify（助手回复按 Markdown 渲染）

## 页面

侧边栏两项，定义在 `src/App.vue`：

| 路径 | 页面 | 做什么 |
| --- | --- | --- |
| `/` | 重定向到 `/chat` | |
| `/chat` | 对话 | 多轮提问，渲染答案，列出引用来源 |
| `/documents` | 知识库 | 上传文件，展示已落盘文档 |

`router-view` 包在 `KeepAlive` 里。同一次打开中，在「对话」和「知识库」之间切换，消息和文档列表都还在。刷新页面后，对话消息清空；知识库页会重新请求文件列表。

## 目录结构

```
src/
├── api/client.ts         # Axios 封装：上传、文件列表、多轮问答
├── router/index.ts       # 路由：/chat、/documents
├── views/
│   ├── ChatView.vue      # 对话页
│   └── DocumentsView.vue # 知识库页
├── App.vue               # 侧边栏 + KeepAlive
├── main.ts               # 挂载 Pinia 与路由
└── style.css             # 全局样式
```

`vite.config.ts` 把 `@` 指到 `src`，开发服务器端口 `5173`，并把 `/api` 代理到 `http://localhost:8000`。

## 前端调用的接口

封装都在 `src/api/client.ts`。`baseURL` 为 `/api`，超时 120 秒。

| 方法 | 路径 | 前端函数 | 页面怎么用 |
| --- | --- | --- | --- |
| GET | `/api/documents` | `listDocuments` | 进入知识库页、上传成功后刷新列表 |
| POST | `/api/upload` | `uploadDocument` | 字段名 `file`，返回 `{ chunks }` |
| POST | `/api/chat` | `sendChat` | 入参 `{ question, history }`，返回 `{ answer, citations }` |

`GET /api/documents` 的每一项是 `{ filename, size, chunks, uploaded_at }`。页面把字节数格式化成 B / KB / MB，把时间格式化成本地时间，并显示分块数。

`citations` 的每一项是 `{ source, page?, snippet }`。对话页只渲染 `source` 和页码（`p页码`），不展示 `snippet`。Markdown 文件的页码在后端是 `0`，到前端会变成空，所以这类引用不显示页码。

## 入库链路

知识库页选文件后的顺序：

选文件 → `POST /api/upload` → 成功后再 `GET /api/documents`

可选扩展名是 `.pdf`、`.docx`、`.md`、`.txt`。上传过程中按钮显示「入库中…」。成功后列表以服务端返回为准，包含文件名、大小、分块数和修改时间。失败时在页面上显示 `上传失败：` 加上错误信息。

后端收到文件后会落盘、解析、分块、向量化，再写入集合 `knyx`。这一段的字段和存放位置见 [backend/README.md](backend/README.md)。

## 问答链路

对话页发送后的顺序：

当前问题 → 带上此前消息 → `POST /api/chat` → 助手气泡渲染 Markdown → 列出引用来源

`submit` 里各步的实际数据是：

1. 当前输入去掉首尾空白后推进消息列表，角色为 `user`。输入框随即清空。
2. 再推进一条 `loading: true` 的助手消息，气泡显示「思考中…」。发送按钮禁用。
3. `history` 取已有消息里去掉这条加载中消息、再去掉刚发送的这一问之后的内容。也就是更早的用户问题和助手回答，按原样作为 `{ role, content }` 提交。
4. 返回后，加载中的那条消息写入 `answer` 和 `citations`。
5. 助手内容用 `marked` 解析（GFM、保留换行），再用 DOMPurify 消毒后渲染。用户消息保持纯文本。
6. 引用来源按返回顺序编号 `[1]`、`[2]`…，显示文件名；有页码时再显示 `p页码`。

Enter 发送，Shift+Enter 换行。请求失败时，这条助手消息改成 `请求失败：` 加上 Axios 的 `message`。

后端检索只用这一次的 `question`，历史只参与生成。默认召回 4 条，相似度低于 0.5 的块会被丢掉。没有命中时接口直接返回固定说明，`citations` 为空数组，页面上就只有这段文字、没有引用来源。默认参数和检索细节见后端 `config.py`、`retrieve.py`、`chat.py`。

## 模块

| 位置 | 职责 |
| --- | --- |
| `src/App.vue` | 侧边栏；`KeepAlive` 保住两个页面的本次会话状态 |
| `src/views/ChatView.vue` | 消息列表、Enter 发送、Markdown 答案、引用序号 |
| `src/views/DocumentsView.vue` | 选文件上传；进入页面时拉取已有文件 |
| `src/api/client.ts` | 三个接口的类型和请求 |
| `src/router/index.ts` | `/` 转到 `/chat`，并设置页签标题 |
| `backend/app/main.py` | 路由、格式校验、把 `RuntimeError` 转成 500 |

## 页面上能看到的状态

| 环节 | 现状 | 结果 |
| --- | --- | --- |
| 侧边栏切换 | `KeepAlive` 保留两个页面组件 | 切走再切回，对话和文档列表还在 |
| 刷新 | 对话消息只在组件的 `ref` 里 | 刷新后对话清空；知识库会重新请求列表 |
| 文档列表 | 来自 `GET /api/documents`，数据在 `docs/` 和集合分块数 | 列表能对上已落盘文件；分块数为 0 表示该文件还没有可检索内容 |
| 回到知识库页 | `onMounted` 只在组件第一次挂载时请求 | 同一次打开中从对话切回知识库，不会自动再拉一次列表 |
| 引用 | 接口带回全部命中和 `snippet` | 页面只显示文件名和页码，不显示片段 |
| 答案格式 | 助手消息走 Markdown | `**文字**` 会加粗；用户输入仍按原文显示 |
| 请求错误 | 页面使用 Axios 的 `message` | FastAPI 返回的 `detail` 不一定出现在气泡里 |

向量和原文分别在 `backend/chroma_db` 与 `backend/docs`。刷新后对话消失，不影响已经入库的文件。

## 开发

```bash
npm install
npm run dev      # http://localhost:5173
```

后端需先在 `backend` 目录启动，见 [backend/README.md](backend/README.md)。

## 构建

```bash
npm run build
npm run typecheck
```
