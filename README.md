# AI聊天助手

基于 FastAPI、SQLAlchemy 和阿里云通义千问（Qwen）构建的 AI 聊天助手服务，支持用户认证、数据库持久化存储聊天记录。

## 📋 项目简介

本项目是一个功能完整的 AI 聊天助手后端服务，使用 FastAPI 框架构建 RESTful API，集成阿里云 DashScope SDK 调用通义千问大语言模型，并通过 MySQL 数据库实现聊天记录的持久化存储和查询。系统支持用户注册登录、JWT Token 认证、多用户隔离的聊天历史记录管理。

## ✨ 主要特性

- 🚀 **快速启动**：基于 FastAPI，高性能异步 Web 框架
- 💬 **智能对话**：集成通义千问 Qwen2.5-3B-Instruct 模型
- 🧠 **上下文记忆**：支持多轮对话，保持对话连贯性
- 🔐 **用户认证**：支持用户注册、登录，JWT Token 认证
- 👥 **多用户隔离**：每个用户的聊天记录独立存储和管理
- 💾 **数据持久化**：使用 MySQL 数据库存储用户信息和聊天记录
- 🔍 **历史查询**：提供聊天记录查询和删除接口
- 🔄 **热重载**：开发模式下支持代码自动重载
- 📖 **自动文档**：FastAPI 自动生成 Swagger UI 和 ReDoc 文档
- 🔑 **OAuth2 标准**：支持 Swagger UI OAuth2 认证流程
- 🔐 **环境变量管理**：使用 python-dotenv 安全管理配置信息

## 🛠️ 技术栈

- **Web 框架**：FastAPI 0.135.3
- **ASGI 服务器**：Uvicorn 0.44.0
- **AI 服务**：阿里云 DashScope SDK 1.25.16
- **AI 模型**：通义千问 qwen2.5-3b-instruct
- **数据库 ORM**：SQLAlchemy 2.0.49
- **数据库驱动**：PyMySQL 1.1.2
- **认证加密**：python-jose (JWT), passlib + bcrypt (密码加密)
- **环境管理**：python-dotenv 1.2.2
- **Python 版本**：建议 Python 3.8+

## 📦 安装步骤

### 1. 克隆项目

```bash
git clone <your-repository-url>
cd ai-chat-assistant
```

### 2. 创建虚拟环境

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 配置环境变量

复制环境变量示例文件并重命名：

```bash
# Windows
copy .env.example .env

# Linux/Mac
cp .env.example .env
```

编辑 `.env` 文件，添加以下配置：

```env
# 阿里云 DashScope API 密钥
DASH_SCOPE_API_KEY=your_api_key_here

# Qwen 模型名称
QWEN_MODEL=qwen2.5-3b-instruct

# MySQL 数据库配置
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=ai_chat_db

# JWT 认证配置
JWT_SECRET=your_secret_key_here
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=1440
```

> 💡 **获取 API Key**：访问 [阿里云 DashScope 控制台](https://dashscope.console.aliyun.com/) 注册并获取 API 密钥  
> 🔑 **JWT Secret**：建议使用随机生成的强密码作为 JWT 密钥，确保安全性

### 5. 准备数据库

确保已安装 MySQL 数据库，并创建对应的数据库：

```sql
CREATE DATABASE ai_chat_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

首次运行程序时，会自动创建 `users` 和 `chat_records` 表。

## 🚀 运行服务

### 开发模式（推荐）

```bash
python main.py
```

服务将在 `http://127.0.0.1:8000` 启动，支持代码热重载。

### 生产模式

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

## 📖 API 文档

启动服务后，可以通过以下地址访问自动生成的 API 文档：

- **Swagger UI**：http://localhost:8000/docs
- **ReDoc**：http://localhost:8000/redoc

## 🔌 API 接口说明

### 健康检查

**请求：**
```http
GET /
```

**响应：**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "status": "ok",
    "message": "AI聊天助手服务已启动"
  }
}
```

---

### 🔐 用户注册

**请求：**
```http
POST /register
Content-Type: application/json

{
  "username": "testuser",
  "email": "test@example.com",
  "password": "123456"
}
```

**参数说明：**
- `username`（必填）：用户名，3-20个字符
- `email`（可选）：邮箱地址
- `password`（必填）：密码，6-100个字符

**响应：**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "user_id": 1,
    "username": "testuser",
    "create_time": "2024-01-01 12:00:00"
  }
}
```

---

### 🔑 用户登录

**请求：**
```http
POST /login
Content-Type: application/json

{
  "username": "testuser",
  "password": "123456"
}
```

**参数说明：**
- `username`（必填）：用户名
- `password`（必填）：密码

**响应：**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "expire_time": "2024-01-02 12:00:00"
  }
}
```

> 💡 **使用提示**：在 Swagger UI 中，点击右上角的 "Authorize" 按钮，输入用户名和密码进行认证，之后所有需要认证的接口会自动携带 Token。

---

### 👤 获取当前用户信息

**请求：**
```http
GET /users/me
Authorization: Bearer <your_token>
```

**响应：**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "user_id": 1,
    "username": "testuser",
    "email": "test@example.com"
  }
}
```

