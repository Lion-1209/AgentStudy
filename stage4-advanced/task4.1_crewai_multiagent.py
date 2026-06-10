"""
Task 4.1: CrewAI 多 Agent 协作
================================
目标：用 CrewAI 实现 3 个 Agent 协作完成技术调研报告

核心概念：
  Agent = 角色（Role）+ 目标（Goal）+ 背景故事（Backstory）
  Task = 任务描述 + 预期输出 + 指定 Agent
  Crew = 一组 Agent + 一组 Task + 执行流程（sequential/hierarchical）

CrewAI 的设计哲学：
  像管理一个团队——你定义角色和任务，框架负责分配和执行

安装依赖：
  pip install crewai crewai-tools python-dotenv
  注意：CrewAI 需要 Python 3.10+
"""

import os
import sys
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from llm_config import get_provider, PROVIDERS

load_dotenv()

# CrewAI 通过环境变量读取 LLM 配置
_, provider_config = get_provider()
os.environ["OPENAI_API_KEY"] = os.getenv(provider_config["api_key_env"])
os.environ["OPENAI_API_BASE"] = provider_config["base_url"]
os.environ["OPENAI_MODEL_NAME"] = provider_config["model"]


# ============================================================
# 定义 3 个 Agent — 像组建一个团队
# ============================================================

# Agent 1：调研员 — 负责收集信息
researcher = Agent(
    role="技术调研分析师",
    goal="收集关于指定技术主题的全面、准确的信息",
    backstory="""你是一位经验丰富的技术调研分析师，
    擅长从多个角度分析技术趋势。你会从技术特点、市场应用、
    优缺点等多个维度来调研一个技术话题。你的调研报告总是
    数据详实、逻辑清晰。""",
    verbose=True,
    allow_delegation=False,  # 不允许把任务转给别人
)

# Agent 2：分析师 — 负责深度分析
analyst = Agent(
    role="技术架构分析师",
    goal="基于调研结果，进行深入的技术分析和评估",
    backstory="""你是一位资深技术架构师，有 15 年的软件架构经验。
    你善于从工程实践的角度评估技术的可行性、成熟度和风险。
    你的分析总是切中要害，能指出技术的局限性和潜在陷阱。""",
    verbose=True,
    allow_delegation=False,
)

# Agent 3：写手 — 负责撰写报告
writer = Agent(
    role="技术文档工程师",
    goal="基于调研和分析结果，撰写结构清晰、易读的技术报告",
    backstory="""你是一位专业的技术文档工程师，
    擅长将复杂的技术概念转化为清晰易懂的文字。
    你的报告总是结构清晰、重点突出、结论明确。
    你会用 Markdown 格式撰写，包含表格和代码示例。""",
    verbose=True,
    allow_delegation=False,
)


# ============================================================
# 定义 3 个任务 — 像分配项目工作
# ============================================================

# Task 1：调研
research_task = Task(
    description="""调研以下技术主题：{topic}

    请收集以下信息：
    1. 技术背景和发展历史
    2. 核心概念和架构
    3. 主要的框架/工具
    4. 典型应用场景
    5. 当前社区热度和发展趋势
    """,
    expected_output="一份结构化的调研报告，包含上述 5 个方面的详细信息",
    agent=researcher,
)

# Task 2：分析
analysis_task = Task(
    description="""基于调研员提供的调研报告，对 {topic} 进行深入分析：

    1. 技术成熟度评估（是否适合生产使用）
    2. 学习曲线和上手难度
    3. 与替代方案的对比
    4. 适用场景和不适用场景
    5. 潜在风险和注意事项
    """,
    expected_output="一份深入的技术分析报告，包含评估结论和建议",
    agent=analyst,
    context=[research_task],  # 关键：这个任务依赖调研任务的结果
)

# Task 3：撰写报告
writing_task = Task(
    description="""基于调研和分析结果，撰写一份关于 {topic} 的完整技术报告。

    报告要求：
    - 使用 Markdown 格式
    - 包含摘要、正文、结论
    - 正文分为调研发现和分析评估两大部分
    - 结论包含明确的学习建议
    - 控制在 1000 字左右
    """,
    expected_output="一份格式规范、内容完整的 Markdown 技术报告",
    agent=writer,
    context=[research_task, analysis_task],  # 依赖前两个任务
)


# ============================================================
# 组建 Crew — 像启动一个项目
# ============================================================

def create_research_crew(topic: str) -> Crew:
    """创建一个技术调研团队"""

    # 用 .format() 填入 topic
    research_task.description = research_task.description.format(topic=topic)
    analysis_task.description = analysis_task.description.format(topic=topic)
    writing_task.description = writing_task.description.format(topic=topic)

    crew = Crew(
        agents=[researcher, analyst, writer],
        tasks=[research_task, analysis_task, writing_task],
        process=Process.sequential,  # 顺序执行：调研 → 分析 → 写报告
        verbose=True,
    )

    return crew


# ============================================================
# 运行
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("CrewAI 多 Agent 协作：技术调研报告")
    print("=" * 60)

    crew = create_research_crew("AI Agent 开发框架对比（LangGraph vs OpenAI Agents SDK）")

    result = crew.kickoff()

    print("\n" + "=" * 60)
    print("最终报告:")
    print("=" * 60)
    print(result)

    # ============================================================
    # CrewAI 的设计模式思考：
    #
    # 优点：
    #   - 代码极其简洁，角色定义直观
    #   - 任务依赖关系清晰（context 参数）
    #   - 适合"分工协作"类任务
    #
    # 缺点：
    #   - 控制粒度较粗，难以精细控制流程
    #   - 多次 LLM 调用，成本较高
    #   - Agent 间通信通过 context 隐式传递，不够透明
    #
    # 对比 LangGraph：
    #   CrewAI = 声明式（定义角色和任务，框架编排）
    #   LangGraph = 命令式（画流程图，精确控制）
    # ============================================================
