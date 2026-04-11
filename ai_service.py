#导入必要的库
import os
from dotenv import load_dotenv

from dashscope import Generation

#加载环境变量

load_dotenv()

#获取API密钥    
dashscope_api_key = os.getenv("DASH_SCOPE_API_KEY")

def call_ai(message:str,history:list=None)->str:
    """
    调用Qwen AI接口，支持上下文记忆
    param message: 用户输入的消息
    param history:聊天历史记录（格式：[{"role":"user/assistant","content":"..."}]）
    return: AI生成的回复
    """
    try:
        #拼接上下文
        messages=history.copy() if history else []
        messages.append({"role":"user","content":message})
        #调用Qwen AI接口
        response=Generation.call(
            model="qwen2.5-3b-instruct",
            messages=messages,
            temperature=0.5,
            max_tokens=2048,
            result_format="message"
        )
        if response.status_code==200:
            return response.output.choices[0].message.content.strip()
        else:
            return f"调用失败：{response.message}(错误码：{response.status_code})"
    except Exception as e:
        return f"系统错误{str(e)}（请检查API Key是否正确）"
    
if __name__=="__main__":
    #测试调用
    print("测试qwen调用")
    print("="*40)
    print(call_ai("请介绍一下你自己"))

  
  