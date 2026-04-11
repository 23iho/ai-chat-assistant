# AI聊天助手

基于 FastAPI 和阿里云通义千问（Qwen）构建的 AI 聊天助手服务。

## 📋 项目简介

本项目是一个轻量级的 AI 聊天助手后端服务，使用 FastAPI 框架构建 RESTful API，集成阿里云 DashScope SDK 调用通义千问大语言模型，支持上下文对话记忆功能。

## ✨ 主要特性

- 🚀 **快速启动**：基于 FastAPI，高性能异步 Web 框架
- 💬 **智能对话**：集成通义千问 Qwen2.5-3B-Instruct 模型
- 🧠 **上下文记忆**：支持多轮对话，保持对话连贯性
- 🔄 **热重载**：开发模式下支持代码自动重载
- 📖 **自动文档**：FastAPI 自动生成 Swagger UI 和 ReDoc 文档
- 🔐 **环境变量管理**：使用 python-dotenv 安全管理 API 密钥

## 🛠️ 技术栈

- **Web 框架**：FastAPI 0.135.3
- **ASGI 服务器**：Uvicorn 0.44.0
- **AI 服务**：阿里云 DashScope SDK 1.25.16
- **AI 模型**：通义千问 qwen2.5-3b-instruct
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

编辑 `.env` 文件，添加您的阿里云 DashScope API 密钥：

```env
DASH_SCOPE_API_KEY=your_api_key_here
```

> 💡 **获取 API Key**：访问 [阿里云 DashScope 控制台](https://dashscope.console.aliyun.com/) 注册并获取 API 密钥

## 🚀 运行服务

### 开发模式（推荐）

```bash
python main.py
```

服务将在 `http://0.0.0.0:8000` 启动，支持代码热重载。

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
  "status": "ok",
  "message": "AI聊天助手服务已启动"
}
```

### AI 对话接口

**请求：**
```http
POST /chat
Content-Type: application/json

{
  "message": "你好，请介绍一下自己",
  "history": [
    {"role": "user", "content": "你好"},
    {"role": "assistant", "content": "你好！我是AI助手"}
  ]
}
```

**响应：**
```json
{
  "reply": "我是基于通义千问模型的AI聊天助手..."
}
```

**参数说明：**
- `message`（必填）：用户输入的消息
- `history`（可选）：历史对话记录，格式为 `[{"role": "user/assistant", "content": "..."}]`

## 📁 项目结构

```
ai-chat-assistant/
├── main.py              # FastAPI 主程序入口
├── ai_service.py        # AI 服务模块（调用通义千问）
├── requirements.txt     # Python 依赖包列表
├── .env                 # 环境变量配置文件（需自行创建）
├── .env.example         # 环境变量示例文件
├── .gitignore          # Git 忽略文件配置
└── README.md           # 项目说明文档
```

## 🔧 核心模块说明

### main.py
- 创建 FastAPI 应用实例
- 定义 API 路由端点
- 配置 Uvicorn 服务器启动参数

### ai_service.py
- 封装通义千问 API 调用逻辑
- 支持上下文对话记忆
- 提供错误处理和异常捕获

## ⚙️ 配置说明

### 环境变量

| 变量名 | 说明 | 示例 |
|--------|------|------|
| `DASH_SCOPE_API_KEY` | 阿里云 DashScope API 密钥 | `sk-xxxxxxxxxxxx` |

### 模型参数

在 `ai_service.py` 中可以调整以下参数：

- `model`：使用的模型名称（默认：`qwen2.5-3b-instruct`）
- `temperature`：生成随机性（0-1，默认：0.5）
- `max_tokens`：最大生成长度（默认：2048）

## 🧪 测试

测试 AI 服务：

```bash
python ai_service.py
```

这将执行内置的测试用例，验证 API 调用是否正常。

## ❓ 常见问题

### 1. 提示 "You must pass the application as an import string"

**原因**：使用 `reload=True` 时需要传入导入字符串而非对象

**解决**：确保 `main.py` 中使用 `uvicorn.run("main:app", ...)` 而非 `uvicorn.run(app, ...)`

### 2. API 调用失败

**检查项**：
- 确认 `.env` 文件中 `DASH_SCOPE_API_KEY` 配置正确
- 验证 API 密钥是否有效且有足够的配额
- 检查网络连接是否正常

### 3. 端口被占用

**解决**：修改 `main.py` 中的端口号，或通过命令行指定：
```bash
uvicorn main:app --host 0.0.0.0 --port 8080
```

## 📝 开发指南

### 添加新的 API 端点

在 `main.py` 中添加路由：

```python
@app.post("/your-endpoint", tags=["分类名称"])
def your_function():
    return {"message": "response"}
```

### 自定义 AI 模型参数

在 `ai_service.py` 的 `call_ai` 函数中调整：

```python
response = Generation.call(
    model="your-model-name",
    temperature=0.7,
    max_tokens=4096,
    # ... 其他参数
)
```

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

本项目仅供学习和研究使用。

## 🔗 相关链接

- [FastAPI 官方文档](https://fastapi.tiangolo.com/)
- [阿里云 DashScope 文档](https://help.aliyun.com/zh/dashscope/)
- [通义千问模型介绍](https://tongyi.aliyun.com/qianwen/)

---

**祝您使用愉快！** 🎉
