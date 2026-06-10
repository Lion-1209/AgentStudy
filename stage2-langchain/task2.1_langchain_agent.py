"""
Task 2.1: LangChain 基础 Agent
===============================
目标：用 LangChain 重新实现 Task 1.2 的功能
      体验框架的标准化和便利性

对比 Task 1.2：
  - 不用手写工具 schema → @tool 装饰器自动生成
  - 不用手写循环 → AgentExecutor 自动管理
  - 不用手写解析 → 框架处理 Function Calling

安装依赖：
  pip install langchain langchain-openai python-dotenv
"""

import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain.tools import tool
from langchain_core.prompts import ChatPromptTemplate

load_dotenv()

# ============================================================
# 工具定义 — 用 @tool 装饰器，比手写 schema 简洁很多
# ============================================================
# LangChain 会自动从函数签名和 docstring 生成 JSON Schema

@tool
def get_weather(city: str) -> str:
    """获取指定城市的天气信息"""
    weather_data = {
        "北京": "晴天 25°C",
        "上海": "多云 28°C",
        "深圳": "阵雨 30°C",
    }
    return weather_data.get(city, f"未找到{city}的天气")


@tool
def calculate(expression: str) -> str:
    """计算数学表达式，例如 '(25 + 28) / 2'"""
    try:
        return str(eval(expression))
    except Exception as e:
        return f"计算错误: {e}"


@tool
def read_file(file_path: str) -> str:
    """读取本地文件的内容，返回最多 2000 字符"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()[:2000]
    except FileNotFoundError:
        return f"文件不存在: {file_path}"
    except Exception as e:
        return f"读取错误: {e}"


# ============================================================
# Agent 创建
# ============================================================

def create_agent():
    # 1. LLM
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0,
    )

    # 2. 工具列表
    tools = [get_weather, calculate, read_file]

    # 3. 提示词模板
    # 注意 {agent_scratchpad} 是必须的，用于存放中间推理过程
    prompt = ChatPromptTemplate.from_messages([
        ("system", "你是一个有用的助手，可以使用工具帮助用户。用中文回答。"),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}"),  # 必须：存放 Think/Act/Observe 过程
    ])

    # 4. 创建 Agent
    # create_tool_calling_agent = 使用 Function Calling 的 Agent
    # 还有 create_react_agent（ReAct 文本解析）等
    agent = create_tool_calling_agent(llm, tools, prompt)

    # 5. 创建 AgentExecutor — 封装了 ReAct 循环
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        max_iterations=5,           # 最大迭代次数
        handle_parsing_errors=True,  # 解析错误时不崩溃
        verbose=True,                # 打印中间过程（调试用）
    )

    return agent_executor


# ============================================================
# 运行
# ============================================================

if __name__ == "__main__":
    agent = create_agent()

    print("=" * 60)
    print("LangChain Agent 测试")
    print("=" * 60)

    result = agent.invoke({
        "input": "帮我查一下北京和上海的天气，算算温差"
    })
    print(f"\n最终回答: {result['output']}")

    # ============================================================
    # 对比 Task 1.2 的思考：
    #
    # 1. 代码量减少了多少？
    #    - 不需要手写 TOOLS_SCHEMA（50+ 行的 JSON）
    #    - 不需要手写 while 循环和解析逻辑
    #    - @tool 装饰器自动从 docstring + 类型注解生成 schema
    #
    # 2. 多了什么？
    #    - ChatPromptTemplate 抽象
    #    - {agent_scratchpad} 占位符
    #    - AgentExecutor 配置项
    #
    # 3. 代价是什么？
    #    - 需要理解 LangChain 的抽象概念
    #    - 框架版本更新可能破坏代码
    #    - 调试困难（verbose=True 帮助很大）
    # ============================================================
