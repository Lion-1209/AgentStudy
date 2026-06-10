"""
Task 2.4: LangGraph 实战 — 代码审查 Agent
==========================================
目标：用 LangGraph 构建一个多步骤代码审查流水线
      包含：多节点、条件路由、循环重试、人工确认

工作流：
  输入代码 → Lint 检查 → 安全扫描 → 风格检查 → 人工确认 → 生成报告
                 ↓            ↓            ↓
             (不通过则修复代码，重新检查，最多重试 3 次)

安装依赖：
  pip install langgraph langchain-openai python-dotenv
"""

import os
from typing import TypedDict
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END

load_dotenv()

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)


# ============================================================
# 状态定义
# ============================================================

class CodeReviewState(TypedDict):
    code: str                   # 待审查的代码
    language: str               # 编程语言
    lint_passed: bool           # Lint 是否通过
    lint_issues: list[str]      # Lint 发现的问题
    security_passed: bool       # 安全检查是否通过
    security_issues: list[str]  # 安全问题
    style_passed: bool          # 风格检查是否通过
    style_issues: list[str]     # 风格问题
    fixed_code: str             # 修复后的代码
    retry_count: int            # 重试次数
    approved: bool              # 人工是否批准
    report: str                 # 最终报告


# ============================================================
# 节点定义
# ============================================================

def lint_check(state: CodeReviewState) -> dict:
    """节点1：Lint 检查 — 检查语法和基本代码质量"""
    print(f"  [Lint] 检查代码 (重试: {state.get('retry_count', 0)})")

    code = state.get("fixed_code") or state["code"]

    prompt = f"""你是代码质量检查专家。请检查以下 {state['language']} 代码的语法和基本质量问题。

代码:
```
{code}
```

检查以下方面：
1. 语法错误
2. 未使用的变量/导入
3. 潜在的运行时错误
4. 异常处理是否完善

请严格按以下格式回答：
通过: <是/否>
问题: <问题描述，每行一个。如果没有问题，写"无">"""

    response = llm.invoke(prompt)
    content = response.content

    passed = "通过: 是" in content or "通过：是" in content
    issues = [
        line.strip().lstrip("- ").lstrip("0123456789. ")
        for line in content.split("\n")
        if line.strip() and "问题:" not in line and "通过:" not in line
        and line.strip() not in ("无", "")
    ]

    return {
        "lint_passed": passed,
        "lint_issues": issues if not passed else [],
        "fixed_code": code,
        "retry_count": state.get("retry_count", 0),
    }


def security_check(state: CodeReviewState) -> dict:
    """节点2：安全扫描 — 检查常见安全漏洞"""
    print(f"  [安全] 扫描安全漏洞")

    code = state.get("fixed_code") or state["code"]

    prompt = f"""你是安全审计专家。请检查以下代码的安全问题。

代码:
```
{code}
```

检查：
1. SQL 注入风险
2. XSS 风险
3. 硬编码的密钥/密码
4. 不安全的文件操作
5. 命令注入

请严格按以下格式回答：
通过: <是/否>
问题: <问题描述，每行一个>"""

    response = llm.invoke(prompt)
    content = response.content

    passed = "通过: 是" in content or "通过：是" in content
    issues = [
        line.strip().lstrip("- ").lstrip("0123456789. ")
        for line in content.split("\n")
        if line.strip() and "问题:" not in line and "通过:" not in line
        and line.strip() not in ("无", "")
    ]

    return {
        "security_passed": passed,
        "security_issues": issues if not passed else [],
    }


def style_check(state: CodeReviewState) -> dict:
    """节点3：风格检查 — 检查代码风格和可读性"""
    print(f"  [风格] 检查代码风格")

    code = state.get("fixed_code") or state["code"]

    prompt = f"""你是代码风格审查专家。请检查以下 {state['language']} 代码的风格。

代码:
```
{code}
```

检查：
1. 命名规范（变量、函数、类名）
2. 注释是否充分
3. 函数长度是否合理
4. 代码格式（缩进、空行）

请严格按以下格式回答：
通过: <是/否>
问题: <问题描述，每行一个>"""

    response = llm.invoke(prompt)
    content = response.content

    passed = "通过: 是" in content or "通过：是" in content
    issues = [
        line.strip().lstrip("- ").lstrip("0123456789. ")
        for line in content.split("\n")
        if line.strip() and "问题:" not in line and "通过:" not in line
        and line.strip() not in ("无", "")
    ]

    return {
        "style_passed": passed,
        "style_issues": issues if not passed else [],
    }


