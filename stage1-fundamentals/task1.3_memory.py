"""
Task 1.3: Agent 记忆机制
========================
目标：在 Task 1.2 基础上实现记忆系统
      - 短期记忆：对话历史的滑动窗口
      - 长期记忆：持久化到文件的向量检索

核心概念：
  短期记忆 = 消息列表（会话内）
  长期记忆 = 外部存储（跨会话）

安装依赖：
  pip install openai python-dotenv numpy
"""

import os
import json
import hashlib
import sys
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from llm_config import get_client, get_model_name

client = get_client()
model = get_model_name()

# 复用 Task 1.2 的工具定义
from task1_2_tool_use import TOOLS_SCHEMA, TOOL_FUNCTIONS


# ============================================================
# 短期记忆：滑动窗口
# ============================================================

class ShortTermMemory:
    """
    短期记忆 = 最近 N 条消息

    为什么需要截断？
    - LLM 有 token 限制（gpt-4o-mini: 128K, claude-3.5: 200K）
    - 每次调用都发送完整历史，token 越多越贵、越慢
    - 太老的消息对当前对话价值很低

    策略：保留 system prompt + 最近 N 轮对话
    """

    def __init__(self, max_messages: int = 20):
        self.messages = []
        self.max_messages = max_messages

    def add(self, role: str, content: str, **kwargs):
        msg = {"role": role, "content": content, **kwargs}
        self.messages.append(msg)
        self._trim()

    def add_tool_call(self, assistant_message):
        """添加包含工具调用的 assistant 消息"""
        self.messages.append(assistant_message)
        self._trim()

    def add_tool_result(self, tool_call_id: str, content: str):
        """添加工具结果"""
        self.messages.append({
            "role": "tool",
            "tool_call_id": tool_call_id,
            "content": content
        })
        self._trim()

    def get_messages(self) -> list:
        return self.messages

    def _trim(self):
        """滑动窗口：保留 system + 最近 N 条"""
        if len(self.messages) <= self.max_messages:
            return

        # 保留第一条（system prompt）和最近的 N-1 条
        system_msg = self.messages[0]
        recent = self.messages[-(self.max_messages - 1):]
        self.messages = [system_msg] + recent

    def get_token_estimate(self) -> int:
        """粗略估算当前消息的 token 数（中文约 1 字 = 1.5 token）"""
        total = 0
        for msg in self.messages:
            content = msg.get("content", "")
            if content:
                total += len(content) * 1.5
        return int(total)


# ============================================================
# 长期记忆：基于文件的存储 + 简单检索
# ============================================================

