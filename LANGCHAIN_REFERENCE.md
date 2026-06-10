# LangChain / LangGraph 常用 API 速查

> 完整文档: https://python.langchain.com/docs/
> LangGraph 文档: https://langchain-ai.github.io/langgraph/

---

## 1. ChatOpenAI — LLM 客户端

```python
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(
    model="glm-4-flash",
    base_url="https://open.bigmodel.cn/api/paas/v4",  # 智谱/DeepSeek 改这里
    api_key="your-key",
    temperature=0,
)

# 直接调用
response = llm.invoke("你好")
print(response.content)  # 获取文本
```

---

## 2. @tool — 工具定义

```python
from langchain.tools import tool

@tool
def get_weather(city: str) -> str:
    """获取城市天气信息"""     # docstring 会自动变成工具的 description
    return f"{city}: 晴 25°C"

# LangChain 自动从函数签名 + docstring 生成 JSON Schema
# 不需要手写 Task 1.2 那种 TOOLS_SCHEMA

# 使用
result = get_weather.invoke({"city": "北京"})
print(result)  # "北京: 晴 25°C"
```

**对比纯 Python (Task 1.2)：**

| | 纯 Python | LangChain @tool |
|---|---|---|
| 工具定义 | 手写 ~20 行 JSON Schema | docstring + 类型注解，自动生成 |
| 调用 | `get_weather(city="北京")` | `get_weather.invoke({"city": "北京"})` |

---

## 3. ChatPromptTemplate — 提示词模板

```python
from langchain_core.prompts import ChatPromptTemplate

prompt = ChatPromptTemplate.from_messages([
    ("system", "你是{role}"),          # {role} 是变量
    ("human", "{input}"),              # {input} 是变量
    ("placeholder", "{agent_scratchpad}"),  # Agent 专用，存放中间推理
])

# 填充变量
formatted = prompt.invoke({"role": "助手", "input": "你好"})
```

**注意：** 用 Agent 时 `{agent_scratchpad}` 是必须的，框架会把 Think/Act/Observe 过程填在这里。

---

## 4. Agent + AgentExecutor — Agent 创建和执行

```python
from langchain.agents import create_tool_calling_agent, AgentExecutor

# 创建 Agent
agent = create_tool_calling_agent(llm, tools, prompt)

# 创建执行器（封装了 ReAct 循环）
executor = AgentExecutor(
    agent=agent,
    tools=[get_weather, calculate],  # 工具列表
    max_iterations=5,                # 最大循环次数
    handle_parsing_errors=True,      # 解析出错不崩溃
    verbose=True,                    # 打印中间过程（调试用）
    return_intermediate_steps=True,  # 返回中间步骤
)

# 执行
result = executor.invoke({"input": "北京天气怎么样"})
print(result["output"])              # 最终回答

# 如果开启了 return_intermediate_steps
for action, observation in result["intermediate_steps"]:
    print(f"工具: {action.tool}, 输入: {action.tool_input}, 结果: {observation}")
```

---

## 5. LangGraph — StateGraph 状态图

### 5.1 定义状态

```python
from typing import TypedDict, Annotated
from langgraph.graph.message import add_messages

class MyState(TypedDict):
    messages: Annotated[list, add_messages]  # 消息列表，自动追加
    question: str
    result: str
    retry_count: int
```

**`Annotated[list, add_messages]` 的意思：** 多个节点都往 `messages` 里追加消息时，自动合并而不是覆盖。普通字段（如 `question`）则是后写的覆盖前写的。

### 5.2 定义节点

```python
# 每个节点是一个函数：接收 state，返回 state 的部分更新
def step_one(state: MyState) -> dict:
    # 读取 state
    question = state["question"]
    # 做处理...
    return {"result": "处理结果"}  # 只返回要更新的字段
```

### 5.3 构建图

```python
from langgraph.graph import StateGraph, START, END

workflow = StateGraph(MyState)

# 添加节点
workflow.add_node("step1", step_one)
workflow.add_node("step2", step_two)
workflow.add_node("step3", step_three)

# 确定性边：A 完了必定走 B
workflow.add_edge(START, "step1")     # 入口 → step1
workflow.add_edge("step1", "step2")   # step1 → step2
workflow.add_edge("step3", END)       # step3 → 结束

# 条件边：根据 state 决定走哪条路
def router(state: MyState) -> str:
    if state["retry_count"] < 3:
        return "step1"     # 回到 step1 重试
    return "step3"         # 去最终步骤

workflow.add_conditional_edges(
    "step2",                                    # 从哪个节点出发
    router,                                     # 路由函数
    {"step1": "step1", "step3": "step3"},       # 返回值 → 目标节点
)
```

### 5.4 编译和执行

```python
app = workflow.compile()

# 执行
result = app.invoke({
    "messages": [],
    "question": "你好",
    "result": "",
    "retry_count": 0,
})

print(result["result"])

# 查看图结构
print(app.get_graph().print_ascii())
```

---

## 6. 速查对比：同一个任务，不同写法

### "查北京天气" — 纯 Python vs LangChain vs LangGraph

```python
# === 纯 Python (Task 1.2) ===
client = OpenAI(...)
for i in range(5):
    response = client.chat.completions.create(model=..., messages=..., tools=...)
    if response.choices[0].message.tool_calls:
        # 手动执行工具，手动拼消息
        ...
    else:
        print(response.choices[0].message.content)

# === LangChain (Task 2.1) ===
executor = AgentExecutor(agent=agent, tools=[get_weather])
result = executor.invoke({"input": "北京天气"})
print(result["output"])

# === LangGraph (Task 2.3) ===
app = workflow.compile()
result = app.invoke({"question": "北京天气"})
print(result["result"])
```

**规律：越高级的抽象，代码越少，但灵活性越低。**
