"""
Task 2.2: LangChain 多工具 Agent
=================================
目标：构建一个有 4-5 种工具的实用 Agent
      学习：工具设计、错误处理、输出解析、结构化输出

安装依赖：
  pip install langchain langchain-openai pydantic python-dotenv
"""

import os
import json
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain.tools import tool
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser

load_dotenv()


# ============================================================
# 工具设计原则：
# 1. 单一职责 — 每个工具只做一件事
# 2. 清晰描述 — description 越具体，LLM 选择越准确
# 3. 合理参数 — 参数类型和约束要明确
# 4. 防御性编程 — 工具内部处理异常，不向外抛
# ============================================================

@tool
def get_weather(city: str) -> str:
    """获取指定城市的当前天气信息，包括温度、天气状况、湿度"""
    weather_data = {
        "北京": json.dumps({"temp": 25, "condition": "晴天", "humidity": 45}, ensure_ascii=False),
        "上海": json.dumps({"temp": 28, "condition": "多云", "humidity": 65}, ensure_ascii=False),
        "深圳": json.dumps({"temp": 30, "condition": "阵雨", "humidity": 85}, ensure_ascii=False),
    }
    result = weather_data.get(city)
    if not result:
        return json.dumps({"error": f"未找到{city}的数据"}, ensure_ascii=False)
    return result


@tool
def calculate(expression: str) -> str:
    """安全计算数学表达式。支持加减乘除、幂运算、括号。示例: '(25 + 28) / 2'"""
    # 安全检查：只允许数字和基本运算符
    allowed = set("0123456789+-*/.() ")
    if not all(c in allowed for c in expression):
        return "错误：表达式包含不允许的字符"
    try:
        return str(eval(expression))
    except ZeroDivisionError:
        return "错误：除以零"
    except Exception as e:
        return f"计算错误: {e}"


@tool
def list_directory(path: str = ".") -> str:
    """列出指定目录下的文件和文件夹。默认为当前目录"""
    try:
        entries = os.listdir(path)
        files = [e for e in entries if os.path.isfile(os.path.join(path, e))]
        dirs = [e for e in entries if os.path.isdir(os.path.join(path, e))]
        result = {"files": files[:20], "directories": dirs[:20]}
        return json.dumps(result, ensure_ascii=False)
    except Exception as e:
        return f"错误: {e}"


@tool
def read_file(file_path: str) -> str:
    """读取文件内容。适用于文本文件，自动限制返回前 2000 字符"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read(2000)
        return content
    except FileNotFoundError:
        return f"错误：文件不存在 '{file_path}'"
    except UnicodeDecodeError:
        return f"错误：文件 '{file_path}' 不是文本文件"
    except Exception as e:
        return f"读取错误: {e}"


@tool
def count_lines(file_path: str) -> str:
    """统计文件的行数和字符数"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        return json.dumps({
            "file": file_path,
            "lines": len(lines),
            "characters": sum(len(line) for line in lines)
        }, ensure_ascii=False)
    except Exception as e:
        return f"错误: {e}"


# ============================================================
# 结构化输出 — 让 Agent 返回 Pydantic 对象而非自由文本
# ============================================================

class AnalysisResult(BaseModel):
    """Agent 的结构化输出"""
    summary: str = Field(description="分析总结")
    details: list[str] = Field(description="详细发现")
    recommendation: str = Field(description="建议")


# ============================================================
# Agent 创建
# ============================================================

def create_multi_tool_agent():
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    tools = [get_weather, calculate, list_directory, read_file, count_lines]

    prompt = ChatPromptTemplate.from_messages([
        ("system", """你是一个代码分析助手。你可以：
1. 列出目录结构
2. 读取文件内容
3. 统计文件信息
4. 计算数值
5. 查询天气（测试用）

请用中文回答。分析时要全面、有条理。"""),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}"),
    ])

    agent = create_tool_calling_agent(llm, tools, prompt)

    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        max_iterations=10,            # 复杂任务需要更多迭代
        handle_parsing_errors=True,    # 解析错误自动恢复
        verbose=True,
        return_intermediate_steps=True,  # 返回中间步骤（用于调试）
    )

    return agent_executor


# ============================================================
# 运行
# ============================================================

if __name__ == "__main__":
    agent = create_multi_tool_agent()

    # 实用任务：让 Agent 分析当前项目
    print("=" * 60)
    print("任务：分析项目目录结构")
    print("=" * 60)

    result = agent.invoke({
        "input": "请帮我分析当前目录下有哪些文件，读取 LEARNING_PLAN.md 的内容，并统计它有多少行"
    })

    print(f"\n最终回答:\n{result['output']}")

    # 查看中间步骤
    print(f"\n--- 调试信息 ---")
    print(f"总迭代步数: {len(result['intermediate_steps'])}")
    for step_action, step_result in result['intermediate_steps']:
        print(f"  工具: {step_action.tool} | 输入: {step_action.tool_input}")
