# 学习计划改进设计规格

> 日期：2026-06-16
> 状态：已批准

## 改进目标

全面查漏补缺，补充缺失的关键技术主题，让学习计划覆盖更完整。延长周期，学深学透。

## 改进方案：方案 A

新增"阶段 5：进阶主题"，现有 4 个阶段做横向增强。

## 阶段 5 结构（新增）

```
Task 5.1  Prompt Engineering 专项
Task 5.2  可观测性与评估（LangSmith/Langfuse）
Task 5.3  RAG 基础（Embedding + 向量库 + 检索生成）
Task 5.4  RAG Agent（检索作为工具集成进 Agent）
Task 5.5  MCP 实战（用现成 MCP server + 写自己的 MCP server）
```

顺序依据：Prompt Engineering 影响后续所有质量 → 可观测性先学会才能调试 RAG → RAG → MCP 进阶。

## 配套学习文档层

新增概念驱动的学习文档，放 `docs/` 目录。核心原则：**先建立心智模型，再讲机制**。

每份文档结构：
1. 本质是什么
2. 为什么需要它
3. 心智模型（用嵌入式背景类比）
4. 关键概念的相互关系
5. 常见误解纠正
6. 一句话本质
7. 机制/代码（辅助）

文档清单：
- stage1/: what-is-agent, why-function-calling, memory-and-context
- stage2/: abstraction-tradeoffs, state-machine-thinking
- stage3/: why-frameworks-fade, agent-loop-essence
- stage4/: division-of-labor, when-multi-when-single
- stage5/: prompt-as-programming, observability-control, rag-knowledge-injection, mcp-standardization

## 现有阶段横向增强

1. 每个 Task 加"完成检查清单"（3-5 个自测问题）
2. 每个 Task 加"可观测性提示"
3. 每阶段加 requirements.txt

## 时间线

总计约 14-19 周（原 10-14 周）：
- 阶段1: 2 周
- 阶段2: 3-4 周
- 阶段3: 2-3 周
- 阶段4: 3-4 周
- 阶段5: 4-6 周

## 实施方式

用户选择：先把所有概念文档写好。

## 环境约束

- 用户只有智谱和 DeepSeek API
- DeepSeek 无 embedding API，RAG 用智谱 embedding-3 或开源 bge-small-zh
- Task 3.2 Claude Agent SDK 需要 Anthropic Key，可跳过
- MCP 是模型无关协议，智谱/DeepSeek 可用
