"""
Task 3.1: OpenAI Agents SDK
============================
目标：用 OpenAI Agents SDK 实现和 Task 2.2 同等功能的 Agent
      体验"去框架化"的现代设计

核心概念：
  Agent = 指令 + 工具 + 模型
  Runner = 执行器，封装了循环
  Handoff = Agent 之间的任务交接

对比 LangChain：
  - 代码更少（通常少 30-50%）
  - 抽象更少（没有 PromptTemplate、AgentExecutor 等概念）
  - 用原生 Python 特性（dataclass、async）而非自定义抽象

安装依赖：
  pip install openai-agents python-dotenv
"""

import os
import asyncio
import sys
from agents import Agent, Runner, function_tool
from dotenv import load_dotenv

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from llm_config import get_provider, PROVIDERS

load_dotenv()

# OpenAI Agents SDK 通过环境变量读取配置
# 设置兼容的 base_url 和 api_key，使 SDK 能用 DeepSeek/智谱
_, provider_config = get_provider()
os.environ["OPENAI_API_KEY"] = os.getenv(provider_config["api_key_env"])
os.environ["OPENAI_BASE_URL"] = provider_config["base_url"]


# ============================================================
# 工具定义 — 比LangChain的 @tool 更简洁
# ============================================================

@function_tool
def get_weather(city: str) -> str:
    """获取指定城市的天气信息"""
    weather_data = {
        "北京": "晴天 25°C",
        "上海": "多云 28°C",
        "深圳": "阵雨 30°C",
    }
    return weather_data.get(city, f"未找到{city}的天气")


@function_tool
def calculate(expression: str) -> str:
    """计算数学表达式，例如 '(25 + 28) / 2'"""
    try:
        return str(eval(expression))
    except Exception as e:
        return f"计算错误: {e}"


@function_tool
def read_file(file_path: str) -> str:
    """读取文件内容，返回前 2000 字符"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()[:2000]
    except FileNotFoundError:
        return f"文件不存在: {file_path}"
    except Exception as e:
        return f"错误: {e}"


@function_tool
def list_directory(path: str = ".") -> str:
    """列出目录下的文件和文件夹"""
    try:
        entries = os.listdir(path)
        files = [e for e in entries if os.path.isfile(os.path.join(path, e))]
        dirs = [e for e in entries if os.path.isdir(os.path.join(path, e))]
        return f"文件: {files[:20]}\n文件夹: {dirs[:20]}"
    except Exception as e:
        return f"错误: {e}"


# ============================================================
# Agent 定义 — 比 LangChain 简洁得多
# ============================================================

# 主 Agent：通用助手
main_agent = Agent(
    name="代码分析助手",
    instructions="""你是一个有用的助手。你可以：
1. 列出目录结构
2. 读取文件内容
3. 计算数值
4. 查询天气

请用中文回答。""",
    tools=[get_weather, calculate, read_file, list_directory],
    model=provider_config["model"],
)


# ============================================================
# 运行
# ============================================================

async def main():
    print("=" * 60)
    print("OpenAI Agents SDK 测试")
    print("=" * 60)

    # 同一个任务，对比 Task 2.2 的代码量
    result = await Runner.run(
        main_agent,
        input="帮我查一下北京和上海的天气，算算温差是多少",
    )

    print(f"\n最终回答: {result.final_output}")

    # ============================================================
    # 对比 LangChain (Task 2.2)：
    #
    # LangChain 需要的组件：
    #   - ChatPromptTemplate
    #   - {agent_scratchpad} 占位符
    #   - create_tool_calling_agent()
    #   - AgentExecutor(max_iterations=..., handle_parsing_errors=...)
    #   - agent.invoke({"input": ...})
    #
    # OpenAI Agents SDK：
    #   - Agent(name, instructions, tools)
    #   - Runner.run(agent, input=...)
    #
    # 少了什么？
    #   - 不需要 PromptTemplate（instructions 就是普通字符串）
    #   - 不需要 scratchpad 占位符（框架自动处理）
    #   - 不需要 AgentExecutor 配置（Runner 更简洁）
    #   - 异步优先（Runner.run 是 async）
    #
    # 多了什么？
    #   - Handoff 机制（Agent 间任务交接，下一节学）
    #   - Guardrails（输入输出安全检查）
    #   - 原生 tracing 支持
    # ============================================================


if __name__ == "__main__":
    asyncio.run(main())
