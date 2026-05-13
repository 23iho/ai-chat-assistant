# AI 聊天助手

基于 FastAPI、SQLAlchemy 和阿里云通义千问（Qwen）构建的 AI 聊天助手，前端后端分离。支持用户认证、多用户隔离、数据库持久化存储聊天记录。

## ✨ 主要特性

- 🚀 **前后端分离**：后端 FastAPI + 前端原生 HTML/CSS/JS
- 💬 **智能对话**：集成通义千问 Qwen 模型
- 🧠 **上下文记忆**：支持多轮对话，保持对话连贯性
- 🔐 **用户认证**：支持注册、登录，JWT Token 认证
- 👥 **多用户隔离**：每个用户的聊天记录独立存储
- 💾 **数据持久化**：MySQL 数据库存储用户信息和聊天记录
- 🔍 **历史查询**：提供聊天记录查询和删除接口
- 📱 **响应式设计**：前端适配桌面和移动设备
- 📖 **自动文档**：FastAPI 自动生成 Swagger UI

## 🛠️ 技术栈

| 层级 | 技术 | 版本 |
|------|------|------|
| 后端框架 | FastAPI | 0.135+ |
| ASGI 服务器 | Uvicorn | 0.44+ |
| AI 服务 | 阿里云 DashScope SDK | 1.25+ |
| AI 模型 | 通义千问（Qwen） | - |
| 数据库 ORM | SQLAlchemy | 2.0+ |
| 数据库驱动 | PyMySQL | 1.1+ |
| 认证加密 | python-jose (JWT) + passlib/bcrypt | - |
| 前端 | 原生 HTML / CSS / JavaScript | - |

## 📁 项目结构

```
ai-chat-assistant/
├── backend/                    ← 后端代码
│   ├── main.py                 FastAPI 主程序，定义路由端点
│   ├── ai_service.py           AI 服务模块（调用通义千问）
│   ├── auth.py                 认证模块（JWT Token 生成和验证）
│   ├── database.py             数据库模块（SQLAlchemy ORM）
│   ├── requirements.txt        Python 依赖包列表
│   ├── .env                    环境变量配置（需自行创建）
│   ├── .env.example            环境变量示例文件
│   └── .gitignore              Git 忽略规则
│
├── frontend/                   ← 前端代码
│   ├── index.html              聊天界面
│   ├── css/style.css           样式文件
│   ├── js/app.js               JavaScript 逻辑
│   └── start.bat               Windows 快捷启动脚本
│
├── .vscode/                    VS Code 配置
└── README.md                   本文件
```

## 📦 安装与配置

### 1. 安装依赖

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Linux/Mac
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
copy .env.example .env       # Windows
# cp .env.example .env       # Linux/Mac
```

编辑 `.env`，填入你的配置：

```env
# 阿里云 DashScope API Key
DASH_SCOPE_API_KEY=sk-xxxxxxxxxxxx

# Qwen 模型
QWEN_MODEL=你想使用的模型

# MySQL 数据库
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=ai_chat_db

# JWT 认证
JWT_SECRET=your_secret_key
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=1440
```

### 3. 准备数据库

```sql
CREATE DATABASE ai_chat_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

首次启动时会自动创建 `users` 和 `chat_records` 表。

## 🚀 启动服务

### 后端（端口 8000）

```bash
cd backend
python main.py
# 或生产模式：uvicorn main:app --host 0.0.0.0 --port 8000
```

### 前端（端口 8080）

```bash
cd frontend
start.bat                     # Windows
# python -m http.server 8080  # 通用
```

浏览器打开 **http://localhost:8080**

## 📖 API 接口

启动后端后访问：

- **Swagger UI**：http://localhost:8000/docs
- **ReDoc**：http://localhost:8000/redoc

### 接口一览

|  方法  | 路径              | 说明           |需登录|
|------  |------            |------          |------|
| GET    | `/`              | 健康检查        | ❌ |
| POST   | `/register`      | 用户注册        | ❌ |
| POST   | `/login`         | 用户登录        | ❌ |
| GET    | `/users/me`      | 当前用户信息    | ✅ |
| GET    | `/chat?message=` | 发送消息（GET） | ✅ |
| POST   | `/chat`          | 发送消息（POST）| ✅ |
| GET    | `/history`       | 查询聊天记录    | ✅ |
| DELETE | `/history`       | 清空聊天记录    | ✅ |

## 🔧 常见问题

**端口被占用？** 修改 `main.py` 中的 `port=8000` 或 `frontend/start.bat` 中的 `8080`。

**数据库连不上？** 确认 MySQL 已启动，`.env` 中配置正确，且数据库 `ai_chat_db` 已手动创建。

**API Key 问题？** 访问 [阿里云 DashScope 控制台](https://dashscope.console.aliyun.com/) 获取。
