from fastapi import FastAPI
from ai_service import call_ai

#创建FastAPI实例
app = FastAPI(title="AI聊天助手",version="0.1.0")
#健康检查接口：用来判断服务是否正常运行
@app.get("/",tags=["系统接口"])
def health_check():
    return {"status":"ok","message":"AI聊天助手服务已启动"}

#定义get方式聊天接口
#@app.get("/chat")：接口路径是/chat.访问http://127.0.0.1:8000/chat就会到这里
#tags=["聊天接口"]：分类到聊天接口
@app.get("/chat",tags=["聊天接口"])
def chat_get(message:str):
    """
    get方式调用AI聊天
    ：param message：用户输入的消息（通过url参数传入）
    ：return：包含用户消息和AI回复的JSON对象
    """
    answer=call_ai(message)
    return {"user":message,"assistant":answer}

#主程序入口
if __name__=="__main__":
    import uvicorn
    uvicorn.run("main:app",host="0.0.0.0",port=8000,reload=True)
