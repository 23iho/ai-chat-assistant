from fastapi import FastAPI,HTTPException,Depends,status,Form
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from ai_service import call_ai
from pydantic import BaseModel,Field,EmailStr,StringConstraints
from typing import Annotated
from sqlalchemy.orm import Session
from database import get_db,ChatRecord,save_and_record,get_chat_history,get_latest_n_chat_history,delete_chat_history,get_db,get_user_by_username,create_user,verify_password
from datetime import datetime, timedelta

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
    clear_history: bool = Field(False, description="是否清空上下文")
#定义用户注册模型
class UserRegister(BaseModel):
    username: Annotated[str, StringConstraints(min_length=3, max_length=20)] = Field(..., description="用户名")
    email: EmailStr | None = Field(None, description="邮箱(可选)")
    password: Annotated[str, StringConstraints(min_length=6, max_length=100)] = Field(..., description="密码")
class UserLogin(BaseModel):
    username: str = Field(...)
    password: str = Field(...)



class UserContextCache:
    """进程内用户上下文缓存（最近 N 轮对话）。

    ⚠️ 已知限制（写进 README "Known Issues"）：
    - 单进程内存，重启即丢，下次访问从 DB 回填
    - 多 worker 部署下命中率会下降（每个 worker 各自一份内存）
    - 仅适合开发/单机，生产环境请替换为 Redis Hash + TTL

    这里先做一个简单的有界实现，防止长期运行内存无限增长。
    """

    # 单 worker 最多保留多少用户的活跃上下文；超出会按 LRU 淘汰最久未访问的。
    # 设为 0 表示不淘汰（仅用于 debug）。
    MAX_USERS = 1000

    def __init__(self, max_window: int = 20):
        self._store: dict[int, list] = {}
        self._access_order: list[int] = []  # 头部最久未访问，尾部最新
        self.max_window = max_window

    def get(self, user_id: int) -> list:
        """获取用户上下文窗口，未命中时初始化为空列表。"""
        if user_id not in self._store:
            self._evict_if_needed()
            self._store[user_id] = []
        self._touch(user_id)
        return self._store[user_id]

    def clear(self, user_id: int) -> None:
        """清空指定用户的上下文窗口。"""
        self._store[user_id] = []
        self._touch(user_id)

    def append_message(self, user_id: int, role: str, content: str) -> None:
        """追加一条消息并按窗口长度截断。"""
        window = self.get(user_id)
        window.append({"role": role, "content": content})
        if len(window) > self.max_window:
            # 只保留最后 max_window 条
            self._store[user_id] = window[-self.max_window:]
        self._touch(user_id)

    def evict(self, user_id: int) -> None:
        """主动移除某个用户（用于账号注销等场景）。"""
        self._store.pop(user_id, None)
        if user_id in self._access_order:
            self._access_order.remove(user_id)

    def stats(self) -> dict:
        """便于调试 / 监控。"""
        return {
            "active_users": len(self._store),
            "max_users": self.MAX_USERS,
            "max_window": self.max_window,
        }

    def _touch(self, user_id: int) -> None:
        if user_id in self._access_order:
            self._access_order.remove(user_id)
        self._access_order.append(user_id)

    def _evict_if_needed(self) -> None:
        if self.MAX_USERS <= 0:
            return
        while len(self._store) >= self.MAX_USERS and self._access_order:
            oldest = self._access_order.pop(0)
            self._store.pop(oldest, None)


# 全局实例（开发/单机用），生产环境替换为 Redis 实现
user_chat_history = UserContextCache(max_window=20)


# 兼容旧调用：让 main.py 里的 get_user_history / clear_user_history 仍然可用
def get_user_history(user_id: int) -> list:
    return user_chat_history.get(user_id)


def clear_user_history(user_id: int) -> None:
    user_chat_history.clear(user_id)

#全局异常捕获
@app.exception_handler(Exception)
async def global_exception_handler(request,exc):
    return JSONResponse(
        status_code=200,
        content={"code":400,"message":f"服务器异常：{str(exc)}","data":{"error":str(exc)}}
    )
#健康检查接口：用来判断服务是否正常运行
@app.get("/",tags=["系统接口"])
def health_check():
    return {
        "code":200,
        "message":"success",
        "data":{"status":"ok","message":"AI聊天助手服务已启动"}
        }

#定义get方式聊天接口
#@app.get("/chat")：接口路径是/chat.访问http://127.0.0.1:8000/chat就会到这里
#tags=["聊天接口"]：分类到聊天接口
@app.get("/chat", tags=["聊天接口"], summary="GET聊天（需登录）")
def chat_get(
    message: str,
    clear_history: bool = False,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    user_id = current_user.id
    # 如果内存上下文为空，从数据库加载最近记录重建上下文
    if user_id not in user_chat_history or not user_chat_history[user_id]:
        records = get_latest_n_chat_history(db, user_id, 20)
        user_chat_history[user_id] = [
            {"role": r.role, "content": r.content}
            for r in records
        ]
    user_history = get_user_history(user_id)
    if clear_history:
        clear_user_history(user_id)
        return {
            "code": 200,
            "message": "success",
            "data": {"message": "上下文已清空"}
        }
    answer = call_ai(message, user_history)
    save_and_record(db, user_id, "user", message)
    save_and_record(db, user_id, "assistant", answer)
    user_history.append({"role": "user", "content": message})
    user_history.append({"role": "assistant", "content": answer})
    if len(user_history) > 20:
        user_chat_history[user_id] = user_history[-20:]
    return {
        "code": 200,
        "message": "success",
        "data": {"user": message, "ai": answer}
    }

#添加post请求接口
#@app.post("/chat"):定义post请求的接口
@app.post("/chat", tags=["聊天接口"], summary="POST方式聊天（需登录）")
def chat_post(
    req: ChatRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user) 
):
    user_id = current_user.id
    # 如果内存上下文为空，从数据库加载最近记录重建上下文
    if user_id not in user_chat_history or not user_chat_history[user_id]:
        records = get_latest_n_chat_history(db, user_id, 20)
        user_chat_history[user_id] = [
            {"role": r.role, "content": r.content}
            for r in records
        ]
    user_history = get_user_history(user_id)
    if req.clear_history:
        clear_user_history(user_id)
        return {
            "code": 200,
            "message": "success",
            "data": {"message": "上下文已清空"}
        }
    answer = call_ai(req.message, user_history)
    save_and_record(db, user_id=user_id, role="user", content=req.message)
    save_and_record(db, user_id=user_id, role="assistant", content=answer)
    user_history.append({"role": "user", "content": req.message})
    user_history.append({"role": "assistant", "content": answer})
    if len(user_history) > 20:
        user_chat_history[user_id] = user_history[-20:]
    return {
        "code": 200,
        "message": "success",
        "data": {"user": req.message, "ai": answer}
    }

#添加聊天记录查询接口
@app.get("/history", tags=["聊天记录接口"], summary="查询我的聊天记录（需登录）")
def get_my_history(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    records = get_chat_history(db, current_user.id, skip, limit)
    history = [
        {
            "id": record.id,
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
            "total": len(history),
            "history": history
        }
    }

#添加删除聊天记录接口
@app.delete("/history", tags=["聊天记录接口"], summary="清空我的聊天记录（需登录）")
def delete_my_history(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    deleted_count = delete_chat_history(db, current_user.id)
    clear_user_history(current_user.id)
    return {
        "code": 200,
        "message": "success",
        "data": {
            "user_id": current_user.id,
            "deleted_count": deleted_count,
            "message": "已清空你的聊天记录"
        }
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
