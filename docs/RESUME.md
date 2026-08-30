# 简历项目描述模板

下面三档描述分别对应不同场景：**GitHub 仓库 description（≤120 字符）/ 简历项目栏（一两行）/ 自我介绍 / 面试展开讲**。

---

## 短描述（一行）

适合：GitHub About 区的 description、简历项目栏、邮件签名档。

> **AI 聊天助手** | FastAPI + 通义千问 Qwen + MySQL | 多用户隔离、JWT 鉴权、SSE 流式、上下文记忆、完整 REST API | github.com/23iho/ai-chat-assistant

英文版（外企或国际平台）：
> Multi-user AI chat service | FastAPI + Qwen + MySQL | JWT auth, SSE streaming, persistent context memory, conversation mgmt

---

## 中描述（一段，适合简历详细描述栏）

> **AI 聊天助手 · 多用户对话服务** ｜ 个人项目 ｜ Python / FastAPI / MySQL / 通义千问 Qwen / DashScope
>
> **背景**：解决 LLM Demo 普遍存在的三大工程问题 —— 刷新丢上下文、多人共用一份记忆、API Key 前端裸奔。独立设计并实现了一套可上线的多用户 AI 对话后端服务，前端原生 HTML/JS。
>
> **核心亮点**：
> - **混合式上下文记忆**：进程内 20 轮滑动窗口（LRU 上限 1000）+ MySQL 持久化回填；热路径零 IO，重启后 < 100ms 自动重建
> - **JWT 鉴权横切**：基于 `Depends(get_current_user)` 实现鉴权横切；所有数据访问以 `user_id` 为强制过滤条件；bcrypt 加盐哈希
> - **统一 REST API 契约**：8 个端点统一 `{code, message, data}` 响应，Pydantic 入参校验，自动 Swagger/ReDoc
> - **SSE 流式输出**：用 `StreamingResponse` + 客户端 `ReadableStream` 实现打字机效果，首字延迟从 3-10s 降到 < 500ms，支持中途停止
> - **多会话管理**：用户可建多个独立会话，互不串台，带新建/重命名/删除/级联清理
>
> **工程规范**：连接池预检 (`pool_pre_ping`)、自动 schema 演进（启动时补缺失列与索引）、统一异常处理、可观测性 hooks。
>
> **技术反思**：主动识别方案的三处局限 —— (1) 进程内缓存多 worker 命中率下降，正确解法是迁 Redis；(2) JWT 无主动失效，规划 jti + 黑名单；(3) 缺少限流，正在集成 slowapi。

---

## 长描述（自我介绍 / 面试展开讲）

