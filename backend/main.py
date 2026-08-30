from fastapi import FastAPI,HTTPException,Depends,status,Form
from fastapi.responses import JSONResponse,StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from ai_service import call_ai, stream_ai
from pydantic import BaseModel,Field,EmailStr,StringConstraints
from typing import Annotated
from sqlalchemy.orm import Session
from database import (
    get_db,
    ChatRecord,
    Conversation,
    save_and_record,
    get_chat_history,
    get_latest_n_chat_history,
    delete_chat_history,
    list_conversations,
    get_conversation,
    create_conversation,
    rename_conversation,
    delete_conversation,
    touch_conversation,
    get_user_by_username,
    create_user,
    verify_password,
)
from datetime import datetime, timedelta
import json

from sqlalchemy.orm import Session
from auth import create_access_token,get_current_user

# OAuth2 安全方案（用于OpenAPI文档）
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login/oauth")

#创建FastAPI实例
app = FastAPI(
    title="AI聊天助手",
    version="0.1.0",
)

# 配置CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080"], 
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

#定义请求体模型
class ChatRequest(BaseModel):
    """聊天请求体模型"""
    message: Annotated[str, StringConstraints(max_length=1000)] = Field(..., description="用户输入的消息")
    conversation_id: int | None = Field(None, description="所属会话ID；为空时自动创建")
    clear_history: bool = Field(False, description="是否清空上下文")


class ConversationCreate(BaseModel):
    title: str | None = Field(None, max_length=200, description="会话标题，可空（用首条消息生成）")


class ConversationRename(BaseModel):
    title: Annotated[str, StringConstraints(min_length=1, max_length=200)] = Field(..., description="新标题")
#定义用户注册模型
class UserRegister(BaseModel):
    username: Annotated[str, StringConstraints(min_length=3, max_length=20)] = Field(..., description="用户名")
    email: EmailStr | None = Field(None, description="邮箱(可选)")
    password: Annotated[str, StringConstraints(min_length=6, max_length=100)] = Field(..., description="密码")
class UserLogin(BaseModel):
    username: str = Field(...)
    password: str = Field(...)



class UserContextCache:
    """进程内的 (用户, 会话) 上下文缓存（最近 N 轮对话）。

    key 用 (user_id, conversation_id) 元组，避免切会话时上下文串台。

    ⚠️ 已知限制（写进 README "Known Issues"）：
    - 单进程内存，重启即丢，下次访问从 DB 回填
    - 多 worker 部署下命中率会下降（每个 worker 各自一份内存）
    - 仅适合开发/单机，生产环境请替换为 Redis Hash + TTL

    这里先做一个简单的有界实现，防止长期运行内存无限增长。
    """

    # 单 worker 最多保留多少个 (user, conv) 的活跃上下文；
    # 超出按 LRU 淘汰最久未访问的。设为 0 表示不淘汰（仅用于 debug）。
    MAX_KEYS = 1000

    def __init__(self, max_window: int = 20):
        self._store: dict[tuple[int, int | None], list] = {}
        self._access_order: list[tuple[int, int | None]] = []
        self.max_window = max_window

    def _key(self, user_id: int, conversation_id: int | None) -> tuple[int, int | None]:
        return (user_id, conversation_id)

    def get(self, user_id: int, conversation_id: int | None = None) -> list:
        """获取 (user, conv) 上下文窗口，未命中时初始化为空列表。"""
        k = self._key(user_id, conversation_id)
        if k not in self._store:
            self._evict_if_needed()
            self._store[k] = []
        self._touch(k)
        return self._store[k]

    def clear(self, user_id: int, conversation_id: int | None = None) -> None:
        """清空指定 (user, conv) 的上下文窗口。"""
        k = self._key(user_id, conversation_id)
        self._store[k] = []
        self._touch(k)

    def append_message(self, user_id: int, conversation_id: int | None,
                       role: str, content: str) -> None:
        """追加一条消息并按窗口长度截断。"""
        window = self.get(user_id, conversation_id)
        window.append({"role": role, "content": content})
        if len(window) > self.max_window:
            self._store[self._key(user_id, conversation_id)] = window[-self.max_window:]
        self._touch(self._key(user_id, conversation_id))

    def evict_user(self, user_id: int) -> None:
        """主动移除某个用户的所有会话（用于账号注销等场景）。"""
        keys = [k for k in self._store if k[0] == user_id]
        for k in keys:
            self._store.pop(k, None)
        self._access_order = [k for k in self._access_order if k[0] != user_id]

    def evict_conversation(self, user_id: int, conversation_id: int | None) -> None:
        k = self._key(user_id, conversation_id)
        self._store.pop(k, None)
        if k in self._access_order:
            self._access_order.remove(k)

    def stats(self) -> dict:
        """便于调试 / 监控。"""
        return {
            "active_keys": len(self._store),
            "max_keys": self.MAX_KEYS,
            "max_window": self.max_window,
        }

    def _touch(self, k: tuple[int, int | None]) -> None:
        if k in self._access_order:
            self._access_order.remove(k)
        self._access_order.append(k)

    def _evict_if_needed(self) -> None:
        if self.MAX_KEYS <= 0:
            return
        while len(self._store) >= self.MAX_KEYS and self._access_order:
            oldest = self._access_order.pop(0)
            self._store.pop(oldest, None)


