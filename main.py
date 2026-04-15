from fastapi import FastAPI,HTTPException
from fastapi.responses import JSONResponse
from ai_service import call_ai
from pydantic import BaseModel,Field

#创建FastAPI实例
app = FastAPI(title="AI聊天助手",version="0.1.0")
#全局异常捕获
@app.exception_handler(Exception)
async def global_exception_handler(request,exc):
    return JSONResponse(
        status_code=200,
        content={"code":400,"message":f"服务器异常：{str(exc)}","data":None}
    )

#定义请求体模型
class ChatRequest(BaseModel):
    """聊天请求体模型"""
    message:str=Field(...,description="用户输入的消息",max_lenth=1000)
    clear_history:bool=Field(False,description="是否清空上下文")
    

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
@app.get("/chat",tags=["聊天接口"])
def chat_get(message:str,clear_history:bool=False):
    """
    get方式调用AI聊天
    ：param message：用户输入的消息（通过url参数传入）
    ：return：统一相应格式
    """
    answer=call_ai(message,clear_history)
    return {
        "code":200,
        "message":"success",
        "data":{"user":message,"assistant":answer}
        }

#添加post请求接口
#@app.post("/chat"):定义post请求的接口
#summary="POST方式聊天":接口的简短描述，会显示在文档里
@app.post("/chat",tags=["聊天接口"],summary="POST方式聊天")
def chat_post(req:ChatRequest):
    """
    post方式调用AI聊天
    ：param req：聊天前驱体（自动从json转换为ChatRequests对象）
    ：return：包含用户消息和AI回复的json
    """
    #1.从请求体中去除用户的消息（req.message)
    #2.调用call_ai函数
    answer=call_ai(req.message,clear_history=req.clear_history)
    return {
        "code":200,
        "message":"success",
        "data":{"user":req.message,"assistant":answer}
        }

#主程序入口
if __name__=="__main__":
    import uvicorn
    uvicorn.run("main:app",host="127.0.0.1",port=8000,reload=True)
