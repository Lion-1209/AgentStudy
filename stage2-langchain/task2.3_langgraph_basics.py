"""
Task 2.3: LangGraph 状态图基础
===============================
目标：理解 LangGraph 的核心概念——用图（节点+边）编排工作流

核心概念：
  节点(Node) = 一个处理步骤（函数）
  边(Edge) = 步骤之间的连接（确定性的）
  条件边(Conditional Edge) = 根据条件走不同路径
  状态(State) = 在节点之间传递的数据

LangGraph vs 手写 if-else：
  - 可视化：可以生成流程图
  - 可追踪：每一步的状态变化都有记录
  - 可恢复：可以在任意节点暂停/恢复
  - 可循环：支持 while 循环模式

安装依赖：
  pip install langgraph langchain-openai python-dotenv
"""

import os
import json
from typing import TypedDict, Annotated
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

load_dotenv()

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)


# ============================================================
# 第一步：定义状态（State）
# ============================================================
# 状态 = 在节点之间传递的数据结构
# 每个节点读取状态、修改状态、传给下一个节点

class WorkflowState(TypedDict):
    """工作流状态定义"""
    messages: Annotated[list, add_messages]  # 对话历史（自动追加）
    current_step: str          # 当前步骤名
    question: str              # 用户问题
    research_result: str       # 调研结果
    analysis_result: str       # 分析结果
    final_report: str          # 最终报告
    needs_more_research: bool  # 是否需要更多调研
    iteration_count: int       # 循环计数


# ============================================================
# 第二步：定义节点（Node）
# ============================================================
# 每个节点是一个函数，接收 state，返回 state 的更新

def research_node(state: WorkflowState) -> dict:
    """节点1：调研 — 收集信息"""
    print(f"  [调研节点] 处理问题: {state['question']}")

    prompt = f"""你是一个调研助手。请针对以下问题，收集关键信息，给出简洁的调研结果。
如果之前有分析结果指出信息不足，请补充调研。

问题: {state['question']}
之前的调研: {state.get('research_result', '无')}
分析反馈: {state.get('analysis_result', '无')}

请给出调研结果（200字以内）："""

    response = llm.invoke(prompt)
    return {
        "research_result": response.content,
        "current_step": "research"
    }


def analysis_node(state: WorkflowState) -> dict:
    """节点2：分析 — 基于调研结果进行分析"""
    print(f"  [分析节点] 分析调研结果")

    prompt = f"""你是一个分析助手。基于以下调研结果，进行分析并判断信息是否充足。

问题: {state['question']}
调研结果: {state['research_result']}

请回答两个问题：
1. 分析结论（200字以内）
2. 信息是否充足？如果不足，说明需要补充什么

格式：
结论: <你的分析>
充足: <是/否>
补充需求: <如果不足，需要补充什么>"""

    response = llm.invoke(prompt)

    needs_more = "否" in response.content.split("充足:")[0] if "充足:" in response.content else False

    return {
        "analysis_result": response.content,
        "needs_more_research": needs_more,
        "current_step": "analysis",
        "iteration_count": state.get("iteration_count", 0) + 1
    }


def report_node(state: WorkflowState) -> dict:
    """节点3：生成报告"""
    print(f"  [报告节点] 生成最终报告")

    prompt = f"""请基于以下信息，生成一份简洁的分析报告。

问题: {state['question']}
调研结果: {state['research_result']}
分析结论: {state['analysis_result']}

格式要求：
## 分析报告
### 问题
### 调研发现
### 结论
### 建议"""

    response = llm.invoke(prompt)
    return {
        "final_report": response.content,
        "current_step": "report"
    }


# ============================================================
# 第三步：定义路由（条件边）
# ============================================================

def should_continue_research(state: WorkflowState) -> str:
    """
    条件路由：判断是否需要继续调研

    返回值是下一个节点的名字
    """
    if state.get("needs_more_research") and state.get("iteration_count", 0) < 3:
        print(f"  [路由] 信息不足，回到调研节点 (第{state['iteration_count']}次)")
        return "research"
    else:
        print(f"  [路由] 信息充足，生成报告")
        return "report"


# ============================================================
# 第四步：构建图
# ============================================================

def build_workflow() -> StateGraph:
    """构建 LangGraph 工作流"""

    # 创建状态图
    workflow = StateGraph(WorkflowState)

    # 添加节点
    workflow.add_node("research", research_node)
    workflow.add_node("analysis", analysis_node)
    workflow.add_node("report", report_node)

    # 添加边 — 定义执行顺序
    workflow.add_edge(START, "research")       # 入口 → 调研
    workflow.add_edge("research", "analysis")  # 调研 → 分析
    # 分析 → 条件路由（继续调研 or 生成报告）
    workflow.add_conditional_edges(
        "analysis",
        should_continue_research,
        {"research": "research", "report": "report"}
    )
    workflow.add_edge("report", END)           # 报告 → 结束

    return workflow


# ============================================================
# 运行
# ============================================================

if __name__ == "__main__":
    # 编译工作流
    workflow = build_workflow()
    app = workflow.compile()

    # 可视化（需要 pip install grandalf）
    # try:
    #     img = app.get_graph().draw_mermaid_png()
    #     with open("workflow.png", "wb") as f:
    #         f.write(img)
    #     print("流程图已保存为 workflow.png")
    # except Exception:
    #     print("无法生成流程图（需要安装 grandalf）")

    # 打印图结构
    print("工作流结构:")
    print(app.get_graph().print_ascii())

    # 执行工作流
    print("\n" + "=" * 60)
    print("执行工作流")
    print("=" * 60)

    initial_state = {
        "messages": [],
        "question": "2026年 AI Agent 开发领域最重要的技术趋势是什么？",
        "research_result": "",
        "analysis_result": "",
        "final_report": "",
        "needs_more_research": False,
        "iteration_count": 0,
    }

    result = app.invoke(initial_state)

    print("\n" + "=" * 60)
    print("最终报告:")
    print("=" * 60)
    print(result["final_report"])
    print(f"\n总迭代次数: {result['iteration_count']}")

    # ============================================================
    # 对比手写 if-else 的思考：
    #
    # LangGraph 的价值不在于"能不能实现"，而在于：
    # 1. 流程可视化 — 复杂流程一目了然
    # 2. 状态追踪 — 每一步的状态变化都可查询
    # 3. 可恢复 — 可以在任意节点暂停，之后恢复执行
    # 4. 循环控制 — 内置重试、最大迭代等机制
    # 5. 人工介入 — interrupt_before 可以在关键节点暂停等人工确认
    #
    # 什么时候需要 LangGraph？
    # - 简单的线性流程 → 不需要，LangChain Agent 就够了
    # - 有条件分支和循环 → 需要
    # - 需要人工介入 → 需要
    # - 需要状态持久化 → 需要
    # ============================================================