---

### 💬 GET 方式聊天（需登录）

**请求：**
```http
GET /chat?message=你好&clear_history=false
Authorization: Bearer <your_token>
```

**参数说明：**
- `message`（必填）：用户输入的消息
- `clear_history`（可选）：是否清空上下文，默认 false

**响应：**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "user": "你好",
    "ai": "你好！我是AI聊天助手..."
  }
}
```

---

### 💬 POST 方式聊天（需登录）

**请求：**
```http
POST /chat
Content-Type: application/json
Authorization: Bearer <your_token>

{
  "message": "你好，请介绍一下自己",
  "clear_history": false
}
```

**参数说明：**
- `message`（必填）：用户输入的消息，最大长度 1000 字符
- `clear_history`（可选）：是否清空上下文，默认 false

**响应：**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "user": "你好，请介绍一下自己",
    "assistant": "我是基于通义千问模型的AI聊天助手..."
  }
}
```

---

### 📜 查询聊天记录（需登录）

**请求：**
```http
GET /history?skip=0&limit=100
Authorization: Bearer <your_token>
```

**参数说明：**
- `skip`（可选）：跳过多少条记录，默认 0
- `limit`（可选）：最多返回多少条，默认 100

**响应：**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "user_id": 1,
    "total": 10,
    "history": [
      {
        "id": 1,
        "role": "user",
        "content": "你好",
        "create_time": "2024-01-01 12:00:00"
      },
      {
        "id": 2,
        "role": "assistant",
        "content": "你好！我是AI助手",
        "create_time": "2024-01-01 12:00:01"
      }
    ]
  }
}
```

---

### 🗑️ 删除聊天记录（需登录）

**请求：**
```http
DELETE /history
Authorization: Bearer <your_token>
```

**响应：**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "user_id": 1,
    "deleted_count": 10,
    "message": "已清空你的聊天记录"
  }
}
```

## 📁 项目结构

```
ai-chat-assistant/
├── main.py              # FastAPI 主程序入口，定义路由端点
├── ai_service.py        # AI 服务模块（调用通义千问）
├── database.py          # 数据库模块（SQLAlchemy ORM + 用户和聊天记录操作）
├── auth.py              # 认证模块（JWT Token 生成和验证）
├── requirements.txt     # Python 依赖包列表
├── .env                 # 环境变量配置文件（需自行创建）
├── .env.example         # 环境变量示例文件
├── .gitignore          # Git 忽略文件配置
└── README.md           # 项目说明文档
```

## 🔧 核心模块说明

### main.py
- 创建 FastAPI 应用实例
- 定义 API 路由端点（健康检查、用户注册/登录、聊天、历史记录查询/删除）
- 配置 OAuth2 安全方案和 Swagger UI 认证
- 配置全局异常处理
- 管理用户级别的聊天上下文

### auth.py
- JWT Token 生成和验证
- OAuth2PasswordBearer 认证方案
- 密码加密和验证（使用 passlib + bcrypt）
- 获取当前登录用户信息

### ai_service.py
- 封装通义千问 API 调用逻辑
- 管理对话上下文（chat_history）
- 支持清空上下文功能
- 提供错误处理和异常捕获

### database.py
- 配置 MySQL 数据库连接
- 定义 User 和 ChatRecord 数据模型
- 提供数据库会话管理
- 实现聊天记录的增删查操作
  - `save_and_record()`: 保存单条聊天记录
  - `get_chat_history()`: 查询用户聊天记录
  - `delete_chat_history()`: 删除指定用户的所有聊天记录

## ⚙️ 配置说明

### 环境变量

| 变量名 | 说明 | 示例 |
|--------|------|------|
| `DASH_SCOPE_API_KEY` | 阿里云 DashScope API 密钥 | `sk-xxxxxxxxxxxx` |
| `QWEN_MODEL` | Qwen 模型名称 | `qwen2.5-3b-instruct` |
| `DB_HOST` | MySQL 主机地址 | `localhost` |
| `DB_PORT` | MySQL 端口 | `3306` |
| `DB_USER` | MySQL 用户名 | `root` |
| `DB_PASSWORD` | MySQL 密码 | `your_password` |
| `DB_NAME` | 数据库名称 | `ai_chat_db` |
| `JWT_SECRET` | JWT 签名密钥（建议随机生成） | `your_secret_key` |
| `JWT_ALGORITHM` | JWT 加密算法 | `HS256` |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | Token 过期时间（分钟） | `1440` |

### 模型参数

在 `ai_service.py` 中可以调整以下参数：

- `model`：使用的模型名称（通过环境变量 `QWEN_MODEL` 配置）
- `temperature`：生成随机性（0-1，默认：0.5）
- `max_tokens`：最大生成长度（默认：2048）

