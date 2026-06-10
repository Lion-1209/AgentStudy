# LangChain / LangGraph 常用 API 完整中文参考

> 完整文档: https://python.langchain.com/docs/
> LangGraph 文档: https://langchain-ai.github.io/langgraph/

---

## 目录

1. [ChatOpenAI — LLM 客户端](#1-chatopenai--llm-客户端)
2. [消息类型 (Message)](#2-消息类型-message)
3. [Output Parser — 输出解析器](#3-output-parser--输出解析器)
4. [ChatPromptTemplate — 提示词模板](#4-chatprompttemplate--提示词模板)
5. [@tool — 工具定义](#5-tool--工具定义)
6. [Agent + AgentExecutor](#6-agent--agentexecutor)
7. [LangGraph StateGraph 状态图](#7-langgraph-stategraph-状态图)
8. [LangGraph 高级功能](#8-langgraph-高级功能)
9. [LCEL (LangChain Expression Language)](#9-lcel-langchain-expression-language)
10. [速查对比表](#10-速查对比表)

---

## 1. ChatOpenAI — LLM 客户端

### 初始化

```python
from langchain_openai import ChatOpenAI

# 基本用法
llm = ChatOpenAI(
    model="glm-4-flash",
    base_url="https://open.bigmodel.cn/api/paas/v4",
    api_key="your-key",          # 也可从 OPENAI_API_KEY 环境变量读取
    temperature=0,
)

# 用我们项目的 llm_config
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from llm_config import get_provider, PROVIDERS
_, provider_config = get_provider()
llm = ChatOpenAI(
    model=provider_config["model"],
    base_url=provider_config["base_url"],
    api_key=os.getenv(provider_config["api_key_env"]),
    temperature=0,
)
```

### 调用方式

```python
# 方式一：直接传字符串
response = llm.invoke("你好")
print(response.content)  # "你好！有什么可以帮你的吗？"

# 方式二：传消息列表
from langchain_core.messages import HumanMessage, SystemMessage
response = llm.invoke([
    SystemMessage(content="你是 Python 专家"),
    HumanMessage(content="什么是装饰器"),
])

# 方式三：批量调用
results = llm.batch(["1+1等于几", "2+2等于几"])
for r in results:
    print(r.content)

# 方式四：流式输出
for chunk in llm.stream("讲个故事"):
    print(chunk.content, end="", flush=True)

# 方式五：异步调用
import asyncio
response = await llm.ainvoke("你好")
```

### 绑定工具

```python
# 把工具绑定到 LLM（不创建 Agent，直接用 LLM 调用工具）
llm_with_tools = llm.bind_tools([get_weather, calculate])

response = llm_with_tools.invoke("北京天气怎么样")
# response.tool_calls 包含工具调用信息
for tc in response.tool_calls:
    print(f"工具: {tc['name']}, 参数: {tc['args']}")
```

### 常用参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `model` | str | "gpt-4o" | 模型名 |
| `temperature` | float | 0.7 | 0=确定性，2=创造性 |
| `max_tokens` | int | None | 最大输出 token |
| `model_kwargs` | dict | {} | 传给 API 的额外参数 |
| `streaming` | bool | False | 是否默认流式 |
| `verbose` | bool | False | 是否打印详细信息 |

---

## 2. 消息类型 (Message)

```python
from langchain_core.messages import (
    SystemMessage,    # 系统指令
    HumanMessage,     # 用户消息
    AIMessage,        # AI 回复
    ToolMessage,      # 工具返回结果
)
```

### 创建和使用

```python
# 创建消息
system = SystemMessage(content="你是助手")
human = HumanMessage(content="你好")

# AIMessage 包含额外信息
response = llm.invoke([system, human])
ai_msg = response

ai_msg.content           # 回复文本: "你好！"
ai_msg.response_metadata # 原始 API 响应元数据
ai_msg.id                # 消息唯一 ID
ai_msg.tool_calls        # 工具调用列表（如果有）

# ToolMessage — 工具执行结果
tool_msg = ToolMessage(
    content="北京: 晴 25°C",
    tool_call_id="call_abc123",  # 对应 AI 的 tool_call id
)
```

### 消息历史管理

```python
from langchain_core.messages import (
    trim_messages,
    HumanMessage, SystemMessage,
)

messages = [
    SystemMessage(content="你是助手"),
    HumanMessage(content="问题1"),
    # ... 很多轮对话
]

# 按 token 数截断，保留 system 消息
trimmed = trim_messages(
    messages,
    max_tokens=4000,           # 最大 token 数
    strategy="last",           # 保留最近的
    token_counter=len,         # token 计算函数（简化）
    include_system=True,       # 保留 system 消息
    allow_partial=False,       # 不截断单条消息
)
```

---

## 3. Output Parser — 输出解析器

### StrOutputParser — 最简单，提取纯文本

```python
from langchain_core.output_parsers import StrOutputParser

parser = StrOutputParser()
result = parser.parse(ai_message)  # 从 AIMessage 提取 content 字符串
```

### PydanticOutputParser — 结构化输出

```python
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

class MovieReview(BaseModel):
    title: str = Field(description="电影名")
    score: float = Field(description="评分 0-10")
    summary: str = Field(description="一句话评价")

parser = PydanticOutputParser(pydantic_object=MovieReview)

# 获取格式说明（注入到 prompt 中）
format_instructions = parser.get_format_instructions()
# "请按以下 JSON schema 格式输出：..."

# 解析 LLM 输出
result = parser.parse('{"title": "盗梦空间", "score": 9.0, "summary": "烧脑佳作"}')
print(result.title)    # "盗梦空间"
print(result.score)    # 9.0
```

### CommaSeparatedListOutputParser — 列表输出

```python
from langchain_core.output_parsers import CommaSeparatedListOutputParser

parser = CommaSeparatedListOutputParser()
result = parser.parse("苹果, 香蕉, 橘子")
# ["苹果", "香蕉", "橘子"]
```

---

## 4. ChatPromptTemplate — 提示词模板

### 基本用法

```python
from langchain_core.prompts import ChatPromptTemplate

# 从消息列表创建
prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个{role}，擅长{skill}"),
    ("human", "{input}"),
])

# 填充变量
messages = prompt.invoke({"role": "Python专家", "skill": "代码优化", "input": "帮我优化这段代码"})
# 返回 ChatPromptValue，可以直接传给 llm.invoke()
```

### 其他创建方式

```python
# 从字符串创建（自动包装为 human 消息）
prompt = ChatPromptTemplate.from_template("请用{language}语言写一个{thing}")

# 从消息元组创建
prompt = ChatPromptTemplate.from_messages([
    ("system", "你是助手"),
    MessagesPlaceholder("history"),   # 占位符，运行时填入消息列表
    ("human", "{input}"),
])

# 使用
messages = prompt.invoke({
    "history": [HumanMessage(content="之前的问题"), AIMessage(content="之前的回答")],
    "input": "新问题",
})
```

### MessagesPlaceholder — 动态消息历史

```python
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

prompt = ChatPromptTemplate.from_messages([
    ("system", "你是助手"),
    MessagesPlaceholder(variable_name="chat_history"),  # 对话历史
    ("human", "{input}"),
])

# chat_history 可以是空列表或之前的消息
result = prompt.invoke({
    "chat_history": [],
    "input": "你好",
})
```

---

## 5. @tool — 工具定义

### 基本用法

```python
from langchain.tools import tool

@tool
def get_weather(city: str) -> str:
    """获取城市天气信息"""
    return f"{city}: 晴 25°C"

# docstring → 工具的 description
# 参数类型注解 → 自动生成参数 schema
# 不需要手写 JSON Schema！
```

### 工具参数详细配置

```python
from langchain.tools import tool

@tool
def search_database(
    query: str,                         # 必填参数
    limit: int = 10,                    # 可选参数（带默认值）
    database: str = "main",             # 可选参数
) -> list[dict]:
    """在数据库中搜索记录

    Args:
        query: 搜索关键词
        limit: 返回结果数量上限，默认10
        database: 要搜索的数据库名，默认main
    """
    # 实际搜索逻辑
    return [{"id": 1, "name": "结果1"}]
```

### 用 Pydantic 精确控制参数

```python
from pydantic import BaseModel, Field
from langchain.tools import tool

class SearchInput(BaseModel):
    query: str = Field(description="搜索关键词")
    limit: int = Field(default=10, description="返回数量上限", ge=1, le=100)

@tool(args_schema=SearchInput)
def search(query: str, limit: int = 10) -> list:
    """搜索数据库"""
    return [{"query": query, "limit": limit}]
```

### 返回 Artifact（附带额外数据）

```python
@tool(response_format="content_and_artifact")
def generate_chart(data: str) -> tuple[str, bytes]:
    """生成图表"""
    chart_bytes = create_chart(data)  # 返回图片二进制
    return "图表已生成", chart_bytes

# 使用时
result = generate_chart.invoke({"data": "1,2,3"})
result.content    # "图表已生成"
result.artifact   # 图片二进制数据
```

### 手动创建工具（不用装饰器）

```python
from langchain_core.tools import StructuredTool

def my_func(x: int) -> int:
    return x * 2

my_tool = StructuredTool.from_function(
    func=my_func,
    name="double",
    description="将数字乘以2",
)
```

---

## 6. Agent + AgentExecutor

### 创建 Agent

```python
from langchain.agents import create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate

# 提示词模板（必须包含 agent_scratchpad）
prompt = ChatPromptTemplate.from_messages([
    ("system", "你是助手，可以用工具帮助用户。"),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}"),  # 必须！存放中间推理过程
])

# 创建 Agent
agent = create_tool_calling_agent(llm, tools, prompt)
```

**注意：** `{agent_scratchpad}` 是必须的。框架会把 Agent 每一步的 Think/Act/Observe 过程填在这里。没有它 Agent 无法工作。

### AgentExecutor 配置

```python
from langchain.agents import AgentExecutor

executor = AgentExecutor(
    agent=agent,
    tools=[get_weather, calculate],   # 工具列表

    # 核心参数
    max_iterations=5,                 # 最大循环次数（防止死循环）
    max_execution_time=30,            # 最大执行时间（秒）
    handle_parsing_errors=True,       # 解析错误时不崩溃，自动恢复
    verbose=True,                     # 打印中间过程（调试神器）

    # 返回控制
    return_intermediate_steps=True,   # 返回中间步骤（调试用）
    early_stopping_method="generate", # 超时时的处理方式

    # 内存（多轮对话）
    # memory=ConversationBufferMemory(memory_key="chat_history"),
)
```

### 执行和获取结果

```python
# 执行
result = executor.invoke({"input": "北京天气怎么样"})

# 结果结构
result["input"]                      # 用户输入
result["output"]                     # 最终回答

# 如果 return_intermediate_steps=True
for action, observation in result["intermediate_steps"]:
    action.tool           # 使用的工具名
    action.tool_input     # 工具输入参数
    action.log            # Agent 的思考过程（文本）
    observation           # 工具返回结果
```

### 其他 Agent 类型

```python
from langchain.agents import (
    create_tool_calling_agent,    # 推荐：用 Function Calling
    create_react_agent,           # ReAct 文本解析（不用 Function Calling）
    create_structured_chat_agent, # 结构化聊天 Agent
    create_json_chat_agent,       # JSON 格式输出
)

# create_react_agent — 适用于不支持 Function Calling 的模型
react_agent = create_react_agent(llm, tools, prompt)
# LLM 会输出 Thought/Action/Action Input 文本，框架解析
```

---

## 7. LangGraph StateGraph 状态图

### 7.1 定义状态 (State)

```python
from typing import TypedDict, Annotated, Sequence
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage

# 基本状态
class MyState(TypedDict):
    question: str
    answer: str
    retry_count: int

# 带消息历史的状态
class ChatState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]  # 自动追加
    current_step: str
```

**`Annotated[list, add_messages]` 的含义：**
- 普通字段：后一个节点返回的值覆盖前一个
- `Annotated[list, add_messages]`：多个节点的返回值自动追加合并，不覆盖

### 7.2 定义节点 (Node)

```python
# 节点是一个函数：(state) → dict（部分更新）
def research(state: MyState) -> dict:
    question = state["question"]
    # 做处理...
    return {"answer": "调研结果...", "current_step": "research"}

def analyze(state: MyState) -> dict:
    # 可以读取上一个节点更新的 state
    answer = state["answer"]
    return {"answer": f"分析: {answer}", "current_step": "analyze"}
```

### 7.3 定义边 (Edge)

```python
from langgraph.graph import StateGraph, START, END

workflow = StateGraph(MyState)

# 添加节点
workflow.add_node("research", research)
workflow.add_node("analyze", analyze)
workflow.add_node("report", generate_report)

# === 确定性边 ===
workflow.add_edge(START, "research")       # 起点 → research
workflow.add_edge("research", "analyze")   # research → analyze
workflow.add_edge("report", END)           # report → 终点

# === 条件边 ===
def should_continue(state: MyState) -> str:
    """路由函数：返回下一个节点名"""
    if state["retry_count"] < 3:
        return "research"    # 回到 research 重试
    return "report"          # 去生成报告

workflow.add_conditional_edges(
    "analyze",                                        # 从哪个节点出发
    should_continue,                                  # 路由函数
    {"research": "research", "report": "report"},     # 返回值 → 目标节点映射
)

# === 多条件路由 ===
def route_by_type(state: MyState) -> str:
    if state["question"].startswith("代码"):
        return "code_review"
    elif state["question"].startswith("安全"):
        return "security"
    else:
        return "general"

workflow.add_conditional_edges(
    START,
    route_by_type,
    {"code_review": "code_review", "security": "security", "general": "general"},
)
```

### 7.4 编译和执行

```python
# 编译（检查图的有效性）
app = workflow.compile()

# 同步执行
result = app.invoke({
    "question": "你好",
    "answer": "",
    "retry_count": 0,
})

# 流式执行（逐步输出每个节点的结果）
for event in app.stream({"question": "你好", "answer": "", "retry_count": 0}):
    print(event)  # 每个节点的输出
    # {"research": {"answer": "...", "current_step": "research"}}
    # {"analyze": {"answer": "...", "current_step": "analyze"}}

# 异步执行
result = await app.ainvoke({...})
async for event in app.astream({...}):
    print(event)

# 查看图结构
print(app.get_graph().print_ascii())
```

---

## 8. LangGraph 高级功能

### 8.1 人工介入 (Human-in-the-loop)

```python
# 编译时指定在哪个节点前暂停
app = workflow.compile(
    interrupt_before=["report"],   # 在 report 节点之前暂停
    # interrupt_after=["analyze"],  # 在 analyze 节点之后暂停
)

# 执行到暂停点
result = app.invoke(initial_state)
# 此时 result 包含暂停前的状态

# 人工检查后继续
# 可以修改 state 后继续执行
result = app.invoke(
    None,                         # None 表示继续上次的执行
    config={"configurable": {"thread_id": "1"}},
)
```

### 8.2 Checkpointer — 状态持久化

```python
from langgraph.checkpoint.memory import MemorySaver

# 内存存储（重启丢失）
memory = MemorySaver()
app = workflow.compile(checkpointer=memory)

# 每次 invoke 传 thread_id
config = {"configurable": {"thread_id": "user-123"}}
result = app.invoke({"question": "你好"}, config)

# 同一个 thread_id 可以恢复之前的对话
result = app.invoke({"question": "继续上次的话题"}, config)
```

### 8.3 子图 (Subgraph)

```python
# 一个图可以作为另一个图的节点
def call_subgraph(state: MyState) -> dict:
    result = sub_app.invoke(state)
    return result

workflow.add_node("substep", call_subgraph)
```

---

## 9. LCEL (LangChain Expression Language)

LCEL 是 LangChain 的管道操作符，用 `|` 连接组件。

### 基本链

```python
from langchain_core.output_parsers import StrOutputParser

# prompt → llm → parser，用管道符连接
chain = prompt | llm | StrOutputParser()

# 调用
result = chain.invoke({"role": "助手", "input": "你好"})
print(result)  # 纯文本
```

### 带工具的链

```python
# llm 绑定工具
llm_with_tools = llm.bind_tools([get_weather, calculate])

# 基本链
chain = prompt | llm_with_tools

result = chain.invoke({"input": "北京天气"})
# result.tool_calls 包含工具调用
```

### Runnable 接口

所有 LCEL 组件都支持：

| 方法 | 说明 |
|------|------|
| `.invoke()` | 同步单次调用 |
| `.batch()` | 批量调用 |
| `.stream()` | 流式输出 |
| `.ainvoke()` | 异步调用 |
| `.astream()` | 异步流式 |
| `.map()` | 并行处理列表输入 |

---

## 10. 速查对比表

### 同一个任务，三种实现

```python
# ========== 纯 Python (Task 1.2) ==========
# 手写一切，理解底层原理

client = OpenAI(...)
for i in range(5):
    response = client.chat.completions.create(
        model=..., messages=..., tools=tool_schema
    )
    if response.choices[0].message.tool_calls:
        # 手动解析、执行、拼消息
        ...
    else:
        print(response.choices[0].message.content)


# ========== LangChain (Task 2.1) ==========
# 框架封装了循环和解析

executor = AgentExecutor(agent=agent, tools=[get_weather])
result = executor.invoke({"input": "北京天气"})
print(result["output"])


# ========== LangGraph (Task 2.3) ==========
# 用图定义流程，精确控制每一步

app = StateGraph(MyState)
app.add_node("research", research_fn)
app.add_node("report", report_fn)
app.add_edge(START, "research")
app.add_edge("research", "report")
result = app.compile().invoke({"question": "北京天气"})
print(result["answer"])
```

### 选择指南

| 场景 | 推荐方案 |
|------|----------|
| 学习 Agent 原理 | 纯 Python |
| 快速构建单 Agent | LangChain AgentExecutor |
| 复杂流程（分支、循环、重试） | LangGraph |
| 需要人工介入 | LangGraph (interrupt) |
| 需要状态持久化 | LangGraph (checkpointer) |
| 简单 LLM 调用 | LCEL 链 (`prompt | llm | parser`) |
| 生产环境可观测性 | LangGraph + LangSmith |
