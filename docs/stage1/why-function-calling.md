# 为什么需要 Function Calling：结构化通信契约

> 阶段 1 概念文档 | 配合 Task 1.1、1.2 对比阅读

---

## 1. 本质是什么

Function Calling 的本质是：**把 LLM 和外部世界的通信方式，从"自由文本"升级成"结构化契约"。**

你在 Task 1.1 里体会过这个问题——你让 LLM 按 `Action: 工具名` 格式输出，结果它输出 `Action: 使用 get_weather 工具获取天气信息`。你的正则匹配不到，Agent 就卡死了。

这不是 LLM "不听话"，而是**自由文本本质上是一种不可靠的通信信道**。Function Calling 用结构化 JSON 替代文本，从根上消除了这个问题。

## 2. 为什么需要它（信息论视角）

把 LLM 调用工具想象成"两个人协作完成一件事"：

### 通信的两种方式

**方式 A：自然语言（Task 1.1 的做法）**

> "嗯，我觉得应该用那个查天气的工具，参数是北京这座城市。"

你得从这句话里**解析**出：工具名 = get_weather，参数 = 北京。但自然语言有无穷多种表达方式，解析必然脆弱。

**方式 B：结构化契约（Task 1.2 的做法）**

```json
{"name": "get_weather", "arguments": {"city": "北京"}}
```

这是**契约**——双方事先约定好格式，没有歧义。

### 为什么方式 A 注定不可靠

信息论里有个概念叫**信道噪声**。自然语言是高噪声信道：同一个意思可以有一万种说法，解析器必须处理所有变体。

```
"Action: get_weather"           ← 你期望的
"Action: 使用 get_weather 工具"  ← LLM 实际输出的（语义对，格式错）
"我要调用天气查询功能"           ← LLM 可能这样输出（更离谱）
```

你写的正则 `r"Action:\s*(\w+)"` 只能匹配第一种。LLM 是概率模型，它优化的是"语义合理"，不是"格式精确"。

**Function Calling 的解法：让 API 层（而不是文本层）来保证格式。** 你声明工具的 JSON Schema，API 直接返回结构化对象，跳过了"生成文本→解析文本"这个高噪声环节。

## 3. 心智模型（嵌入式类比）

| Task 1.1（文本解析） | Task 1.2（Function Calling） |
|---------------------|---------------------------|
| 串口收 ASCII 字符串，自己写解析 | 用结构化的通信协议（如 Modbus、CAN 报文） |
| 自己处理所有边界情况 | 协议层保证帧格式正确 |
| 偶尔解析失败，系统崩溃 | 有 CRC 校验，格式可靠 |

你做嵌入式肯定懂：**为什么不直接用文本协议？因为不可靠。** 同样的道理，Function Calling 就是 LLM 的"结构化通信协议"。

## 4. 关键概念的相互关系

Function Calling 涉及三个角色，理解它们的分工就懂了整个机制：

```
┌──────────┐  声明工具(schema)   ┌──────────┐
│  你的代码  │ ──────────────────→ │   LLM    │
│          │ ←────────────────── │          │
│          │  返回工具调用(struct) │          │
└──────────┘                      └──────────┘
      │
      │ 执行函数，拿到结果
      ↓
┌──────────┐
│ 工具函数  │ (get_weather 等普通函数)
└──────────┘
```

### 三个角色

1. **Schema 声明（你写的）**：告诉 LLM "有这些工具可用，每个工具长这样"
   ```python
   {"name": "get_weather", "parameters": {"city": "string"}}
   ```

2. **工具调用（LLM 生成的）**：LLM 决定用哪个工具、填什么参数，返回结构化对象
   ```python
   tool_call.function.name == "get_weather"
   tool_call.function.arguments == '{"city": "北京"}'
   ```

3. **工具执行（你写的）**：你的代码真正调用 `get_weather(city="北京")`，把结果喂回去

**关键点：LLM 从不真正执行工具。** 它只是"说"要调用什么。真正执行的是你的代码。这是安全设计——LLM 不可信，不能让它直接操作你的系统。

### 为什么用 `tool_call_id` 关联

LLM 可能一次调用多个工具：
```
工具调用1 (id=abc): get_weather(北京)
工具调用2 (id=xyz): get_weather(上海)
```

返回结果时必须用 id 标明"这是哪个调用的结果"：
```
结果1 (tool_call_id=abc): 晴天 25°C
结果2 (tool_call_id=xyz): 多云 28°C
```

不然 LLM 不知道哪个结果对应哪个调用。这就像 I2C 通信里的设备地址——必须能区分多个从设备。

## 5. 常见误解纠正

### 误解 1："Function Calling 让 LLM 学会了调用函数"

**错。** LLM 没有学会任何"调用"能力。它做的还是老本行——预测文本。只不过 API 在它输出外面套了一层结构化包装。真正调用函数的是**你的代码**。Function Calling 是 API 的工程封装，不是 LLM 的新能力。

### 误解 2："有了 Function Calling，Task 1.1 的文本解析就没用了"

**错。** 文本解析在某些场景仍有用：
- 模型不支持 Function Calling 时（很少见了）
- 需要 LLM 输出复杂推理链时（ReAct 的 Thought 部分）
- 调试时手动观察 LLM 思考

但**作为工具调用机制，永远优先用 Function Calling**。Task 1.1 的价值是让你理解"为什么要"Function Calling，而不是让你继续用文本解析。

### 误解 3："description 写不写无所谓，反正有参数名"

**大错。** `description` 是 LLM 选择工具的**唯一依据**。LLM 看不到你的函数实现，它只看 description 决定"这个工具适不适合当前任务"。description 写得烂，LLM 要么用错工具，要么该用的时候不用。**工具的 description 比函数实现更重要。**

## 6. 一句话本质

> **Function Calling = 用结构化契约替代自然语言通信，把"不可靠的文本解析"变成"可靠的 API 约定"。LLM 只负责"说"要调用什么，你的代码负责"做"。**

## 7. 你写过的代码，对应到这里

对比 Task 1.1 和 1.2 的核心差异：

```python
# Task 1.1：高噪声信道（文本解析）
response = client.chat.completions.create(messages=..., )  # 不传 tools
text = response.choices[0].message.content
action = re.search(r"Action:\s*(\w+)", text)  # ← 可能匹配不到

# Task 1.2：低噪声信道（结构化契约）
response = client.chat.completions.create(messages=..., tools=TOOLS_SCHEMA)
if response.choices[0].message.tool_calls:    # ← 一定有明确结果
    name = tool_call.function.name            # ← 直接读，不用解析
```

同样是"判断 LLM 要不要调工具"，Task 1.1 靠正则猜，Task 1.2 靠结构化字段读。这就是从"玩具"到"生产级"的关键一跃。

## 8. 延伸阅读

- [Anthropic: Advanced Tool Use](https://www.anthropic.com/engineering/advanced-tool-use)
- OpenAI Function Calling 文档：https://platform.openai.com/docs/guides/function-calling
