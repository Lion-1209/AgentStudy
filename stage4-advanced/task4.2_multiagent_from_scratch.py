"""
Task 4.2: 从零实现 Multi-Agent（不用框架）
============================================
目标：不用任何框架，自己实现 Agent 之间的协作
      理解 Multi-Agent 的本质：一个 Agent 的输出 = 另一个 Agent 的输入

核心模式：
  1. Pipeline（管道）—— Agent 按顺序依次处理
  2. Supervisor（监督者）—— 一个 Agent 分发任务给其他 Agent
  3. Debate（辩论）—— Agent 之间互相质疑和修正

这里实现 Pipeline + Supervisor 两种模式。

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
# 最小 Agent 类
# ============================================================

class SimpleAgent:
    """最小 Agent：名字 + system prompt + LLM 调用"""

    def __init__(self, name: str, system_prompt: str, model: str = "gpt-4o-mini"):
        self.name = name
        self.system_prompt = system_prompt
        self.model = model

    def run(self, user_input: str) -> str:
        """执行一次 LLM 调用"""
        response = client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": user_input}
            ],
            temperature=0,
        )
        result = response.choices[0].message.content
        print(f"  [{self.name}] 输出长度: {len(result)} 字符")
        return result


# ============================================================
# 模式一：Pipeline（管道模式）
# ============================================================

def pipeline_mode(query: str) -> str:
    """
    Pipeline 模式：Agent 串行处理

    用户输入 → Agent1 处理 → Agent2 处理 → Agent3 处理 → 最终输出

    本质：前一个的输出是后一个的输入，就像 Unix 管道
      cat file | grep pattern | sort | uniq
    """
    print("\n" + "=" * 60)
    print("Pipeline 模式")
    print("=" * 60)

    # 定义三个专职 Agent
    researcher = SimpleAgent(
        name="调研员",
        system_prompt="你是调研分析师。对给定的主题进行简明调研，列出 3-5 个关键发现。用中文。控制在 200 字以内。"
    )

    analyst = SimpleAgent(
        name="分析师",
        system_prompt="你是技术分析师。基于调研结果，给出深入的分析和评估。用中文。控制在 200 字以内。"
    )

    writer = SimpleAgent(
        name="写手",
        system_prompt="你是技术写手。基于调研和分析结果，写一份简洁的总结报告。用中文。用 Markdown 格式。"
    )

    # 管道执行
    print(f"\n用户输入: {query}")

    step1_result = researcher.run(query)
    print(f"\n--- 调研结果 ---\n{step1_result[:200]}...")

    step2_result = analyst.run(step1_result)
    print(f"\n--- 分析结果 ---\n{step2_result[:200]}...")

    step3_result = writer.run(step2_result)
    print(f"\n--- 最终报告 ---\n{step3_result}")

    return step3_result


# ============================================================
# 模式二：Supervisor（监督者模式）
# ============================================================

def supervisor_mode(query: str) -> str:
    """
    Supervisor 模式：一个 Agent 负责任务分发

    Supervisor 接收用户请求 → 判断需要哪些 Agent → 分发任务 → 汇总结果

    本质：Supervisor 就是一个会调用其他 Agent 的 Agent
    """
    print("\n" + "=" * 60)
    print("Supervisor 模式")
    print("=" * 60)

    # Worker Agents
    code_agent = SimpleAgent(
        name="代码专家",
        system_prompt="你是代码专家。回答关于编程、代码相关的问题。用中文。控制在 150 字以内。"
    )

    architecture_agent = SimpleAgent(
        name="架构专家",
        system_prompt="你是系统架构专家。回答关于系统设计、架构相关的问题。用中文。控制在 150 字以内。"
    )

    security_agent = SimpleAgent(
        name="安全专家",
        system_prompt="你是安全专家。回答关于安全、隐私相关的问题。用中文。控制在 150 字以内。"
    )

    # Worker 注册表
    workers = {
        "code": code_agent,
        "architecture": architecture_agent,
        "security": security_agent,
    }

    # Supervisor Agent
    supervisor = SimpleAgent(
        name="Supervisor",
        system_prompt=f"""你是任务分发者。根据用户的问题，决定需要咨询哪些专家。

可用专家: {list(workers.keys())}
- code: 代码和编程问题
- architecture: 系统设计和架构问题
- security: 安全和隐私问题

请返回 JSON 格式：
{{"tasks": {{"专家名": "需要问的问题"}}}}

例如：
{{"tasks": {{"code": "这段代码有什么问题？", "security": "有什么安全风险？"}}}}"""
    )

    # 1. Supervisor 分析任务
    print(f"\n用户输入: {query}")
    supervisor_response = supervisor.run(query)
    print(f"\n[Supervisor] 任务分配: {supervisor_response}")

    # 2. 解析 Supervisor 的分配
    try:
        # 提取 JSON
        json_str = supervisor_response
        if "```" in json_str:
            json_str = json_str.split("```")[1]
            if json_str.startswith("json"):
                json_str = json_str[4:]
        tasks = json.loads(json_str)["tasks"]
    except (json.JSONDecodeError, KeyError):
        print("[Supervisor] 解析失败，默认使用代码专家")
        tasks = {"code": query}

    # 3. 分发给各 Worker
    worker_results = {}
    for worker_name, task in tasks.items():
        if worker_name in workers:
            print(f"\n  → 分发给 {worker_name}: {task[:50]}...")
            result = workers[worker_name].run(task)
            worker_results[worker_name] = result
        else:
            print(f"  → 未知专家: {worker_name}")

    # 4. Supervisor 汇总
    summary_input = f"原始问题: {query}\n\n各专家回答:\n"
    for name, result in worker_results.items():
        summary_input += f"\n[{name}]: {result}\n"
    summary_input += "\n请汇总以上专家意见，给出综合回答。用中文。"

    final_result = supervisor.run(summary_input)
    print(f"\n--- 最终回答 ---\n{final_result}")

    return final_result


# ============================================================
# 运行
# ============================================================

if __name__ == "__main__":
    # Pipeline 模式
    pipeline_mode(
        "LangGraph 和 OpenAI Agents SDK 的优缺点对比"
    )

    # Supervisor 模式
    supervisor_mode(
        "我想开发一个 Web 应用，需要考虑代码架构和安全问题。应该怎么开始？"
    )

    # ============================================================
    # 核心感悟：
    #
    # Multi-Agent 的本质非常简单：
    #   Pipeline = 前一个 Agent 的输出作为后一个的输入
    #   Supervisor = 一个 Agent 调度其他 Agent
    #
    # CrewAI、AutoGen 等框架做的事情就是：
    #   1. 标准化了 Agent 的定义方式
    #   2. 自动化了任务分发和结果汇总
    #   3. 添加了日志、追踪等工程化能力
    #
    # 但底层机制就是：LLM 调用 + 字符串传递
    # ============================================================
