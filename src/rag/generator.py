# -*- coding: utf-8 -*-
"""生成器：通过 DeepSeek API 调用 LLM 生成答案。"""
from __future__ import annotations
import os
from openai import OpenAI


class Generator:
    def __init__(
        self,
        model: str = "deepseek-flash",
        base_url: str = "https://api.deepseek.com",
        api_key: str | None = None,
        temperature: float = 0.2,
        max_tokens: int = 512,
        timeout: float = 60,
    ):
        key = api_key or os.environ.get("DEEPSEEK_API_KEY")
        if not key:
            raise RuntimeError("缺少 DEEPSEEK_API_KEY（请在环境变量中配置）")
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.client = OpenAI(api_key=key, base_url=base_url, timeout=timeout)

    def complete(self, messages: list[dict]) -> str:
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )
        return (resp.choices[0].message.content or "").strip()

    def ask(self, user_prompt: str, system: str = "") -> str:
        msgs = []
        if system:
            msgs.append({"role": "system", "content": system})
        msgs.append({"role": "user", "content": user_prompt})
        return self.complete(msgs)
