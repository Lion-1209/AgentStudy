"""
Task 4.3: 综合项目 — AI 代码分析助手 (项目骨架)
================================================
目标：整合所学，构建一个完整的代码分析项目

架构：
  用户输入仓库路径
      ↓
  [结构分析] → 目录树、文件类型统计、依赖关系
      ↓
  [代码质量] → 行数统计、复杂度、重复代码检测
      ↓
  [安全扫描] → 敏感信息、常见漏洞模式
      ↓
  [报告生成] → 汇总为 Markdown 报告

你可以选择用以下任一框架实现：
  - LangGraph（推荐，适合流水线）
  - OpenAI Agents SDK
  - CrewAI

这是一个项目骨架，需要你填充完整实现。
"""

import os
import json
from typing import TypedDict


# ============================================================
# 第一步：定义你的项目状态（如果是 LangGraph）
# ============================================================

class CodeAnalysisState(TypedDict):
    """代码分析状态"""
    repo_path: str                # 仓库路径
    file_tree: dict               # 目录结构
    file_types: dict              # 文件类型统计
    total_lines: int              # 总行数
    total_files: int              # 总文件数
    quality_issues: list[str]     # 代码质量问题
    security_issues: list[str]    # 安全问题
    dependencies: list[str]       # 依赖项
    report: str                   # 最终报告


# ============================================================
# 第二步：实现工具函数
# ============================================================

def scan_directory(path: str) -> dict:
    """扫描目录结构"""
    # TODO: 实现目录扫描
    # 提示：用 os.walk 遍历，按文件类型分类统计
    pass


def count_code_lines(path: str) -> dict:
    """统计代码行数"""
    # TODO: 实现行数统计
    # 提示：遍历代码文件，按类型统计行数、空行、注释行
    pass


def detect_secrets(path: str) -> list[str]:
    """检测敏感信息"""
    # TODO: 实现敏感信息检测
    # 提示：检查硬编码的 API key、密码、token 等
    # 关键词：password, secret, api_key, token, credential
    pass


def check_code_quality(path: str) -> list[str]:
    """检查代码质量"""
    # TODO: 实现代码质量检查
    # 提示：检查过长函数、重复代码、复杂度等
    pass


def parse_dependencies(path: str) -> list[str]:
    """解析依赖项"""
    # TODO: 实现依赖解析
    # 提示：检查 requirements.txt, package.json, Cargo.toml 等
    pass


# ============================================================
# 第三步：选择框架，构建工作流
# ============================================================

def build_with_langgraph():
    """
    用 LangGraph 实现（推荐）

    提示：
    1. 创建 StateGraph(CodeAnalysisState)
    2. 为每个分析步骤创建节点函数
    3. 添加边：scan → quality → security → report
    4. 可以添加条件路由：如果发现严重安全问题，标记为高危
    """
    # from langgraph.graph import StateGraph, START, END
    pass


def build_with_openai_sdk():
    """
    用 OpenAI Agents SDK 实现

    提示：
    1. 为每个分析步骤创建 Agent
    2. 用 Handoff 串联
    3. 或者用一个 Agent + 多个工具
    """
    # from agents import Agent, Runner, function_tool
    pass


def build_with_crewai():
    """
    用 CrewAI 实现

    提示：
    1. 定义 Agent：结构分析师、质量审查员、安全审计员、报告撰写员
    2. 定义 Task：每个 Agent 一个 Task
    3. context 参数串联
    """
    # from crewai import Agent, Task, Crew, Process
    pass


# ============================================================
# 第四步：生成报告
# ============================================================

def generate_report(state: CodeAnalysisState) -> str:
    """生成 Markdown 格式的分析报告"""
    report = f"""# 代码分析报告

## 基本信息
- 仓库路径: {state['repo_path']}
- 文件总数: {state['total_files']}
- 代码总行数: {state['total_lines']}
- 文件类型分布: {json.dumps(state.get('file_types', {}), ensure_ascii=False)}

## 依赖项
{chr(10).join(f'- {dep}' for dep in state.get('dependencies', []))}

## 代码质量
{chr(10).join(f'- {issue}' for issue in state.get('quality_issues', [])) or '无问题'}

## 安全扫描
{chr(10).join(f'- {issue}' for issue in state.get('security_issues', [])) or '无问题'}
"""
    return report


# ============================================================
# 运行入口
# ============================================================

if __name__ == "__main__":
    # 选择你喜欢的框架，填充实现，然后运行
    print("Task 4.3: 综合项目")
    print("请选择一个框架实现，填充 TODO 部分")
    print("建议从 LangGraph 开始，它最适合这种流水线场景")
