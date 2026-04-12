#导入必要的库
import os
from dotenv import load_dotenv

from dashscope import Generation

#加载环境变量
load_dotenv()
#设置全局变量：保存用户聊天历史(上下文)
chat_history=[]

#获取API密钥    
dashscope_api_key = os.getenv("DASH_SCOPE_API_KEY")

def call_ai(message:str,clear_history:bool = False):  
    global chat_history
    """
    调用Qwen AI接口，支持上下文记忆
    param message: 用户输入的消息
    param clear_history: 是否清空上下文(默认不清空)
    return: AI生成的回复
    """
    #先检查是否需要清空上下文
    if clear_history:
        chat_history=[]
    try:
        #拼接上下文
        chat_history.append({"role":"user","content":message})
        #调用Qwen AI接口
        response=Generation.call(
            model=os.getenv("QWEN_MODEL"),
            messages=chat_history,
            temperature=0.5,
            max_tokens=2048,
            result_format="message"
        )
        if response.status_code==200:
            ai_reply=response.output.choices[0].message.content.strip()
            chat_history.append({"role":"assistant","content":ai_reply})
            return ai_reply
        else:
            return f"调用失败：{response.message}(错误码：{response.status_code})"
    except Exception as e:
        return f"系统错误{str(e)}（请检查API Key是否正确）"
    
if __name__=="__main__":
    #测试调用
    print("测试qwen调用")
    print("="*40)
    print(call_ai("请介绍一下你自己"))

  
  