def auto_fix(state: CodeReviewState) -> dict:
    """节点4：自动修复 — 根据所有问题尝试修复代码"""
    print(f"  [修复] 自动修复代码")

    all_issues = []
    if not state.get("lint_passed"):
        all_issues.extend([f"[Lint] {i}" for i in state.get("lint_issues", [])])
    if not state.get("security_passed"):
        all_issues.extend([f"[安全] {i}" for i in state.get("security_issues", [])])
    if not state.get("style_passed"):
        all_issues.extend([f"[风格] {i}" for i in state.get("style_issues", [])])

    code = state.get("fixed_code") or state["code"]

    prompt = f"""请修复以下代码中的问题，只输出修复后的完整代码，不要解释。

原始代码:
```
{code}
```

需要修复的问题:
{chr(10).join(f'- {issue}' for issue in all_issues)}

修复后的代码:"""

    response = llm.invoke(prompt)
    fixed = response.content
    # 提取代码块
    if "```" in fixed:
        fixed = fixed.split("```")[1]
        if fixed.split("\n")[0].strip() in ("python", "javascript", "java", "cpp"):
            fixed = "\n".join(fixed.split("\n")[1:])

    return {
        "fixed_code": fixed.strip(),
        "retry_count": state.get("retry_count", 0) + 1,
    }


def generate_report(state: CodeReviewState) -> dict:
    """节点5：生成报告"""
    print(f"  [报告] 生成审查报告")

    all_passed = all([
        state.get("lint_passed", True),
        state.get("security_passed", True),
        state.get("style_passed", True),
    ])

    report_parts = ["## 代码审查报告\n"]

    if state.get("lint_issues"):
        report_parts.append("### Lint 问题\n" + "\n".join(f"- {i}" for i in state["lint_issues"]))
    else:
        report_parts.append("### Lint: 通过")

    if state.get("security_issues"):
        report_parts.append("### 安全问题\n" + "\n".join(f"- {i}" for i in state["security_issues"]))
    else:
        report_parts.append("### 安全: 通过")

    if state.get("style_issues"):
        report_parts.append("### 风格问题\n" + "\n".join(f"- {i}" for i in state["style_issues"]))
    else:
        report_parts.append("### 风格: 通过")

    report_parts.append(f"\n### 总计重试: {state.get('retry_count', 0)} 次")
    report_parts.append(f"### 最终状态: {'全部通过' if all_passed else '仍有问题'}")

    if state.get("fixed_code"):
        report_parts.append(f"\n### 修复后的代码\n```{state.get('language', '')}\n{state['fixed_code']}\n```")

    return {"report": "\n\n".join(report_parts)}


# ============================================================
# 路由函数
# ============================================================

MAX_RETRIES = 3

def route_after_checks(state: CodeReviewState) -> str:
    """所有检查完成后，决定是修复还是生成报告"""
    all_passed = all([
        state.get("lint_passed", True),
        state.get("security_passed", True),
        state.get("style_passed", True),
    ])

    if all_passed:
        return "report"

    if state.get("retry_count", 0) >= MAX_RETRIES:
        print(f"  [路由] 达到最大重试次数 ({MAX_RETRIES})，直接生成报告")
        return "report"

    return "fix"


# ============================================================
# 构建图
# ============================================================

def build_code_review_workflow() -> StateGraph:
    workflow = StateGraph(CodeReviewState)

    # 添加节点
    workflow.add_node("lint", lint_check)
    workflow.add_node("security", security_check)
    workflow.add_node("style", style_check)
    workflow.add_node("fix", auto_fix)
    workflow.add_node("report", generate_report)

    # 定义边
    workflow.add_edge(START, "lint")
    workflow.add_edge("lint", "security")
    workflow.add_edge("security", "style")

    # 风格检查后：条件路由 → 修复 or 报告
    workflow.add_conditional_edges(
        "style",
        route_after_checks,
        {"fix": "fix", "report": "report"}
    )

    # 修复后重新检查
    workflow.add_edge("fix", "lint")

    # 报告后结束
    workflow.add_edge("report", END)

    return workflow


# ============================================================
# 运行
# ============================================================

if __name__ == "__main__":
    app = build_code_review_workflow().compile()

    # 打印工作流结构
    print("代码审查工作流:")
    print(app.get_graph().print_ascii())

    # 测试用例：一段有问题的 Python 代码
    test_code = """
import os
import sys
import json

def process_data(data, password="admin123"):
    # hardcoded password above
    query = f"SELECT * FROM users WHERE name = '{data['name']}'"
    result = eval(data.get("expression", ""))
    x=1
    y=2
    if x==y:print("equal")
    return result

def very_long_function_that_does_everything(a, b, c, d, e, f, g):
    # this function is too long and does too many things
    total = a + b + c + d + e + f + g
    average = total / 7
    maximum = max(a, b, c, d, e, f, g)
    minimum = min(a, b, c, d, e, f, g)
    sorted_vals = sorted([a, b, c, d, e, f, g])
    median = sorted_vals[3]
    return total, average, maximum, minimum, median
"""

    print("\n" + "=" * 60)
    print("开始代码审查")
    print("=" * 60)

    result = app.invoke({
        "code": test_code,
        "language": "python",
        "lint_passed": False,
        "lint_issues": [],
        "security_passed": False,
        "security_issues": [],
        "style_passed": False,
        "style_issues": [],
        "fixed_code": "",
        "retry_count": 0,
        "approved": False,
        "report": "",
    })

    print("\n" + "=" * 60)
    print(result["report"])