class LongTermMemory:
    """
    长期记忆 = 持久化的信息存储

    生产环境中通常用向量数据库（ChromaDB, Pinecone, Weaviate）。
    这里用 JSON 文件 + 简单关键词匹配来演示概念。

    存储什么？
    - 用户偏好（"我喜欢用 Python"）
    - 重要事实（"我的项目叫 AgentStudy"）
    - 之前的对话摘要
    """

    def __init__(self, storage_file: str = "memory_store.json"):
        self.storage_file = storage_file
        self.memories = self._load()

    def _load(self) -> list:
        if os.path.exists(self.storage_file):
            with open(self.storage_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return []

    def _save(self):
        with open(self.storage_file, "w", encoding="utf-8") as f:
            json.dump(self.memories, f, ensure_ascii=False, indent=2)

    def store(self, content: str, category: str = "fact"):
        """存储一条记忆"""
        memory = {
            "id": hashlib.md5(content.encode()).hexdigest()[:8],
            "content": content,
            "category": category,  # fact / preference / summary
            "timestamp": datetime.now().isoformat(),
        }
        # 去重
        if not any(m["content"] == content for m in self.memories):
            self.memories.append(memory)
            self._save()
            print(f"  [记忆] 已存储: {content[:50]}...")

    def retrieve(self, query: str, top_k: int = 3) -> list[str]:
        """
        检索相关记忆

        生产环境用 embedding 相似度搜索，
        这里用简单的关键词匹配演示概念。
        """
        if not self.memories:
            return []

        # 简单的关键词匹配得分
        query_words = set(query)
        scored = []
        for mem in self.memories:
            mem_words = set(mem["content"])
            overlap = len(query_words & mem_words)
            scored.append((overlap, mem["content"]))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [content for score, content in scored[:top_k] if score > 0]

    def get_context_string(self, query: str) -> str:
        """获取格式化的记忆上下文，用于注入到 system prompt"""
        relevant = self.retrieve(query)
        if not relevant:
            return ""
        memories_text = "\n".join(f"  - {m}" for m in relevant)
        return f"\n\n以下是关于用户的已知信息：\n{memories_text}"


# ============================================================
# 带记忆的 Agent
# ============================================================

class MemoryAgent:
    """
    整合短期记忆 + 长期记忆的 Agent

    工作流程：
    1. 接收用户输入
    2. 从长期记忆中检索相关信息
    3. 构建 prompt（system + 长期记忆 + 短期记忆 + 当前问题）
    4. ReAct 循环
    5. 从对话中提取重要信息存入长期记忆
    """

    def __init__(self):
        self.stm = ShortTermMemory(max_messages=20)
        self.ltm = LongTermMemory()

        # 初始化 system prompt
        self.stm.add("system",
            "你是一个有用的助手。你可以使用工具帮助用户。请用中文回答。"
        )

    def chat(self, user_input: str, max_iterations: int = 5) -> str:
        # 1. 从长期记忆检索相关上下文
        memory_context = self.ltm.get_context_string(user_input)

        # 2. 构建带记忆的用户消息
        enhanced_input = user_input
        if memory_context:
            enhanced_input = f"{user_input}\n\n[系统注入的相关记忆: {memory_context}]"

        self.stm.add("user", enhanced_input)

        # 3. ReAct 循环（与 Task 1.2 相同）
        for i in range(max_iterations):
            response = client.chat.completions.create(
                model=model,
                messages=self.stm.get_messages(),
                tools=TOOLS_SCHEMA,
                tool_choice="auto",
                temperature=0,
            )

            message = response.choices[0].message

            if message.tool_calls:
                self.stm.add_tool_call(message)
                for tool_call in message.tool_calls:
                    func_name = tool_call.function.name
                    func_args = json.loads(tool_call.function.arguments)
                    print(f"  调用工具: {func_name}({func_args})")

                    if func_name in TOOL_FUNCTIONS:
                        result = TOOL_FUNCTIONS[func_name](**func_args)
                    else:
                        result = f"未知工具: {func_name}"

                    self.stm.add_tool_result(tool_call.id, str(result))
            else:
                if message.content:
                    self.stm.add("assistant", message.content)
                    # 4. 提取重要信息存入长期记忆
                    self._extract_memories(user_input, message.content)
                    return message.content

        return "达到最大迭代次数。"

    def _extract_memories(self, user_input: str, assistant_response: str):
        """
        从对话中提取值得记住的信息

        生产环境可以用 LLM 来做信息提取，
        这里用简单规则演示概念。
        """
        # 检测用户偏好
        preference_keywords = ["我喜欢", "我习惯", "我用", "我的项目", "我叫"]
        for keyword in preference_keywords:
            if keyword in user_input:
                self.ltm.store(user_input, category="preference")

        # 检测事实信息
        fact_keywords = ["是", "叫", "有", "在"]
        for keyword in fact_keywords:
            if any(k in user_input for k in preference_keywords):
                continue
            if keyword in user_input and len(user_input) < 100:
                self.ltm.store(user_input, category="fact")
                break


# ============================================================
# 交互式运行
# ============================================================

if __name__ == "__main__":
    agent = MemoryAgent()

    print("带记忆的 Agent（输入 'quit' 退出）")
    print("=" * 60)

    # 模拟多轮对话
    test_inputs = [
        "我的项目叫 AgentStudy，是一个学习 AI Agent 开发的仓库",
        "帮我查一下北京天气",
        "你还记得我的项目叫什么吗？",  # 测试长期记忆
    ]

    for user_input in test_inputs:
        print(f"\n用户: {user_input}")
        response = agent.chat(user_input)
        print(f"Agent: {response}")

    # 查看存储的长期记忆
    print("\n" + "=" * 60)
    print("长期记忆内容:")
    for mem in agent.ltm.memories:
        print(f"  [{mem['category']}] {mem['content']}")