> **AI Chat Assistant — Multi-tenant LLM Chat Service**
> 个人项目 ｜ FastAPI · SQLAlchemy · MySQL · JWT · DashScope/Qwen
> 源码：github.com/23iho/ai-chat-assistant
>
> ---
>
> **项目背景**：为解决 LLM Demo 普遍存在的三大工程问题（刷新丢上下文、多人共用一份记忆、API Key 前端裸奔），独立设计并实现了一套可上线的多用户 AI 对话服务。前后端分离，后端约 1500 行 Python，前端原生 HTML/JS（无框架依赖），覆盖注册 / 登录 / 多会话 / 流式聊天 / 历史 CRUD 全链路。
>
> **核心技术亮点**：
>
> 1. **混合式上下文记忆**：设计"进程内滑动窗口 + 数据库回填"方案。LRU 上限 1000 个 (用户, 会话) 元组防止 OOM；DB 回填走 `(user_id, conversation_id)` 复合索引，单次查询 < 100ms；固定窗口长度把单次请求 token 消耗稳定在模型上限内。重启后自动重建，不丢上下文。
>
> 2. **JWT 鉴权横切**：基于 FastAPI 的 `Depends(get_current_user)` 依赖注入实现鉴权横切，业务函数第一行即拿到可信 `user_id`；所有数据访问层以 `user_id` 为强制过滤条件（CRUD 函数签名必传 `user_id`），从架构层面杜绝越权读写；密码用 bcrypt 加盐哈希存储。
>
> 3. **统一 REST API 契约**：所有端点统一 `{code, message, data}` 三段式响应信封，HTTP 状态码遵循 REST 语义（401/404/500）；Pydantic 入参校验；FastAPI 自动生成 OpenAPI/Swagger/ReDoc 文档。
>
> 4. **SSE 流式输出**：用 `StreamingResponse(media_type="text/event-stream")` 把 DashScope 的 `stream=True` 生成器推到前端，前端用 `ReadableStream` + `TextDecoder` 解析逐 token 渲染；首字延迟从 3-10s 降到 < 500ms；`AbortController` 实现中途"停止生成"。
>
> 5. **多会话管理**：`Conversation` 表 + `ChatRecord.conversation_id` 外键 + `relationship(cascade='all, delete-orphan')`；用户可建多个独立会话，互不串台；新建/重命名/删除/级联清理消息；会话被使用时刷新 `updated_at`，活跃会话自动排到列表最前。
>
> **工程化基建**：
> - 连接池：`pool_pre_ping=True` + `pool_recycle=3600`，避免拿到 MySQL `wait_timeout` 切断的连接
> - 自动 schema 演进：`ensure_schema()` 启动时检查并补缺失列与索引（轻量级方案，破坏性变更留给 Alembic）
> - 错误处理：分层异常体系（HTTPException 走 FastAPI 内置 handler，未知异常走 global handler 兜底）
> - 数据校验：Pydantic `Annotated[str, StringConstraints(min_length=3, max_length=20)]` 等
>
> **技术反思与演进路径**（这一节体现"我知道自己不知道什么"，是简历最强信号）：
> 1. 进程内 `UserContextCache` 在 `--workers > 1` 下命中率会下降 → 正确解法是迁 Redis Hash + TTL
> 2. JWT 无法主动失效（登出只是前端删 token）→ 规划 jti + Redis 黑名单 + Refresh Token
> 3. 公网部署缺少限流，API Key 有被刷爆风险 → 规划 slowapi + Redis 令牌桶 + 每日 token 配额
> 4. SSE 中途断流时最后一段 AI 文本可能未落库 → 规划客户端心跳 + 服务端最终一致性写入
>
> **可讲的技术故事**（面试 STAR 浓缩）：
>
> - **故事一：上下文污染 Bug**
>   早期把 `chat_history.append()` 写在 `ai_service` 内部，AI 调用失败时脏消息也被追加进上下文，导致后续对话越来越偏。定位后重构为传入副本 `messages = chat_history + [...]`，状态收归 `main.py` 单一管理。**这是我从"能跑就行"到"理解单一数据源"的转折点**。
>
> - **故事二：记忆存内存还是数据库的权衡**
>   在"纯内存"（重启即丢、零 IO）和"纯数据库"（重启无忧、每轮多一次查询）之间反复纠结，最终选了混合方案 —— 热路径零 IO，冷路径回填。**这是我第一次真正体会到缓存设计里"命中率 / 一致性 / 重启成本"的三角约束**，也知道它的边界：多 worker 下命中率下降，正确解法是 Redis。
>
> - **故事三：异常处理的取舍**
>   一开始为了前端好解析，全局异常统一返回 HTTP 200 + 业务 code。后来意识到这破坏了 REST 语义，让 CDN / 网关 / 监控 / 前端 `response.ok` 全部失效。改为语义化状态码 + 业务码双通道。**这个反模式反而成了成长证据** —— 我能说清当初为什么那么写、现在为什么改了。
>
> ---
>
> **仓库亮点**（简历项目栏可附）：
> - MIT License
> - 13 个端点、1500+ 行 Python、600+ 行前端 JS
> - 完整 README（架构图、API 示例、已知限制、路线图）
> - 启动后自动建表 + 自动补齐缺失列

---

## 📝 简历使用建议

### 三条红线

1. **简历吹"高并发 / 企业级"但代码里 `user_chat_history` 是普通 dict** —— 会被当场拆穿
2. **简历链接过去 README 跑不起来 / 缺 LICENSE / 最后提交三个月前** —— 印象分直接扣光
3. **描述里只有技术栈名词（FastAPI、JWT、SQLAlchemy）没有动词和结果** —— 和一百份雷同简历没区别

### 投递前必修的两个代码问题（都已经修了）

✅ `main.py` 登录接口的异常处理顺序（HTTPException 被吞成 200）
✅ 全局异常处理器返回 HTTP 200（违反 REST 语义）

修完后这两处都进了 README "已知限制"，从扣分项变成加分项。

### 投递前要做的两件事

1. **录一个 15-20 秒的 Demo GIF**（注册 → 登录 → 多轮流式对话 → 切会话 → 刷新页面记录仍在）
2. **填 GitHub 仓库 topics**（`fastapi` / `qwen` / `dashscope` / `chatbot` / `jwt` / `mysql` / `sse` / `streaming`）

### 让数字说话

下面这些是项目里能挖出来的真实数字，挑 1-2 个放到简历上：

| 数字 | 来源 | 简历话术 |
|------|------|----------|
| 13 个 API 端点 | OpenAPI 自动生成 | "完整 REST API 设计，13 个端点统一响应契约" |
| ~1500 行 Python | `cloc backend/` | "独立完成 ~1500 行后端代码" |
| ~600 行前端 JS | `cloc frontend/` | "原生 JS 实现无依赖单页应用" |
| 首字延迟从 3-10s 降到 <500ms | 实测 | "SSE 流式输出，首字延迟降低 ~90%" |
| 1000 个 (user, conv) LRU 上限 | UserContextCache.MAX_KEYS | "进程内有界 LRU 缓存，防止 OOM" |
| 20 轮滑动窗口 | max_window=20 | "固定 20 轮上下文窗口" |
| 0 次 SQL 全表扫描 | 复合索引 + DESC LIMIT | "所有查询走索引，单会话查询 < 100ms" |

只写真实数字，不要编"支撑 10 万 QPS"这种面试官一追问就崩的话。
