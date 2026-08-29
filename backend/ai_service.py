#导入必要的库
import os
from dotenv import load_dotenv

from dashscope import Generation

#加载环境变量
load_dotenv()

#获取API密钥
# 注：dashscope SDK 同时认 DASHSCOPE_API_KEY 这个环境变量，
# 如果你想直接用 SDK 默认行为，可以省掉这一行。
dashscope_api_key = os.getenv("DASH_SCOPE_API_KEY") or os.getenv("DASHSCOPE_API_KEY")

def call_ai(message: str, chat_history: list):
    """
    调用 Qwen AI 接口（阻塞式），返回完整回复。
    用于测试 / Swagger 演示 / 不需要流式的场景。
    """
    try:
        # 拼接上下文（创建副本，不修改原始列表，由 main.py 统一管理状态）
        messages = chat_history + [{"role":"user","content":message}]
        response = Generation.call(
            model=os.getenv("QWEN_MODEL"),
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


def stream_ai(message: str, chat_history: list):
    """
    流式调用 Qwen，逐 token yield 字符串片段。

    用法：
        for chunk in stream_ai(msg, history):
            ...  # chunk 是 str，可能是 ''
    异常情况通过 raise 抛出，由调用方决定怎么呈现给前端。
    """
    messages = chat_history + [{"role": "user", "content": message}]
    for resp in Generation.call(
        model=os.getenv("QWEN_MODEL"),
        messages=messages,
        temperature=0.5,
        max_tokens=2048,
        result_format="message",
        stream=True,
        incremental_output=True,  # 增量输出，避免每个 chunk 都重复
    ):
        if resp.status_code == 200:
            chunk = resp.output.choices[0].message.content
            if chunk:
                yield chunk
        else:
            raise RuntimeError(f"Qwen 调用失败：{resp.message}(错误码：{resp.status_code})")


if __name__=="__main__":
    #测试调用
    print("测试 qwen 调用（阻塞）")
    print("="*40)
    test_history = []
    print(call_ai("请介绍一下你自己", test_history))
    print()
    print("测试 qwen 调用（流式）")
    print("="*40)
    for chunk in stream_ai("用一句话介绍自己", []):
        print(chunk, end="", flush=True)
    print()