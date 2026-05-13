#导入必要的库
import os
from dotenv import load_dotenv

from dashscope import Generation

#加载环境变量
load_dotenv()

#获取API密钥    
dashscope_api_key = os.getenv("DASH_SCOPE_API_KEY")

def call_ai(message: str, chat_history: list):  
    """
    调用Qwen AI接口，支持上下文记忆
    param message: 用户输入的消息
    param chat_history: 当前用户的聊天历史上下文
    return: AI生成的回复
    """
    try:
        # 拼接上下文（创建副本，不修改原始列表，由 main.py 统一管理状态）
        messages = chat_history + [{"role":"user","content":message}]
        #调用Qwen AI接口
        response=Generation.call(
            model=os.getenv("QWEN_MODEL"),
            messages=messages,
            temperature=0.5,
            max_tokens=2048,
            result_format="message"
        )
        if response.status_code==200:
            ai_reply=response.output.choices[0].message.content.strip()
            return ai_reply
        else:
            return f"调用失败：{response.message}(错误码：{response.status_code})"
    except Exception as e:
        return f"系统错误{str(e)}（请检查API Key是否正确）"
    
if __name__=="__main__":
    #测试调用
    print("测试qwen调用")
    print("="*40)
    test_history = []
    print(call_ai("请介绍一下你自己", test_history))