### 数据库表结构

**users 表：**

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键，自增 |
| username | String(50) | 用户名（唯一） |
| email | String(100) | 邮箱地址（可选） |
| password_hash | String(255) | bcrypt 加密后的密码 |
| create_time | DateTime | 创建时间 |

**chat_records 表：**

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键，自增 |
| user_id | Integer | 用户ID（外键关联 users 表） |
| role | String(20) | 角色（"user" 或 "assistant"） |
| content | Text | 聊天内容 |
| create_time | DateTime | 创建时间 |

## 🧪 测试

测试 AI 服务：

```bash
python ai_service.py
```

这将执行内置的测试用例，验证 API 调用是否正常。

测试数据库功能：

```bash
python database.py
```

这将删除 default_user 的聊天记录（用于测试）。

## ❓ 常见问题

### 1. 提示 "You must pass the application as an import string"

**原因**：使用 `reload=True` 时需要传入导入字符串而非对象

**解决**：确保 `main.py` 中使用 `uvicorn.run("main:app", ...)` 而非 `uvicorn.run(app, ...)`

### 2. API 调用失败

**检查项**：
- 确认 `.env` 文件中 `DASH_SCOPE_API_KEY` 配置正确
- 验证 API 密钥是否有效且有足够的配额
- 检查网络连接是否正常

### 3. 数据库连接失败

**检查项**：
- 确认 MySQL 服务正在运行
- 检查 `.env` 中的数据库配置是否正确
- 确认数据库 `ai_chat_db` 已创建
- 验证数据库用户权限

### 4. 端口被占用

**解决**：修改 `main.py` 中的端口号，或通过命令行指定：
```bash
uvicorn main:app --host 0.0.0.0 --port 8080
```

### 5. Swagger UI 认证失败（401 Unauthorized）

**问题**：在 Swagger UI 中登录后，调用需要认证的接口仍然返回 401

**解决步骤**：
1. 点击右上角的 "Authorize" 按钮（锁图标🔒）
2. 在弹出的窗口中输入用户名和密码
3. 点击 "Authorize" 完成认证
4. 确认出现绿色的锁图标表示已认证
5. 现在可以正常调用需要认证的接口

**注意**：如果仍然失败，请检查：
- JWT_SECRET 环境变量是否正确配置
- Token 是否已过期（默认 1440 分钟 = 24 小时）
- 浏览器控制台是否有 CORS 或网络错误

### 6. 密码加密失败

**原因**：passlib 库与新版本的 bcrypt (4.x/5.x) 存在兼容性问题

**解决**：将 bcrypt 降级到 3.x 版本
```bash
pip install bcrypt==3.2.2
```

## 📝 开发指南

### 添加新的 API 端点

在 `main.py` 中添加路由：

```python
@app.post("/your-endpoint", tags=["分类名称"])
def your_function(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)  # 需要认证时添加
):
    return {"code": 200, "message": "success", "data": {}}
```

### 自定义 AI 模型参数

在 `ai_service.py` 的 `call_ai` 函数中调整：

```python
response = Generation.call(
    model=os.getenv("QWEN_MODEL"),
    temperature=0.7,
    max_tokens=4096,
    # ... 其他参数
)
```

### 扩展数据库功能

在 `database.py` 中添加新的查询方法：

```python
def get_user_stats(db, user_id: int):
    """获取用户统计信息"""
    total = db.query(ChatRecord).filter(ChatRecord.user_id == user_id).count()
    return {"user_id": user_id, "total_messages": total}
```

### 使用 Swagger UI OAuth2 认证

1. **配置登录接口**：确保 `/login/oauth` 接口返回标准 OAuth2 格式
2. **点击 Authorize**：在 Swagger UI 右上角点击锁图标
3. **输入凭据**：填写用户名和密码
4. **自动携带 Token**：认证后，所有请求会自动添加 `Authorization: Bearer <token>` 头

### JWT Token 自定义配置

在 `.env` 文件中调整：

```env
# 延长 Token 有效期（单位：分钟）
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=4320  # 3天

# 更换加密算法
JWT_ALGORITHM=HS512

# 更新密钥（生产环境务必使用强随机密钥）
JWT_SECRET=your_new_strong_secret_key_here
```

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

本项目仅供学习和研究使用。

## 🔗 相关链接

- [FastAPI 官方文档](https://fastapi.tiangolo.com/)
- [SQLAlchemy 官方文档](https://www.sqlalchemy.org/)
- [阿里云 DashScope 文档](https://help.aliyun.com/zh/dashscope/)
- [通义千问模型介绍](https://tongyi.aliyun.com/qianwen/)
- [JWT 标准](https://jwt.io/)
- [OAuth 2.0 规范](https://oauth.net/2/)
- [Swagger UI 文档](https://swagger.io/tools/swagger-ui/)

---

**祝您使用愉快！** 🎉
