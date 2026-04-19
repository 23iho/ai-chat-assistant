from fastapi import FastAPI,HTTPException,Depends
from fastapi.responses import JSONResponse
from ai_service import call_ai,chat_history
from pydantic import BaseModel,Field
from sqlalchemy.orm import Session
from database import get_db,ChatRecord,save_and_record,get_chat_history,delete_chat_history
from datetime import datetime

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
def chat_get(message:str,clear_history:bool=False,user_id:str="test_user",db:Session=Depends(get_db)):
    """
    get方式调用AI聊天
    ：param message：用户输入的消息（通过url参数传入）
    ：return：统一相应格式
    """
    answer=call_ai(message,clear_history)
    save_and_record(db,user_id=user_id,role="user",content=message)
    save_and_record(db,user_id=user_id,role="assistant",content=answer)
    return {
        "code":200,
        "message":"success",
        "data":{"user":message,"assistant":answer}
        }

#添加post请求接口
#@app.post("/chat"):定义post请求的接口
#summary="POST方式聊天":接口的简短描述，会显示在文档里
@app.post("/chat",tags=["聊天接口"],summary="POST方式聊天")
def chat_post(req:ChatRequest,user_id:str="default_user",db:Session=Depends(get_db)):
    """
    post方式调用AI聊天
    ：param req：聊天前驱体（自动从json转换为ChatRequests对象）
    ：return：包含用户消息和AI回复的json
    """

    #1.从请求体中去除用户的消息（req.message)
    #2.调用call_ai函数
    answer=call_ai(req.message,clear_history=req.clear_history)
    save_and_record(db,user_id=user_id,role="user",content=req.message)
    save_and_record(db,user_id=user_id,role="assistant",content=answer)
    return {
        "code":200,
        "message":"success",
        "data":{"user":req.message,"assistant":answer}
        }

#添加聊天记录查询接口
@app.get("/history/{user_id}",tags=["聊天记录接口"],summary="查询用户聊天记录")
def get_history(user_id:str="default_user",skip:int=0,limit:int=100,db:Session=Depends(get_db)):
    records=get_chat_history(db,user_id,skip,limit)
    history=[
        {"id":record.id,
         "role":record.role,
         "content":record.content,
         "create_time":record.create_time.strftime("%Y-%m-%d %H:%M:%S")}
         for record in records
    ]
    return {
        "code":200,
        "message":"success",
        "data":{
            "user_id":user_id,
            "total":len(history),
            "history":history}
    }

#添加删除聊天记录接口
@app.delete("/history/{user_id}",tags=["聊天记录接口"],summary="删除用户聊天记录")
def delete_history(user_id:str="default_user",db:Session=Depends(get_db)):
    deleted_count=delete_chat_history(db,user_id)
    global chat_history
    chat_history.clear()
    return {
        "code":200,
        "message":"success",
        "data":{"user_id":user_id,"deleted_count":deleted_count,"message":"已删除用户的聊天记录并清空上下文"}
    }

#主程序入口
if __name__=="__main__":
    import uvicorn
    uvicorn.run("main:app",host="127.0.0.1",port=8000,reload=True)
