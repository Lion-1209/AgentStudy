# OpenAI Python SDK 常用 API 完整中文参考

> 智谱/DeepSeek 完全兼容此 API 格式，只需改 `base_url`
> 完整官方文档: https://platform.openai.com/docs/api-reference

---

## 目录

1. [客户端初始化](#1-客户端初始化)
2. [基础对话调用](#2-基础对话调用)
3. [消息类型详解 (messages)](#3-消息类型详解-messages)
4. [Function Calling 工具调用](#4-function-calling-工具调用)
5. [流式输出 (Streaming)](#5-流式输出-streaming)
6. [异步调用 (Async)](#6-异步调用-async)
7. [错误处理](#7-错误处理)
8. [Token 计算](#8-token-计算)
9. [全部参数速查表](#9-全部参数速查表)
10. [Provider 配置速查](#10-provider-配置速查)

---

## 1. 客户端初始化

```python
from openai import OpenAI

# 方式一：直接传参
client = OpenAI(
    api_key="sk-xxx",
    base_url="https://api.openai.com/v1",  # 默认值，可省略
    timeout=60.0,           # 请求超时（秒）
    max_retries=2,          # 失败自动重试次数
)

# 方式二：从环境变量读取（推荐）
# 会自动读取 OPENAI_API_KEY 和 OPENAI_BASE_URL
client = OpenAI()

# 方式三：用我们项目的 llm_config.py
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from llm_config import get_client
client = get_client()
```

### 各平台 base_url 和模型名

| 平台 | base_url | 免费模型 | 付费模型 |
|------|----------|----------|----------|
| OpenAI | `https://api.openai.com/v1` | 无 | gpt-4o-mini, gpt-4o |
| DeepSeek | `https://api.deepseek.com` | 无 | deepseek-chat, deepseek-reasoner |
| 智谱 | `https://open.bigmodel.cn/api/paas/v4` | glm-4-flash | glm-4-plus, glm-4-air |

---

## 2. 基础对话调用

```python
response = client.chat.completions.create(
    model="deepseek-chat",
    messages=[
        {"role": "system", "content": "你是一个有用的助手"},
        {"role": "user", "content": "你好"},
    ],
    temperature=0,
    max_tokens=1024,
)

# 获取回复文本
text = response.choices[0].message.content
print(text)
```

### response 对象结构

```python
response = client.chat.completions.create(...)

response.id               # "chatcmpl-abc123"，请求的唯一 ID
response.object            # "chat.completion"
response.created           # 创建时间戳（整数）
response.model             # 实际使用的模型名

response.choices           # 列表，通常只有一个元素
response.choices[0].index  # 0
response.choices[0].message.role       # "assistant"
response.choices[0].message.content   # 回复文本
response.choices[0].finish_reason     # 结束原因（见下表）

response.usage.prompt_tokens     # 输入 token 数
response.usage.completion_tokens # 输出 token 数
response.usage.total_tokens      # 总 token 数
```

### finish_reason 含义

| 值 | 含义 |
|----|------|
| `"stop"` | 正常结束，模型自己决定说完了 |
| `"length"` | 达到 max_tokens 限制，被截断了 |
| `"tool_calls"` | 模型要调用工具，还没说完 |
| `"content_filter"` | 内容被安全过滤器拦截 |

---

## 3. 消息类型详解 (messages)

### 基本三种 role

| role | 说明 | 类比 |
|------|------|------|
| `system` | 系统指令，定义 AI 的角色和行为规则 | 岗位说明书 |
| `user` | 用户发的消息 | 你问的问题 |
| `assistant` | AI 的回复（放在历史中） | AI 之前的回答 |

```python
messages = [
    {"role": "system", "content": "你是一个 Python 专家"},
    {"role": "user", "content": "什么是列表推导式？"},
    {"role": "assistant", "content": "列表推导式是..."},
    {"role": "user", "content": "能举个例子吗？"},
]
```

### 多轮对话 — 维护消息历史

```python
messages = [
    {"role": "system", "content": "你是助手"},
]

# 第一轮
messages.append({"role": "user", "content": "1+1等于几"})
response = client.chat.completions.create(model="glm-4-flash", messages=messages)
messages.append({"role": "assistant", "content": response.choices[0].message.content})

# 第二轮（LLM 能看到之前的对话）
messages.append({"role": "user", "content": "那2+2呢"})
response = client.chat.completions.create(model="glm-4-flash", messages=messages)
print(response.choices[0].message.content)  # "2+2等于4"
```

### 消息历史的 token 管理

```python
# 简单策略：保留 system + 最近 N 条
def trim_messages(messages, max_messages=20):
    if len(messages) <= max_messages:
        return messages
    system = messages[0]  # 保留 system prompt
    recent = messages[-(max_messages - 1):]  # 最近的 N-1 条
    return [system] + recent
```

---

## 4. Function Calling 工具调用

这是 Agent 开发最核心的 API。Agent 能"做事"就靠它。

### 4.1 定义工具

```python
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",              # 函数名（唯一标识）
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
                        "enum": ["celsius", "fahrenheit"],  # 枚举限制
                        "description": "温度单位",
                    },
                },
                "required": ["city"],            # 必填参数
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculate",
            "description": "计算数学表达式",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "数学表达式，如 '(25+28)/2'",
                    },
                },
                "required": ["expression"],
            },
        },
    },
]
```

### 4.2 参数类型速查（JSON Schema）

| JSON Schema 类型 | Python 对应 | 示例 |
|-----------------|-------------|------|
| `"string"` | `str` | `"北京"` |
| `"number"` | `float` | `3.14` |
| `"integer"` | `int` | `42` |
| `"boolean"` | `bool` | `true` |
| `"array"` | `list` | `["a", "b"]` |
| `"object"` | `dict` | `{"key": "val"}` |

常用约束：
```json
{
    "type": "string",
    "enum": ["option_a", "option_b"],   // 限定可选值
    "minLength": 1,                       // 最小长度
    "maxLength": 100                      // 最大长度
}
```

### 4.3 发起带工具的请求

```python
response = client.chat.completions.create(
    model="deepseek-chat",
    messages=messages,
    tools=tools,               # 传入工具定义列表
    tool_choice="auto",        # 工具调用策略
)
```

### 4.4 tool_choice 选项

| 值 | 含义 | 使用场景 |
|----|------|----------|
| `"auto"` | LLM 自己决定是否调用工具 | 最常用，通用 Agent |
| `"none"` | 禁止调用工具，强制纯文本回复 | 纯对话场景 |
| `"required"` | 必须调用工具，不能纯文本 | 强制走工具流程 |
| `{"type": "function", "function": {"name": "get_weather"}}` | 强制调用指定工具 | 路由到固定工具 |

```python
# 示例：强制调用 get_weather
response = client.chat.completions.create(
    model="deepseek-chat",
    messages=messages,
    tools=tools,
    tool_choice={"type": "function", "function": {"name": "get_weather"}},
)
```

### 4.5 处理 LLM 的工具调用请求

```python
message = response.choices[0].message

# message 的关键属性：
message.content       # 文本内容，可能为 None（只有工具调用时）
message.tool_calls    # 工具调用列表，可能为 None
message.role          # "assistant"

if message.tool_calls:
    for tool_call in message.tool_calls:
        tool_call.id                    # 唯一 ID，如 "call_abc123"
        tool_call.type                  # "function"
        tool_call.function.name         # 工具名: "get_weather"
        tool_call.function.arguments    # 参数 JSON 字符串: '{"city": "北京"}'

        # 解析参数
        import json
        args = json.loads(tool_call.function.arguments)

        # 执行你的函数
        result = get_weather(**args)

        # 把结果送回给 LLM
        # 关键：必须用 tool_call_id 关联请求和响应
        messages.append(message)                    # 先加 assistant 的工具调用消息
        messages.append({
            "role": "tool",
            "tool_call_id": tool_call.id,           # 必须对应上
            "content": str(result),                  # 工具返回结果（字符串）
        })
else:
    # LLM 直接回复文本，没有调用工具
    text = message.content
```

### 4.6 完整的 Agent 工具调用循环

```python
import json

def run_agent(user_query: str, tools: list, tool_functions: dict, max_steps: int = 5) -> str:
    """完整的 Agent 循环"""
    messages = [
        {"role": "system", "content": "你是助手，可以用工具帮助用户。"},
        {"role": "user", "content": user_query},
    ]

    for step in range(max_steps):
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=messages,
            tools=tools,
            tool_choice="auto",
        )
        message = response.choices[0].message

        if message.tool_calls:
            # 有工具调用 → 执行工具，继续循环
            messages.append(message)
            for tc in message.tool_calls:
                func_name = tc.function.name
                func_args = json.loads(tc.function.arguments)

                # 执行工具
                if func_name in tool_functions:
                    result = tool_functions[func_name](**func_args)
                else:
                    result = f"错误：未知工具 {func_name}"

                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": str(result),
                })
        else:
            # 没有工具调用 → 返回最终回答
            return message.content

    return "达到最大步数，任务未完成。"

# 使用
tool_functions = {"get_weather": get_weather, "calculate": calculate}
answer = run_agent("北京和上海温差多少", tools, tool_functions)
```

---

## 5. 流式输出 (Streaming)

### 5.1 基本流式

```python
stream = client.chat.completions.create(
    model="deepseek-chat",
    messages=[{"role": "user", "content": "讲个故事"}],
    stream=True,    # 开启流式
)

for chunk in stream:
    # chunk 结构和 response 类似，但内容是增量的
    if chunk.choices[0].delta.content:    # delta 而不是 message
        print(chunk.choices[0].delta.content, end="", flush=True)
```

### 5.2 流式 + 工具调用

```python
stream = client.chat.completions.create(
    model="deepseek-chat",
    messages=messages,
    tools=tools,
    stream=True,
)

# 流式工具调用需要手动拼接
tool_calls = {}  # 用 id 做 key，逐步拼接

for chunk in stream:
    delta = chunk.choices[0].delta

    # 文本内容
    if delta.content:
        print(delta.content, end="", flush=True)

    # 工具调用（增量）
    if delta.tool_calls:
        for tc in delta.tool_calls:
            idx = tc.index
            if idx not in tool_calls:
                tool_calls[idx] = {"id": "", "name": "", "arguments": ""}
            if tc.id:
                tool_calls[idx]["id"] = tc.id
            if tc.function.name:
                tool_calls[idx]["name"] += tc.function.name
            if tc.function.arguments:
                tool_calls[idx]["arguments"] += tc.function.arguments

# stream 结束后，tool_calls 就是完整的工具调用
for idx, tc in tool_calls.items():
    print(f"工具: {tc['name']}, 参数: {tc['arguments']}")
```

### 5.3 流式的 finish_reason

```python
for chunk in stream:
    if chunk.choices[0].finish_reason:
        print(f"\n结束原因: {chunk.choices[0].finish_reason}")
```

---

## 6. 异步调用 (Async)

```python
import asyncio
from openai import AsyncOpenAI

client = AsyncOpenAI(api_key="your-key", base_url="...")

async def main():
    # 异步调用，用法和同步完全一样，只是加了 await
    response = await client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": "你好"}],
    )
    print(response.choices[0].message.content)

asyncio.run(main())
```

### 并发调用多个请求

```python
async def ask(question: str) -> str:
    response = await client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": question}],
    )
    return response.choices[0].message.content

async def main():
    # 同时发 3 个请求
    results = await asyncio.gather(
        ask("1+1=?"),
        ask("2+2=?"),
        ask("3+3=?"),
    )
    for q, a in zip(["1+1", "2+2", "3+3"], results):
        print(f"{q} = {a}")

asyncio.run(main())
```

---

## 7. 错误处理

```python
from openai import (
    APITimeoutError,        # 超时
    APIConnectionError,     # 网络连接失败
    RateLimitError,         # 请求频率超限（429）
    BadRequestError,        # 请求参数错误（400）
    AuthenticationError,    # API Key 无效（401）
    APIStatusError,         # 其他 HTTP 错误
)

try:
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": "你好"}],
    )
except AuthenticationError:
    print("API Key 无效，请检查 .env 配置")
except RateLimitError:
    print("请求太频繁，稍后再试")
except APITimeoutError:
    print("请求超时，可能是网络问题")
except APIConnectionError:
    print("无法连接到 API 服务器")
except BadRequestError as e:
    print(f"请求参数错误: {e}")
except APIStatusError as e:
    print(f"HTTP {e.status_code}: {e.message}")
```

### 自动重试

```python
# 在客户端初始化时设置
client = OpenAI(
    api_key="your-key",
    max_retries=3,        # 自动重试次数（默认 2）
    timeout=30.0,         # 超时时间（秒）
)
```

---

## 8. Token 计算

```python
# 粗略估算（中文约 1 字 = 1.5-2 token）
def estimate_tokens(text: str) -> int:
    """粗略估算 token 数"""
    chinese_chars = sum(1 for c in text if '一' <= c <= '鿿')
    other_chars = len(text) - chinese_chars
    return int(chinese_chars * 1.5 + other_chars * 0.5)

# 精确计算（需要 tiktoken 库，仅支持 OpenAI 模型）
# pip install tiktoken
# import tiktoken
# enc = tiktoken.encoding_for_model("gpt-4")
# tokens = len(enc.encode("你好世界"))

# 从 API 响应获取实际 token 用量
response = client.chat.completions.create(...)
print(f"输入: {response.usage.prompt_tokens} token")
print(f"输出: {response.usage.completion_tokens} token")
print(f"总计: {response.usage.total_tokens} token")
```

---

## 9. 全部参数速查表

### chat.completions.create() 参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `model` | string | **必填** | 模型名称 |
| `messages` | list | **必填** | 对话消息列表 |
| `temperature` | float | 1 | 0=确定性高，2=随机性高 |
| `max_tokens` | int | 模型上限 | 最大输出 token 数 |
| `top_p` | float | 1 | 核采样概率，和 temperature 二选一调节 |
| `n` | int | 1 | 生成几个候选回复 |
| `stream` | bool | False | 是否流式输出 |
| `stop` | str/list | None | 遇到这些字符串就停止生成 |
| `tools` | list | None | 工具定义列表 |
| `tool_choice` | str/dict | "auto" | 工具调用策略 |
| `response_format` | dict | None | 指定输出格式 |
| `seed` | int | None | 随机种子，相同 seed+temperature=0 结果一致 |
| `presence_penalty` | float | 0 | -2.0~2.0，正值鼓励谈新话题 |
| `frequency_penalty` | float | 0 | -2.0~2.0，正值降低重复内容 |
| `logprobs` | bool | False | 是否返回每个 token 的概率 |
| `user` | string | None | 用户标识，用于审计 |

### response_format — 强制 JSON 输出

```python
# 方式一：简单 JSON 模式
response = client.chat.completions.create(
    model="deepseek-chat",
    messages=[{"role": "user", "content": "列出3个水果，用JSON格式"}],
    response_format={"type": "json_object"},  # 强制输出合法 JSON
)
# 注意：用了 json_object，prompt 里必须提到 "JSON"

# 方式二：指定 JSON Schema（部分平台支持）
response = client.chat.completions.create(
    model="deepseek-chat",
    messages=[{"role": "user", "content": "今天北京天气"}],
    response_format={
        "type": "json_schema",
        "json_schema": {
            "name": "weather",
            "schema": {
                "type": "object",
                "properties": {
                    "city": {"type": "string"},
                    "temp": {"type": "integer"},
                    "condition": {"type": "string"},
                },
                "required": ["city", "temp", "condition"],
            },
        },
    },
)
```

---

## 10. Provider 配置速查

```python
# ===== DeepSeek =====
client = OpenAI(
    api_key="sk-xxx",
    base_url="https://api.deepseek.com",
)
# 模型：deepseek-chat（通用）, deepseek-reasoner（推理）

# ===== 智谱 GLM =====
client = OpenAI(
    api_key="xxx.xxx",
    base_url="https://open.bigmodel.cn/api/paas/v4",
)
# 模型：glm-4-flash（免费）, glm-4-plus（付费）, glm-4-air（轻量）

# ===== OpenAI =====
client = OpenAI(api_key="sk-xxx")
# 模型：gpt-4o-mini（便宜）, gpt-4o（强）, gpt-4-turbo

# ===== 本地模型（Ollama）=====
client = OpenAI(
    api_key="ollama",        # 随便填
    base_url="http://localhost:11434/v1",
)
# 模型：qwen2, llama3, mistral 等
```
