"""
Skill 基类 —— 定义统一接口
"""
from typing import Optional


class BaseSkill:
    """AI Skill 基类，所有 skill 必须继承此类"""

    name: str = "base"
    description: str = "Base skill"

    def __init__(self, api_key: str, api_base: str, model: str):
        self.api_key = api_key
        self.api_base = api_base
        self.model = model

    async def execute(self, **kwargs) -> dict:
        """执行 skill，子类必须实现"""
        raise NotImplementedError

    async def call_llm(self, messages: list, **kwargs) -> str:
        """
        统一的大模型调用方法，使用 openai 兼容接口
        """
        try:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(
                api_key=self.api_key,
                base_url=self.api_base,
            )
            response = await client.chat.completions.create(
                model=self.model,
                messages=messages,
                **kwargs,
            )
            return response.choices[0].message.content or ""
        except ImportError:
            # 如果 openai 不可用，使用 httpx 作为后备
            import httpx
            import json

            url = f"{self.api_base.rstrip('/')}/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
            payload = {
                "model": self.model,
                "messages": messages,
                **kwargs,
            }
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(url, headers=headers, json=payload)
                resp.raise_for_status()
                data = resp.json()
                return data["choices"][0]["message"]["content"] or ""
