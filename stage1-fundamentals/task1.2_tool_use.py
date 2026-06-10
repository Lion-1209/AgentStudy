"""
Task 1.2: Tool Use 机制（结构化函数调用）
==========================================
目标：在 Task 1.1 基础上，使用 OpenAI 的原生 Function Calling API，
      而不是用正则解析文本。这是生产环境的做法。

核心改进：
  Task 1.1：LLM 输出文本 → 正则解析 → 调用工具  （脆弱、不可靠）
  Task 1.2：LLM 输出结构化 JSON → 直接调用工具    （可靠、生产级）

安装依赖：
  pip install openai python-dotenv
"""

import os
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# ============================================================
# 工具定义 — 使用 OpenAI Function Calling 的标准格式
# ============================================================
# 这个 schema 格式是 OpenAI/Anthropic 等厂商共同遵守的标准
# 它告诉 LLM：有哪些工具、每个工具接受什么参数

def get_weather(city: str) -> str:
    weather_data = {
        "北京": "晴天 25°C",
        "上海": "多云 28°C",
        "深圳": "阵雨 30°C",
    }
    return weather_data.get(city, f"未找到{city}的天气")


def calculate(expression: str) -> str:
    try:
        return str(eval(expression))
    except Exception as e:
        return f"计算错误: {e}"


def read_file(file_path: str) -> str:
    """读取文件内容"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()[:2000]  # 限制长度，避免 token 爆炸
    except FileNotFoundError:
        return f"文件不存在: {file_path}"
    except Exception as e:
        return f"读取错误: {e}"


# 工具映射表：函数 → schema
TOOL_FUNCTIONS = {
    "get_weather": get_weather,
    "calculate": calculate,
    "read_file": read_file,
}

# 关键：这就是 Function Calling 的工具定义格式
# description 和 parameters 的质量直接决定 LLM 能否正确使用工具
TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "获取指定城市的当前天气信息",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "城市名称，例如'北京'、'上海'"
                    }
                },
                "required": ["city"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calculate",
            "description": "计算数学表达式，支持加减乘除和常用数学函数",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "要计算的数学表达式，例如 '(25 + 28) / 2'"
                    }
                },
                "required": ["expression"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "读取本地文件的内容",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "要读取的文件路径"
                    }
                },
                "required": ["file_path"]
            }
        }
    }
]


# ============================================================
# Agent 核心 — 使用 Function Calling
# ============================================================

def run_agent_with_tools(user_query: str, max_iterations: int = 5) -> str:
    """
    使用原生 Function Calling 的 Agent 循环

    与 Task 1.1 的区别：
    1. 不需要自己写正则解析 LLM 输出
    2. 不需要在 system prompt 中教 LLM 输出格式
    3. LLM 自动生成结构化的工具调用请求
    4. 更可靠、更准确
    """
    messages = [
        {
            "role": "system",
            "content": "你是一个有用的助手，可以使用工具来帮助用户回答问题。请使用中文回答。"
        },
        {
            "role": "user",
            "content": user_query
        }
    ]

    for i in range(max_iterations):
        print(f"\n--- 迭代 {i + 1} ---")

        # 调用 LLM，传入工具定义
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            tools=TOOLS_SCHEMA,          # 关键：传入工具定义
            tool_choice="auto",          # 让 LLM 自己决定是否调用工具
            temperature=0,
        )

        message = response.choices[0].message

        # 情况 1：LLM 决定调用工具
        if message.tool_calls:
            # 把 assistant 的工具调用消息加入历史
            messages.append(message)

            for tool_call in message.tool_calls:
                func_name = tool_call.function.name
                func_args = json.loads(tool_call.function.arguments)

                print(f"  调用工具: {func_name}({func_args})")

                # 执行工具
                if func_name in TOOL_FUNCTIONS:
                    result = TOOL_FUNCTIONS[func_name](**func_args)
                else:
                    result = f"错误：未知工具 {func_name}"

                print(f"  工具结果: {result}")

                # 把工具结果加入消息历史
                # 注意：必须用 tool_call_id 关联请求和响应
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": str(result)
                })

        # 情况 2：LLM 给出最终回答
        else:
            if message.content:
                return message.content

    return "达到最大迭代次数，任务未完成。"


# ============================================================
# 运行
# ============================================================

if __name__ == "__main__":
    # 对比 Task 1.1：同样的问题，但用 Function Calling 实现
    # 你会发现 LLM 的工具调用准确率和可靠性大幅提升

    print("=" * 60)
    print("测试 1：单步工具调用")
    print("=" * 60)
    result = run_agent_with_tools("北京今天天气怎么样？")
    print(f"\n回答: {result}")

    print("\n" + "=" * 60)
    print("测试 2：多步推理 — 需要 Agent 自动规划调用顺序")
    print("=" * 60)
    result = run_agent_with_tools(
        "帮我查一下北京和上海的天气，算算温差是多少，再读一下当前目录下的 LEARNING_PLAN.md 文件"
    )
    print(f"\n回答: {result}")

    # ============================================================
    # 思考题：
    # 1. 对比 Task 1.1 和 1.2，Function Calling 解决了什么问题？
    #    答：消除了文本解析的不可靠性，LLM 直接输出结构化 JSON
    #
    # 2. tool_choice="auto" 意味着什么？还有哪些选项？
    #    答：auto = LLM 自行决定是否调用工具
    #       none = 禁止调用工具
    #       required = 必须调用工具
    #       {"type": "function", "function": {"name": "xxx"}} = 强制调用指定工具
    #
    # 3. 如果工具返回结果很长，怎么避免 token 爆炸？
    #    答：在工具函数内部截断/摘要，限制返回长度
    # ============================================================
