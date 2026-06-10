# AI Agent 开发学习计划

> 目标：从零掌握 Agent 开发，4 个阶段，约 10-14 周
> 前置条件：Python 基础、理解 LLM vs Agent 区别

---

## 阶段总览

```
阶段1: 理解本质 ──────── smolagents + 从零实现 ReAct 循环（1-2 周）
  ↓
阶段2: 市场主流 ──────── LangChain + LangGraph（3-4 周）
  ↓
阶段3: 未来方向 ──────── OpenAI Agents SDK + Claude Agent SDK（2-3 周）
  ↓
阶段4: 进阶实战 ──────── Multi-Agent + 完整项目（3-4 周）
```

---

## 阶段 1：理解 Agent 本质（1-2 周）

> 目标：不依赖任何框架，手动实现 Agent 核心循环，真正理解 Agent 是什么

### 理论阅读（并行）
- [ ] [Anthropic: Building Effective Agents](https://www.anthropic.com/research/building-effective-agents)
- [ ] [OpenAI: A Practical Guide to Building Agents (PDF)](https://cdn.openai.com/business-guides-and-resources/a-practical-guide-to-building-agents.pdf)

---

### Task 1.1：用纯 Python 实现最小 ReAct 循环

**目标：** 用一个 while 循环 + LLM API 调用，实现 Agent 最核心的 Think→Act→Observe 循环。

**代码参考 →** `stage1-fundamentals/task1.1_minimal_react.py`

**关键知识点：**
- ReAct 循环的本质就是：LLM 生成文本 → 解析出动作 → 执行动作 → 把结果喂回 LLM → 重复
- 不需要任何框架，核心逻辑不到 50 行
- 理解 Agent = LLM + Tool Use + Loop

---

### Task 1.2：实现 Tool Use 机制

**目标：** 在 Task 1.1 基础上，给 Agent 添加工具调用能力。自己实现一个简易的 function calling。

**代码参考 →** `stage1-fundamentals/task1.2_tool_use.py`

**关键知识点：**
- Tool 的本质：一个函数 + 描述信息（名字、参数、用途说明）
- LLM 输出结构化的工具调用请求 → 解析 → 执行 → 返回结果
- 工具描述（description）的质量直接决定 Agent 能否正确选择工具

---

### Task 1.3：给 Agent 加上记忆

**目标：** 在 Task 1.2 基础上，实现短期记忆（对话历史截断）和长期记忆（简单文件存储）。

**代码参考 →** `stage1-fundamentals/task1.3_memory.py`

**关键知识点：**
- 短期记忆：维护 message 列表，超出 token 限制时需要截断/摘要
- 长期记忆：把重要信息持久化到文件/数据库，下次对话可检索
- Token 管理是 Agent 开发中非常实际的问题

---

### Task 1.4：读 smolagents 源码

**目标：** 阅读 smolagents 核心代码，对比你 Task 1.1-1.3 的实现，理解工业级实现和你写的最小版本有什么区别。

**阅读路线：**
1. 安装：`pip install smolagents`
2. 克隆源码：`git clone https://github.com/huggingface/smolagents`
3. 阅读顺序：
   - `smolagents/agents.py` → 找到 `CodeAgent` 和 `ToolCallingAgent` 的 `run()` 方法，看它怎么实现循环
   - `smolagents/tools.py` → 看 `Tool` 基类，理解工具是怎么注册和调用的
   - `smolagents/memory.py` → 看记忆是怎么管理的
   - `smolagents/models.py` → 看 LLM 调用是怎么封装的

**输出：** 写一份笔记，记录你的实现和 smolagents 的 3 个核心区别

---

## 阶段 2：LangChain + LangGraph（3-4 周）

> 目标：掌握当前招聘市场需求最大的框架，能独立构建生产级 Agent 应用

### 理论阅读（并行）
- [ ] [LangChain 官方教程](https://python.langchain.com/docs/tutorials/)
- [ ] [LangGraph 官方教程](https://langchain-ai.github.io/langgraph/tutorials/)

---

### Task 2.1：LangChain 基础 — 单 Agent + 工具

**目标：** 用 LangChain 重新实现 Task 1.2 的功能，体验框架带来的标准化和便利性。

**代码参考 →** `stage2-langchain/task2.1_langchain_agent.py`

**关键知识点：**
- `@tool` 装饰器 vs 手写工具描述 — 框架自动生成 schema
- `AgentExecutor` — 封装了 ReAct 循环，不需要自己写 while
- `ChatPromptTemplate` — 提示词模板化管理
- 对比纯 Python 实现：代码量减少了什么？多了什么抽象？

---

### Task 2.2：LangChain 多工具 Agent

**目标：** 构建一个有 4-5 种工具的实用 Agent，学习工具设计、错误处理、输出解析。

**代码参考 →** `stage2-langchain/task2.2_multi_tool_agent.py`

**关键知识点：**
- 工具设计原则：单一职责、清晰的描述、合理的参数
- `handle_tool_errors=True` — 工具执行失败时不要让整个 Agent 崩溃
- 输出解析器（Output Parser）— 从 LLM 的自由文本输出中提取结构化数据
- 调试技巧：设置 `LANGCHAIN_TRACING_V2=true` 接入 LangSmith 追踪

---

### Task 2.3：LangGraph 状态图基础

**目标：** 用 LangGraph 实现一个有条件分支的工作流，理解状态图编排模式。

**代码参考 →** `stage2-langchain/task2.3_langgraph_basics.py`

**关键知识点：**
- `StateGraph` — 用图（节点+边）定义工作流，取代手写 if-else
- `add_node` / `add_edge` / `add_conditional_edges` — 节点、确定性边、条件边
- State 的传递 — 每个节点返回状态更新，下一个节点读更新后的状态
- `compile()` — 编译图，可以做可视化

---

### Task 2.4：LangGraph 实战 — 代码审查 Agent

**目标：** 用 LangGraph 构建一个完整的代码审查流水线，包含多步骤、循环、人工介入。

**代码参考 →** `stage2-langchain/task2.4_code_review_agent.py`

**关键知识点：**
- 多节点协作：lint 检查 → 安全扫描 → 风格检查 → 生成报告
- 条件路由：lint 通过则跳过修复节点，不通过则进入修复
- 循环：修复后重新检查，最多重试 N 次
- `interrupt_before` — 在关键节点暂停，等待人工确认
- 这就是 LangGraph 的核心价值：复杂流程的可视化和可控性

---

## 阶段 3：Vendor SDK（2-3 周）

> 目标：掌握 OpenAI Agents SDK 和 Claude Agent SDK，理解"去框架化"趋势

---

### Task 3.1：OpenAI Agents SDK 基础

**目标：** 用 OpenAI Agents SDK 实现和 Task 2.2 同等功能的多工具 Agent。

**代码参考 →** `stage3-vendor-sdk/task3.1_openai_agents_sdk.py`

**关键知识点：**
- `Agent` 类 — 定义 Agent 的指令、工具、模型
- `Runner.run()` — 执行 Agent，内置循环
- Agent Handoff — Agent 之间可以交接任务（类似电话转接）
- Guardrails — 输入/输出的安全检查机制
- 对比 LangChain：代码更少，抽象更少，更直觉

---

### Task 3.2：Claude Agent SDK 基础

**目标：** 用 Claude Agent SDK 构建 Agent，体验与 Claude Code 同源的运行时。

**代码参考 →** `stage3-vendor-sdk/task3.2_claude_agent_sdk.py`

**关键知识点：**
- 内置 8 个工具：Read, Edit, Bash, Grep, Glob, WebSearch, WebFetch, Write
- MCP（Model Context Protocol）集成 — 标准化的工具协议
- 和 Claude Code 使用完全相同的运行时
- 自定义工具的添加方式

---

### Task 3.3：框架对比总结

**目标：** 用同一个任务（代码分析 Agent）分别在 3 个框架中实现，写一份对比报告。

**输出：** 创建 `stage3-vendor-sdk/comparison_report.md`，包含：

| 维度 | 纯 Python (Task 1.2) | LangChain (Task 2.2) | OpenAI SDK (Task 3.1) | Claude SDK (Task 3.2) |
|------|---------------------|---------------------|----------------------|----------------------|
| 代码行数 | ? | ? | ? | ? |
| 上手难度 | ? | ? | ? | ? |
| 灵活性 | ? | ? | ? | ? |
| 生产就绪度 | ? | ? | ? | ? |
| 适合场景 | ? | ? | ? | ? |

---

## 阶段 4：进阶实战（3-4 周）

> 目标：掌握 Multi-Agent 协作，完成一个完整的项目

---

### Task 4.1：CrewAI 多 Agent 协作

**目标：** 用 CrewAI 实现 3 个 Agent 协作完成一个技术调研报告。

**代码参考 →** `stage4-advanced/task4.1_crewai_multiagent.py`

**关键知识点：**
- Agent 角色（Role）、目标（Goal）、背景（Backstory）
- Task 定义和依赖关系
- Process 模式：sequential（顺序）vs hierarchical（层级）
- Crew — Agent 和 Task 的容器

---

### Task 4.2：从零实现 Multi-Agent（不用框架）

**目标：** 不用任何框架，自己实现 2 个 Agent 之间的协作，理解多 Agent 的本质。

**代码参考 →** `stage4-advanced/task4.2_multiagent_from_scratch.py`

**关键知识点：**
- Agent 间通信的本质：就是把一个 Agent 的输出当作另一个的输入
- Supervisor 模式：一个 Agent 负责分发任务，其他 Agent 执行
- Pipeline 模式：Agent 按顺序依次处理
- 去掉框架后，你会发现 Multi-Agent 其实没那么神秘

---

### Task 4.3：综合项目 — AI 代码分析助手

**目标：** 整合所学，构建一个完整的 AI 代码分析项目。输入一个 GitHub 仓库 URL，自动分析代码结构、质量、安全风险，生成报告。

**代码参考 →** `stage4-advanced/task4.3_code_analyzer/`

**架构设计：**
```
用户输入仓库 URL
    ↓
[克隆仓库] Agent
    ↓
[结构分析] Agent  →  分析目录结构、文件类型、依赖关系
    ↓
[代码质量] Agent  →  检查代码规范、复杂度、重复代码
    ↓
[安全扫描] Agent  →  检查常见漏洞、敏感信息泄露
    ↓
[报告生成] Agent  →  汇总分析结果，生成 Markdown 报告
    ↓
输出报告
```

**你可以选择用以下任一框架实现：**
- LangGraph（推荐，适合这种有明确步骤的流水线）
- OpenAI Agents SDK
- CrewAI

---

## 推荐资源汇总

### 必读
| 资源 | 链接 |
|------|------|
| Anthropic: Building Effective Agents | https://www.anthropic.com/research/building-effective-agents |
| OpenAI: Practical Guide to Building Agents | https://cdn.openai.com/business-guides-and-resources/a-practical-guide-to-building-agents.pdf |
| Hugging Face Agents Course | https://huggingface.co/learn/agents-course/en/unit1/tutorial |

### 框架文档
| 框架 | 文档 |
|------|------|
| LangChain | https://python.langchain.com/docs/ |
| LangGraph | https://langchain-ai.github.io/langgraph/ |
| OpenAI Agents SDK | https://openai.github.io/openai-agents-python/agents/ |
| Claude Agent SDK | https://github.com/anthropics/claude-agent-sdk-python |
| CrewAI | https://docs.crewai.com/ |
| smolagents | https://github.com/huggingface/smolagents |

### 实战参考项目
| 项目 | 链接 | 学习价值 |
|------|------|---------|
| DeerFlow (ByteDance) | https://github.com/bytedance/deer-flow | SuperAgent 架构、MCP、沙箱 |
| OpenHands | https://github.com/All-Hands-AI/OpenHands | 自主编码 Agent |
| SWE-agent (Princeton) | https://github.com/princeton-nlp/SWE-agent | 自动修复 GitHub Issue |

---

## 通用注意事项

1. **每个 Task 都要完整实现并运行**，不要只看不写
2. **API Key 管理**：用 `.env` 文件 + `python-dotenv`，不要硬编码
3. **做好版本控制**：每完成一个 Task 就 commit
4. **记录踩坑笔记**：Agent 开发的调试经验和普通软件开发差别很大
5. **不要追求一次写对**：Agent 的行为有不确定性，调 prompt 是常态
6. **关注成本**：开发阶段用便宜的模型（gpt-4o-mini / claude-3.5-haiku），避免烧钱
