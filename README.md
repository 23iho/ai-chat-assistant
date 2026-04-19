# AI聊天助手

基于 FastAPI、SQLAlchemy 和阿里云通义千问（Qwen）构建的 AI 聊天助手服务，支持数据库持久化存储聊天记录。

## 📋 项目简介

本项目是一个功能完整的 AI 聊天助手后端服务，使用 FastAPI 框架构建 RESTful API，集成阿里云 DashScope SDK 调用通义千问大语言模型，并通过 MySQL 数据库实现聊天记录的持久化存储和查询。

## ✨ 主要特性

- 🚀 **快速启动**：基于 FastAPI，高性能异步 Web 框架
- 💬 **智能对话**：集成通义千问 Qwen2.5-3B-Instruct 模型
- 🧠 **上下文记忆**：支持多轮对话，保持对话连贯性
- 💾 **数据持久化**：使用 MySQL 数据库存储聊天记录
- 🔍 **历史查询**：提供聊天记录查询和删除接口
- 🔄 **热重载**：开发模式下支持代码自动重载
- 📖 **自动文档**：FastAPI 自动生成 Swagger UI 和 ReDoc 文档
- 🔐 **环境变量管理**：使用 python-dotenv 安全管理配置信息

## 🛠️ 技术栈

- **Web 框架**：FastAPI 0.135.3
- **ASGI 服务器**：Uvicorn 0.44.0
- **AI 服务**：阿里云 DashScope SDK 1.25.16
- **AI 模型**：通义千问 qwen2.5-3b-instruct
- **数据库 ORM**：SQLAlchemy
- **数据库驱动**：PyMySQL
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
```

> 💡 **获取 API Key**：访问 [阿里云 DashScope 控制台](https://dashscope.console.aliyun.com/) 注册并获取 API 密钥

### 5. 准备数据库

确保已安装 MySQL 数据库，并创建对应的数据库：

```sql
CREATE DATABASE ai_chat_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

首次运行程序时，会自动创建 `chat_records` 表。

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

### GET 方式聊天

**请求：**
```http
GET /chat?message=你好&user_id=test_user
```

**参数说明：**
- `message`（必填）：用户输入的消息
- `clear_history`（可选）：是否清空上下文，默认 false
- `user_id`（可选）：用户ID，默认 test_user

**响应：**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "user": "你好",
    "assistant": "你好！我是AI聊天助手..."
  }
}
```

### POST 方式聊天

**请求：**
```http
POST /chat
Content-Type: application/json

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

### 查询聊天记录

**请求：**
```http
GET /history/{user_id}?skip=0&limit=100
```

**参数说明：**
- `user_id`（路径参数）：用户ID
- `skip`（可选）：跳过多少条记录，默认 0
- `limit`（可选）：最多返回多少条，默认 100

**响应：**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "user_id": "test_user",
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

### 删除聊天记录

**请求：**
```http
DELETE /history/{user_id}
```

**参数说明：**
- `user_id`（路径参数）：用户ID

**响应：**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "user_id": "test_user",
    "deleted_count": 10,
    "message": "已删除用户的聊天记录并清空上下文"
  }
}
```

## 📁 项目结构

```
ai-chat-assistant/
├── main.py              # FastAPI 主程序入口，定义路由端点
├── ai_service.py        # AI 服务模块（调用通义千问）
├── database.py          # 数据库模块（SQLAlchemy ORM + 聊天记录操作）
├── requirements.txt     # Python 依赖包列表
├── .env                 # 环境变量配置文件（需自行创建）
├── .env.example         # 环境变量示例文件
├── .gitignore          # Git 忽略文件配置
└── README.md           # 项目说明文档
```

## 🔧 核心模块说明

### main.py
- 创建 FastAPI 应用实例
- 定义 API 路由端点（健康检查、聊天、历史记录查询/删除）
- 配置全局异常处理
- 配置 Uvicorn 服务器启动参数

### ai_service.py
- 封装通义千问 API 调用逻辑
- 管理对话上下文（chat_history）
- 支持清空上下文功能
- 提供错误处理和异常捕获

### database.py
- 配置 MySQL 数据库连接
- 定义 ChatRecord 数据模型
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

### 模型参数

在 `ai_service.py` 中可以调整以下参数：

- `model`：使用的模型名称（通过环境变量 `QWEN_MODEL` 配置）
- `temperature`：生成随机性（0-1，默认：0.5）
- `max_tokens`：最大生成长度（默认：2048）

### 数据库表结构

**chat_records 表：**

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键，自增 |
| user_id | String(50) | 用户ID |
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

## 📝 开发指南

### 添加新的 API 端点

在 `main.py` 中添加路由：

```python
@app.post("/your-endpoint", tags=["分类名称"])
def your_function(db: Session = Depends(get_db)):
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
def get_user_stats(db, user_id: str):
    """获取用户统计信息"""
    total = db.query(ChatRecord).filter(ChatRecord.user_id == user_id).count()
    return {"user_id": user_id, "total_messages": total}
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

---

**祝您使用愉快！** 🎉
