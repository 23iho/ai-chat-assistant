# 导入必要的库
import os
from dotenv import load_dotenv
import dashscope
from dashscope import Generation

# 加载.env文件中的环境变量
load_dotenv()

# 单API Key初始化（核心，就这一行）
dashscope.api_key = os.getenv("QWEN_API_KEY")

def call_ai(message: str, history: list = None) -> str:
    """
    调用Qwen AI接口，支持上下文记忆
    :param message: 用户输入的消息
    :param history: 聊天历史记录（格式：[{"role": "user/assistant", "content": "消息内容"}]）
    :return: AI的回答
    """
    try:
        # 拼接上下文（有历史记录就带上）
        messages = history.copy() if history else []
        messages.append({"role": "user", "content": message})

        # 调用Qwen API（单API Key直连）
        response = Generation.call(
            model=os.getenv("QWEN_MODEL"),
            messages=messages,
            temperature=0.7,
            max_tokens=1024,
            result_format="message"
        )

        # 提取AI回复
        if response.status_code == 200:
            return response.output.choices[0].message.content.strip()
        else:
            return f"调用失败：{response.message}（错误码：{response.code}）"

    except Exception as e:
        return f"系统错误：{str(e)}（请检查API Key是否正确）"

# 测试函数（保存后直接运行这个文件，就能验证是否成功）
if __name__ == "__main__":
    print("测试Qwen单API Key调用...")
    print("AI：", call_ai("你好，我是大一学生，正在学习后端开发"))