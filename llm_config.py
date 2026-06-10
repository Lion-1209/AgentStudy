"""
LLM 配置 — 支持 DeepSeek 和智谱 (GLM)
========================================
两个平台都兼容 OpenAI API 格式，只需改 base_url 和 model。

配置方式：
  1. 复制 .env.example 为 .env
  2. 填入你有的 API Key
  3. 代码会自动选择可用的 Provider
"""

import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

# ============================================================
# Provider 配置
# ============================================================

PROVIDERS = {
    "deepseek": {
        "api_key_env": "DEEPSEEK_API_KEY",
        "base_url": "https://api.deepseek.com",
        "model": "deepseek-chat",          # deepseek-chat / deepseek-reasoner
    },
    "zhipu": {
        "api_key_env": "ZHIPU_API_KEY",
        "base_url": "https://open.bigmodel.cn/api/paas/v4",
        "model": "glm-4-flash",            # glm-4-flash(免费) / glm-4-plus / glm-4-air
    },
}


def get_provider() -> tuple[str, dict]:
    """自动检测可用的 Provider"""
    for name, config in PROVIDERS.items():
        if os.getenv(config["api_key_env"]):
            return name, config

    raise ValueError(
        "未找到可用的 API Key。请在 .env 文件中配置：\n"
        "  DEEPSEEK_API_KEY=xxx  (DeepSeek)\n"
        "  ZHIPU_API_KEY=xxx     (智谱)\n"
    )


def get_client() -> OpenAI:
    """获取 OpenAI 兼容的客户端"""
    name, config = get_provider()
    print(f"[LLM] 使用 Provider: {name}, Model: {config['model']}")
    return OpenAI(
        api_key=os.getenv(config["api_key_env"]),
        base_url=config["base_url"],
    )


def get_model_name() -> str:
    """获取当前模型名称"""
    _, config = get_provider()
    return config["model"]


# ============================================================
# 快速测试
# ============================================================

if __name__ == "__main__":
    client = get_client()
    model = get_model_name()

    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": "你好，请用一句话介绍你自己"}],
        temperature=0,
    )
    print(f"回复: {response.choices[0].message.content}")
