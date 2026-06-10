"""
Task 3.2: Claude Agent SDK
===========================
目标：用 Claude Agent SDK 构建 Agent
      体验与 Claude Code 同源的运行时

核心概念：
  AgentLoop = Claude Code 的核心运行循环
  内置工具 = Read, Edit, Bash, Grep, Glob, WebSearch, WebFetch, Write
  MCP = Model Context Protocol，标准化的工具协议

注意：Claude Agent SDK 需要额外的安装步骤，
      具体请参考 https://github.com/anthropics/claude-agent-sdk-python

安装依赖：
  pip install claude-agent-sdk python-dotenv
"""

import os
import asyncio
from dotenv import load_dotenv

load_dotenv()

# ============================================================
# Claude Agent SDK 的两种用法
# ============================================================

# --- 方式一：直接使用 Claude API（推荐先学这个理解原理）---

from anthropic import Anthropic

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


def simple_claude_agent(user_query: str):
    """
    用 Claude API 直接实现 Agent 循环
    结构和 Task 1.2 非常相似，只是换成了 Anthropic API
    """
    # Claude 的工具定义格式（与 OpenAI 略有不同）
    tools = [
        {
            "name": "get_weather",
            "description": "获取指定城市的天气信息",
            "input_schema": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "城市名称"
                    }
                },
                "required": ["city"]
            }
        },
        {
            "name": "calculate",
            "description": "计算数学表达式",
            "input_schema": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "数学表达式"
                    }
                },
                "required": ["expression"]
            }
        }
    ]

    def execute_tool(name: str, input_data: dict) -> str:
        if name == "get_weather":
            weather = {"北京": "晴天 25°C", "上海": "多云 28°C", "深圳": "阵雨 30°C"}
            return weather.get(input_data["city"], f"未找到{input_data['city']}的天气")
        elif name == "calculate":
            try:
                return str(eval(input_data["expression"]))
            except Exception as e:
                return f"错误: {e}"
        return f"未知工具: {name}"

    messages = [{"role": "user", "content": user_query}]

    for i in range(5):
        print(f"\n--- 迭代 {i + 1} ---")

        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            tools=tools,
            messages=messages,
        )

        # Claude 的返回格式：content 是一个列表
        # 可能包含 text_block 和 tool_use_block
        has_tool_use = False
        tool_results = []

        for block in response.content:
            if block.type == "text":
                print(f"  Claude: {block.text}")
                return block.text  # 最终回答
            elif block.type == "tool_use":
                has_tool_use = True
                print(f"  调用工具: {block.name}({block.input})")
                result = execute_tool(block.name, block.input)
                print(f"  工具结果: {result}")
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result
                })

        if has_tool_use:
            # 把 assistant 的工具调用和工具结果都加入消息
            messages.append({"role": "assistant", "content": response.content})
            messages.append({"role": "user", "content": tool_results})

    return "达到最大迭代次数。"


# --- 方式二：使用 Claude Agent SDK（更高级的封装）---

async def claude_agent_sdk_example():
    """
    使用 claude-agent-sdk 封装

    Claude Agent SDK 提供了和 Claude Code 相同的运行时：
    - 内置 8 个工具（Read, Edit, Bash, Grep, Glob, WebSearch, WebFetch, Write）
    - 自动管理上下文和 token
    - 支持 MCP 协议
    """
    # 安装后取消注释以下代码
    # from claude_agent_sdk import AgentLoop, ClaudeCodeAgent
    #
    # agent = ClaudeCodeAgent(
    #     model="claude-sonnet-4-20250514",
    #     instructions="你是一个代码分析助手，用中文回答。",
    # )
    #
    # result = await agent.run("分析当前目录下的项目结构")
    # print(result)

    print("Claude Agent SDK 示例（需要安装 claude-agent-sdk）")
    print("请参考: https://github.com/anthropics/claude-agent-sdk-python")


# ============================================================
# 运行
# ============================================================

if __name__ == "__main__":
    # 使用方式一：直接 API
    print("=" * 60)
    print("Claude Agent（直接 API）")
    print("=" * 60)

    result = simple_claude_agent("帮我查一下北京和上海的天气，算算温差")
    print(f"\n最终回答: {result}")

    # 使用方式二：Claude Agent SDK
    print("\n" + "=" * 60)
    print("Claude Agent SDK")
    print("=" * 60)
    asyncio.run(claude_agent_sdk_example())

    # ============================================================
    # 对比总结：
    #
    # OpenAI Function Calling vs Anthropic Tool Use：
    #   格式几乎相同（都是 JSON schema），但有细节差异
    #   - OpenAI: tools 参数，response.choices[0].message.tool_calls
    #   - Claude: tools 参数，response.content 中的 tool_use blocks
    #   - OpenAI tool result: {"role": "tool", "tool_call_id": ...}
    #   - Claude tool result: {"role": "user", "content": [tool_result blocks]}
    #
    # 关键区别：Claude 的 tool result 是作为 user 消息发送的
    # ============================================================
