"""
Task 1.1: 最小 ReAct 循环
========================
目标：用纯 Python 实现一个最小的 Agent 循环。
      不依赖任何框架，只有 LLM API 调用 + while 循环。

核心概念：Agent = LLM + Tool Use + Loop

ReAct 循环：
  Think（思考） → Act（行动） → Observe（观察） → 重复

安装依赖：
  pip install openai python-dotenv

使用前创建 .env 文件：
  OPENAI_API_KEY=sk-your-key-here
"""

import os
import re
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ============================================================
# 第一步：定义工具
# ============================================================
# Agent 的能力来自工具。每个工具就是一个普通函数。

def get_weather(city: str) -> str:
    """获取指定城市的天气（模拟数据）"""
    # 实际项目中这里会调用真实的天气 API
    weather_data = {
        "北京": "晴天，温度 25°C，空气质量良好",
        "上海": "多云，温度 28°C，有轻微雾霾",
        "深圳": "阵雨，温度 30°C，湿度 85%",
    }
    return weather_data.get(city, f"未找到{city}的天气数据")


def calculate(expression: str) -> str:
    """计算数学表达式"""
    try:
        # 注意：eval 在生产环境有安全风险，这里仅用于演示
        result = eval(expression)
        return str(result)
    except Exception as e:
        return f"计算错误: {e}"


def search_web(query: str) -> str:
    """搜索网络（模拟）"""
    # 实际项目中调用 Google/Bing/DuckDuckGo API
    return f"搜索结果：关于「{query}」的最新信息...（模拟数据）"


# 工具注册表：名字 → (函数, 描述, 参数描述)
TOOLS = {
    "get_weather": {
        "func": get_weather,
        "description": "获取指定城市的天气信息",
        "params": {"city": "城市名称，如'北京'"}
    },
    "calculate": {
        "func": calculate,
        "description": "计算数学表达式",
        "params": {"expression": "数学表达式，如 '2 + 3 * 4'"}
    },
    "search_web": {
        "func": search_web,
        "description": "搜索网络获取信息",
        "params": {"query": "搜索关键词"}
    }
}

# ============================================================
# 第二步：构建系统提示词
# ============================================================
# 这是最关键的部分——告诉 LLM 它是什么、能做什么、怎么输出

def build_system_prompt() -> str:
    tool_descriptions = "\n".join(
        f"  - {name}: {info['description']}。参数: {info['params']}"
        for name, info in TOOLS.items()
    )

    return f"""你是一个有用的AI助手。你可以使用以下工具来帮助用户：

{tool_descriptions}

当你需要使用工具时，请严格按以下格式输出：
Thought: <你的思考过程>
Action: <工具名称>
Action Input: <工具参数的 JSON>

当你有了足够的信息可以回答用户时，请输出：
Thought: <你的思考过程>
Final Answer: <最终回答>

重要：每次只能使用一个工具。等待工具返回结果后再决定下一步。"""


# ============================================================
# 第三步：ReAct 循环（Agent 的核心）
# ============================================================

def parse_action(text: str) -> tuple[str, str] | None:
    """从 LLM 输出中解析出动作和参数"""
    # 用正则提取 Action 和 Action Input
    action_match = re.search(r"Action:\s*(\w+)", text)
    input_match = re.search(r"Action Input:\s*(.+?)(?:\n|$)", text)

    if action_match and input_match:
        action = action_match.group(1).strip()
        action_input = input_match.group(1).strip()
        return action, action_input
    return None


def parse_final_answer(text: str) -> str | None:
    """从 LLM 输出中提取最终回答"""
    match = re.search(r"Final Answer:\s*(.+)", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return None


def run_agent(user_query: str, max_iterations: int = 5) -> str:
    """
    最小 Agent 循环

    这就是 Agent 的全部核心逻辑：
    1. 把用户问题发给 LLM
    2. LLM 回复中包含 Action → 执行工具，把结果喂回 LLM → 回到步骤 1
    3. LLM 回复中包含 Final Answer → 返回给用户
    4. 超过最大循环次数 → 强制停止
    """
    # 消息历史（这就是短期记忆）
    messages = [
        {"role": "system", "content": build_system_prompt()},
        {"role": "user", "content": user_query}
    ]

    for i in range(max_iterations):
        print(f"\n--- 迭代 {i + 1} ---")

        # 调用 LLM
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # 开发阶段用便宜模型
            messages=messages,
            temperature=0,
        )

        assistant_message = response.choices[0].message.content
        print(f"LLM 输出:\n{assistant_message}")

        # 检查是否有最终回答
        final_answer = parse_final_answer(assistant_message)
        if final_answer:
            return final_answer

        # 检查是否需要调用工具
        action_result = parse_action(assistant_message)
        if action_result:
            action_name, action_input = action_result

            if action_name in TOOLS:
                # 执行工具
                print(f"执行工具: {action_name}({action_input})")
                tool_result = TOOLS[action_name]["func"](action_input)
                print(f"工具结果: {tool_result}")

                # 把 LLM 的输出和工具结果都加入消息历史
                messages.append({"role": "assistant", "content": assistant_message})
                messages.append({
                    "role": "user",
                    "content": f"Observation: {tool_result}\n\n请继续思考。"
                })
            else:
                # 工具不存在
                messages.append({"role": "assistant", "content": assistant_message})
                messages.append({
                    "role": "user",
                    "content": f"Observation: 错误 - 工具 '{action_name}' 不存在。可用工具: {list(TOOLS.keys())}"
                })
        else:
            # LLM 没有输出 Action 也没有 Final Answer，提示它继续
            messages.append({"role": "assistant", "content": assistant_message})
            messages.append({
                "role": "user",
                "content": "请使用工具或给出最终回答。如果已有足够信息，请用 'Final Answer:' 格式回答。"
            })

    return "抱歉，我无法在规定步数内完成任务。"


# ============================================================
# 运行
# ============================================================

if __name__ == "__main__":
    # 测试 1：简单工具调用
    print("=" * 60)
    print("测试 1：查天气")
    print("=" * 60)
    result = run_agent("北京今天天气怎么样？")
    print(f"\n最终回答: {result}")

    # 测试 2：多步推理（需要调用多个工具）
    print("\n" + "=" * 60)
    print("测试 2：多步推理")
    print("=" * 60)
    result = run_agent("帮我查一下北京和上海的天气，然后算一下两个城市的温差是多少")
    print(f"\n最终回答: {result}")