# 全局实例（开发/单机用），生产环境替换为 Redis 实现
user_chat_history = UserContextCache(max_window=20)


# ===== 共用辅助函数 =====

def _resolve_conversation(db, current_user, conversation_id: int | None,
                          first_message: str | None = None) -> Conversation:
    """根据 conversation_id 拿到当前用户的会话。

    - 如果传了 ID 且属于当前用户 → 返回
    - 否则新建一个（标题用首条消息的前 30 字，或 "新对话"）
    """
    if conversation_id is not None:
        conv = get_conversation(db, conversation_id, current_user.id)
        if conv:
            return conv
    title = (first_message or "新对话")[:30]
    return create_conversation(db, current_user.id, title)


def _ensure_context_loaded(db, user_id: int, conversation_id: int) -> list:
    """从 DB 加载该会话最近 20 条到内存上下文（首次访问时）。"""
    key = (user_id, conversation_id)
    if not user_chat_history._store.get(key):
        records = get_latest_n_chat_history(db, user_id, 20, conversation_id=conversation_id)
        user_chat_history._store[key] = [
            {"role": r.role, "content": r.content} for r in records
        ]
        user_chat_history._touch(key)
    return user_chat_history._store[key]


#全局异常捕获
# 这里只兜底"没被任何路由处理的异常"。
# HTTPException / RequestValidationError 走各自专用 handler，
# 保持 REST 语义（401 / 404 / 422 真实状态码），不被吞成 200。
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"code": exc.status_code, "message": exc.detail, "data": None},
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse(
        status_code=422,
        content={"code": 422, "message": "参数校验失败", "data": {"errors": exc.errors()}},
    )

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"code": 500, "message": f"服务器异常：{str(exc)}", "data": {"error": str(exc)}},
    )
#健康检查接口：用来判断服务是否正常运行
@app.get("/",tags=["系统接口"])
def health_check():
    return {
        "code":200,
        "message":"success",
        "data":{"status":"ok","message":"AI聊天助手服务已启动"}
        }

