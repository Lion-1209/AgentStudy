# AgentStudy

AI Agent 开发学习计划与实战代码，从零基础到独立构建 Agent 应用。

## 学习路线

```
阶段1: 理解本质 ──── smolagents + 纯 Python 实现 ReAct 循环（1-2 周）
  ↓
阶段2: 市场主流 ──── LangChain + LangGraph（3-4 周）
  ↓
阶段3: 未来方向 ──── OpenAI Agents SDK + Claude Agent SDK（2-3 周）
  ↓
阶段4: 进阶实战 ──── Multi-Agent + 综合项目（3-4 周）
```

## 项目结构

```
AgentStudy/
├── LEARNING_PLAN.md                  完整学习计划（总纲）
├── stage1-fundamentals/              阶段1：纯 Python 实现 Agent 核心
│   ├── task1.1_minimal_react.py          ReAct 循环从零实现
│   ├── task1.2_tool_use.py               Function Calling 实现
│   └── task1.3_memory.py                 短期 + 长期记忆
├── stage2-langchain/                 阶段2：LangChain + LangGraph
│   ├── task2.1_langchain_agent.py        LangChain 基础 Agent
│   ├── task2.2_multi_tool_agent.py       多工具 Agent + 错误处理
│   ├── task2.3_langgraph_basics.py       LangGraph 状态图基础
│   └── task2.4_code_review_agent.py      代码审查流水线（实战）
├── stage3-vendor-sdk/                阶段3：Vendor SDK
│   ├── task3.1_openai_agents_sdk.py      OpenAI Agents SDK
│   └── task3.2_claude_agent_sdk.py       Claude Agent SDK
└── stage4-advanced/                  阶段4：进阶实战
    ├── task4.1_crewai_multiagent.py       CrewAI 多 Agent 协作
    ├── task4.2_multiagent_from_scratch.py 从零实现 Multi-Agent
    └── task4.3_code_analyzer/             综合项目（待完成）
```

## 快速开始

1. 克隆仓库
```bash
git clone https://github.com/Lion-1209/AgentStudy.git
cd AgentStudy
```

2. 创建虚拟环境
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. 安装依赖（按阶段安装）
```bash
# 阶段1
pip install openai python-dotenv

# 阶段2
pip install langchain langchain-openai langgraph

# 阶段3
pip install openai-agents anthropic

# 阶段4
pip install crewai crewai-tools
```

4. 配置 API Key
```bash
cp .env.example .env
# 编辑 .env 填入你的 API Key
```

5. 从阶段1开始学习
```bash
python stage1-fundamentals/task1.1_minimal_react.py
```

## 框架对比

| 框架 | 设计哲学 | 适合场景 | 学习阶段 |
|------|----------|----------|----------|
| 纯 Python | 理解本质 | 学习 Agent 内部机制 | 阶段1 |
| LangChain | 万能工具箱 | 通用 LLM 应用 | 阶段2 |
| LangGraph | 状态图编排 | 复杂业务流程 | 阶段2 |
| OpenAI Agents SDK | 轻量原生 | 新项目首选 | 阶段3 |
| Claude Agent SDK | Claude 生态 | Claude 模型项目 | 阶段3 |
| CrewAI | 角色扮演团队 | 多角色协作 | 阶段4 |

## 推荐资源

- [Anthropic: Building Effective Agents](https://www.anthropic.com/research/building-effective-agents)
- [OpenAI: Practical Guide to Building Agents](https://cdn.openai.com/business-guides-and-resources/a-practical-guide-to-building-agents.pdf)
- [Hugging Face Agents Course](https://huggingface.co/learn/agents-course/en/unit1/tutorial)
- [500+ AI Agent Projects](https://github.com/ashishpatel26/500-AI-Agents-Projects)
