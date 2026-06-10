# OpenAI Python SDK 常用 API 速查

> 智谱/DeepSeek 完全兼容此 API 格式，只需改 `base_url`
> 完整文档: https://platform.openai.com/docs/api-reference

---

## 1. 基础调用

```python
from openai import OpenAI

client = OpenAI(
    api_key="your-key",
    base_url="https://api.deepseek.com",  # 默认是 OpenAI，换成智谱/DeepSeek 的地址
)

# 最简单的调用
response = client.chat.completions.create(
    model="deepseek-chat",          # 模型名
    messages=[                       # 消息列表
        {"role": "system", "content": "你是助手"},
        {"role": "user", "content": "你好"},
    ],
    temperature=0,                   # 0=确定性强，1=创造性高，默认1
    max_tokens=1024,                 # 最大输出 token 数
)

# 获取回复文本
text = response.choices[0].message.content
```

### messages 的三种 role

| role | 说明 | 类比 |
|------|------|------|
| `system` | 系统指令，定义 AI 的角色和行为规则 | 岗位说明书 |
| `user` | 用户发的消息 | 你问的问题 |
| `assistant` | AI 的回复 | AI 的回答 |

```python
messages = [
    {"role": "system", "content": "你是一个 Python 专家"},
    {"role": "user", "content": "什么是列表推导式？"},
    {"role": "assistant", "content": "列表推导式是..."},   # 之前的对话历史
    {"role": "user", "content": "能举个例子吗？"},         # 新问题
]
```

---

## 2. Function Calling（工具调用）

这是 Agent 开发最核心的 API。

### 2.1 定义工具

```python
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",              # 函数名
            "description": "获取城市天气信息",    # 描述越清晰，LLM 选择越准确
            "parameters": {                      # JSON Schema 格式
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "城市名，如'北京'",
                    },
                    "unit": {
                        "type": "string",
                        "enum": ["celsius", "fahrenheit"],
                        "description": "温度单位",
                    },
                },
                "required": ["city"],            # 必填参数
            },
        },
    },
]
```

### 2.2 发起带工具的请求

```python
response = client.chat.completions.create(
    model="deepseek-chat",
    messages=messages,
    tools=tools,               # 传入工具定义
    tool_choice="auto",        # LLM 自己决定是否调用
)
```

### 2.3 tool_choice 选项

| 值 | 含义 |
|----|------|
| `"auto"` | LLM 自己决定是否调用工具（最常用） |
| `"none"` | 禁止调用工具，强制纯文本回复 |
| `"required"` | 强制调用某个工具（不能纯文本回复） |
| `{"type": "function", "function": {"name": "get_weather"}}` | 强制调用指定工具 |

### 2.4 处理 LLM 的工具调用请求

```python
message = response.choices[0].message

if message.tool_calls:
    # LLM 想调用工具
    for tool_call in message.tool_calls:
        name = tool_call.function.name          # 工具名: "get_weather"
        args = json.loads(tool_call.function.arguments)  # 参数: {"city": "北京"}
        tool_call_id = tool_call.id             # 调用 ID，用于关联结果

        # 执行你的函数
        result = get_weather(**args)

        # 把结果送回给 LLM（必须用 tool_call_id 关联）
        messages.append(message)                # 先加 LLM 的调用请求
        messages.append({
            "role": "tool",
            "tool_call_id": tool_call_id,       # 关键：必须对应上
            "content": str(result),
        })
else:
    # LLM 直接回复文本（没有调用工具）
    text = message.content
```

### 2.5 完整的工具调用循环

```python
messages = [{"role": "user", "content": "北京天气怎么样"}]

for i in range(5):  # 最多 5 轮
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=messages,
        tools=tools,
        tool_choice="auto",
    )
    message = response.choices[0].message

    if message.tool_calls:
        messages.append(message)  # 加入 LLM 的工具调用
        for tc in message.tool_calls:
            result = execute_tool(tc.function.name, json.loads(tc.function.arguments))
            messages.append({"role": "tool", "tool_call_id": tc.id, "content": str(result)})
    else:
        print(message.content)   # 最终回答
        break
```

---

## 3. 流式输出（Streaming）

```python
stream = client.chat.completions.create(
    model="deepseek-chat",
    messages=[{"role": "user", "content": "讲个故事"}],
    stream=True,  # 开启流式
)

for chunk in stream:
    delta = chunk.choices[0].delta.content
    if delta:
        print(delta, end="", flush=True)  # 逐字输出
```

---

## 4. 常用参数速查

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `model` | string | 必填 | 模型名 |
| `messages` | list | 必填 | 对话消息列表 |
| `temperature` | float | 1 | 0=确定性，2=随机性 |
| `max_tokens` | int | 模型上限 | 最大输出 token |
| `tools` | list | 无 | 工具定义列表 |
| `tool_choice` | str/dict | "auto" | 工具调用策略 |
| `stream` | bool | False | 是否流式输出 |
| `top_p` | float | 1 | 核采样，和 temperature 二选一 |
| `stop` | str/list | 无 | 遇到指定字符串就停止生成 |