#定义get方式聊天接口（保留用于 Swagger 演示和单元测试）
# 注意：GET 请求会把消息写到 URL 里（access log / 浏览器历史），
# 实际使用请走 POST /chat 或 POST /chat/stream。
@app.get("/chat", tags=["聊天接口"], summary="GET聊天（需登录，仅供演示）")
def chat_get(
    message: str,
    conversation_id: int | None = None,
    clear_history: bool = False,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    user_id = current_user.id
    conv = _resolve_conversation(db, current_user, conversation_id, first_message=message)
    user_history = _ensure_context_loaded(db, user_id, conv.id)
    if clear_history:
        user_chat_history.clear(user_id, conv.id)
        return {"code": 200, "message": "success", "data": {"message": "上下文已清空"}}
    answer = call_ai(message, user_history)
    save_and_record(db, user_id, "user", message, conversation_id=conv.id)
    save_and_record(db, user_id, "assistant", answer, conversation_id=conv.id)
    user_chat_history.append_message(user_id, conv.id, "user", message)
    user_chat_history.append_message(user_id, conv.id, "assistant", answer)
    touch_conversation(db, conv.id)
    return {
        "code": 200,
        "message": "success",
        "data": {
            "user": message, "ai": answer,
            "conversation_id": conv.id, "conversation_title": conv.title,
        }
    }

#添加post请求接口
@app.post("/chat", tags=["聊天接口"], summary="POST方式聊天（需登录）")
def chat_post(
    req: ChatRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    user_id = current_user.id
    conv = _resolve_conversation(db, current_user, req.conversation_id,
                                 first_message=req.message)
    user_history = _ensure_context_loaded(db, user_id, conv.id)
    if req.clear_history:
        user_chat_history.clear(user_id, conv.id)
        return {"code": 200, "message": "success", "data": {"message": "上下文已清空"}}
    answer = call_ai(req.message, user_history)
    save_and_record(db, user_id, "user", req.message, conversation_id=conv.id)
    save_and_record(db, user_id, "assistant", answer, conversation_id=conv.id)
    user_chat_history.append_message(user_id, conv.id, "user", req.message)
    user_chat_history.append_message(user_id, conv.id, "assistant", answer)
    touch_conversation(db, conv.id)
    return {
        "code": 200,
        "message": "success",
        "data": {
            "user": req.message, "ai": answer,
            "conversation_id": conv.id, "conversation_title": conv.title,
        }
    }


# ===== SSE 流式聊天 =====
# 与 /chat 阻塞式不同，/chat/stream 在 AI 边生成时边把 chunk 推给前端，
# 前端拿到一个 chunk 就更新一次 UI，首字延迟从"等全文"降到"等第一个字"。
@app.post("/chat/stream", tags=["聊天接口"], summary="SSE 流式聊天（需登录）")
def chat_stream(
    req: ChatRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    user_id = current_user.id

    # 解析会话（无 ID 则新建一个，标题用首条消息）
    conv = _resolve_conversation(db, current_user, req.conversation_id,
                                 first_message=req.message)

    # 第一个 chunk 先告诉前端"这条消息属于哪个会话"，
    # 让前端可以立刻把会话切到新会话
    init_payload = json.dumps(
        {"type": "init", "conversation_id": conv.id, "conversation_title": conv.title},
        ensure_ascii=False,
    )

    # clear_history 直接清空该会话的上下文
    if req.clear_history:
        user_chat_history.clear(user_id, conv.id)
        def cleared():
            yield f"data: {init_payload}\n\n"
            payload = json.dumps({"type": "info", "message": "上下文已清空"}, ensure_ascii=False)
            yield f"data: {payload}\n\n"
            yield "data: [DONE]\n\n"
        return StreamingResponse(
            cleared(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    # 重建上下文
    user_history = _ensure_context_loaded(db, user_id, conv.id)
    history_snapshot = list(user_history)  # 给 stream_ai 用，避免双写

    # 先把用户消息存 DB + 上下文（即使后面 stream 中途断开也不丢）
    save_and_record(db, user_id=user_id, role="user", content=req.message, conversation_id=conv.id)
    user_chat_history.append_message(user_id, conv.id, "user", req.message)

    def event_generator():
        yield f"data: {init_payload}\n\n"
        full_content_parts = []
        try:
            for chunk in stream_ai(req.message, history_snapshot):
                full_content_parts.append(chunk)
                payload = json.dumps({"type": "content", "text": chunk}, ensure_ascii=False)
                yield f"data: {payload}\n\n"
        except RuntimeError as e:
            err_payload = json.dumps({"type": "error", "message": str(e)}, ensure_ascii=False)
            yield f"data: {err_payload}\n\n"
            return
        except Exception as e:
            err_payload = json.dumps({"type": "error", "message": f"系统错误：{e}"}, ensure_ascii=False)
            yield f"data: {err_payload}\n\n"
            return

        full_content = "".join(full_content_parts)
        if full_content:
            save_and_record(db, user_id=user_id, role="assistant",
                            content=full_content, conversation_id=conv.id)
            user_chat_history.append_message(user_id, conv.id, "assistant", full_content)
            touch_conversation(db, conv.id)

        done_payload = json.dumps({"type": "done"}, ensure_ascii=False)
        yield f"data: {done_payload}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # 关掉 nginx 之类的中间缓冲，保证实时
        },
    )


#添加聊天记录查询接口
@app.get("/history", tags=["聊天记录接口"], summary="查询我的聊天记录（需登录）")
def get_my_history(
    skip: int = 0,
    limit: int = 100,
    conversation_id: int | None = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    # 校验 conversation_id 属于当前用户
    if conversation_id is not None and not get_conversation(db, conversation_id, current_user.id):
        raise HTTPException(status_code=404, detail="会话不存在或不属于当前用户")

    records = get_chat_history(db, current_user.id, skip, limit, conversation_id=conversation_id)
    history = [
        {
            "id": record.id,
            "conversation_id": record.conversation_id,
            "role": record.role,
            "content": record.content,
            "create_time": record.create_time.strftime("%Y-%m-%d %H:%M:%S")
        }
        for record in records
    ]
    return {
        "code": 200,
        "message": "success",
        "data": {
            "user_id": current_user.id,
            "conversation_id": conversation_id,
            "total": len(history),
            "history": history
        }
    }

#添加删除聊天记录接口
@app.delete("/history", tags=["聊天记录接口"], summary="清空我的聊天记录（需登录）")
def delete_my_history(
    conversation_id: int | None = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    if conversation_id is not None and not get_conversation(db, conversation_id, current_user.id):
        raise HTTPException(status_code=404, detail="会话不存在或不属于当前用户")
    deleted_count = delete_chat_history(db, current_user.id, conversation_id=conversation_id)
    if conversation_id is not None:
        user_chat_history.evict_conversation(current_user.id, conversation_id)
    return {
        "code": 200,
        "message": "success",
        "data": {
            "user_id": current_user.id,
            "conversation_id": conversation_id,
            "deleted_count": deleted_count,
            "message": "已清空聊天记录"
        }
    }


# ===== 会话（Conversation）CRUD =====

@app.get("/conversations", tags=["会话接口"], summary="列出我的会话")
def list_my_conversations(
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    items = list_conversations(db, current_user.id, limit=limit)
    return {
        "code": 200,
        "message": "success",
        "data": {
            "user_id": current_user.id,
            "total": len(items),
            "conversations": [
                {
                    "id": c.id,
                    "title": c.title,
                    "created_at": c.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                    "updated_at": c.updated_at.strftime("%Y-%m-%d %H:%M:%S"),
                }
                for c in items
            ],
        },
    }


@app.post("/conversations", tags=["会话接口"], summary="新建会话")
def create_my_conversation(
    req: ConversationCreate | None = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    title = (req.title if req and req.title else "新对话").strip()[:200] or "新对话"
    conv = create_conversation(db, current_user.id, title)
    return {
        "code": 200,
        "message": "success",
        "data": {
            "id": conv.id,
            "title": conv.title,
            "created_at": conv.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        },
    }


@app.patch("/conversations/{conversation_id}", tags=["会话接口"], summary="重命名会话")
def rename_my_conversation(
    conversation_id: int,
    req: ConversationRename,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    conv = rename_conversation(db, conversation_id, current_user.id, req.title)
    if not conv:
        raise HTTPException(status_code=404, detail="会话不存在或不属于当前用户")
    return {
        "code": 200,
        "message": "success",
        "data": {
            "id": conv.id,
            "title": conv.title,
            "updated_at": conv.updated_at.strftime("%Y-%m-%d %H:%M:%S"),
        },
    }


@app.delete("/conversations/{conversation_id}", tags=["会话接口"], summary="删除会话（级联删除消息）")
def delete_my_conversation(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    deleted = delete_conversation(db, conversation_id, current_user.id)
    if not deleted and not get_conversation(db, conversation_id, current_user.id):
        # 没找到也直接当不存在处理，避免泄露信息
        pass
    user_chat_history.evict_conversation(current_user.id, conversation_id)
    return {
        "code": 200,
        "message": "success",
        "data": {
            "conversation_id": conversation_id,
            "deleted_records": deleted,
            "message": "会话已删除",
        },
    }


#注册接口
@app.post("/register",tags=["用户系统"],summary="用户注册")
def user_register(req:UserRegister,db:Session=Depends(get_db)):
    if get_user_by_username(db,req.username):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="用户名已存在")
    user=create_user(db,req.username,req.password,req.email)
    return {
        "code":200,
        "message":"success",
        "data":{"user_id":user.id,"username":user.username,"create_time":user.create_time.strftime(r"%Y-%m-%d %H:%M:%S")}
    }
#定义登录接口
@app.post("/login",tags=["用户系统"])
def user_login(req:UserLogin,db:Session=Depends(get_db)):
    # 注意：这里不再套 try/except。HTTPException 是 Exception 的子类，
    # 之前的 except Exception 写在前，会先把 HTTPException 吞掉变成 400，
    # 后面的 except HTTPException 是永远不可达的死代码。
    # 业务异常由 FastAPI 内置 handler 渲染成 JSONResponse，符合 REST 语义。
    user = get_user_by_username(db,req.username)
    if not user:
        raise HTTPException(status_code=401,detail="用户名或密码错误")

    if not verify_password(req.password, user.password_hash):
        raise HTTPException(status_code=401,detail="用户名或密码错误")

    access_token,expire_time = create_access_token(data={"user_id": user.id, "username": user.username})
    return {
        "code":200,
        "message":"success",
        "data":{"access_token":access_token,"token_type":"bearer","expire_time":expire_time}
    }

# OAuth2 兼容的登录端点（供 Swagger UI Authorize 使用）
@app.post("/login/oauth", include_in_schema=False,response_model=None)
def oauth_login(
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    """OAuth2 标准格式的登录端点，仅供 Swagger UI 认证使用"""
    user = get_user_by_username(db, username)
    if not user:
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    
    if not verify_password(password, user.password_hash):
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    access_token, expire_time = create_access_token(data={"user_id": user.id, "username": user.username})

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

@app.get("/users/me",tags=["用户系统"])
def get_my_info(current_user=Depends(get_current_user)):
    return {
        "code":200,
        "message":"success",
        "data":{"user_id":current_user.id,"username":current_user.username,"email":current_user.email}
    }
#主程序入口
if __name__=="__main__":
    import uvicorn
    uvicorn.run("main:app",host="0.0.0.0",port=8000,reload=True)
