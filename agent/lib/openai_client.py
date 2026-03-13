"""
OpenAI client: LLM (chat completions) for text generation.
"""

import os
import time

import requests

OPENAI_BASE_URL = "https://api.openai.com/v1"
OPENAI_LLM_MODEL = os.environ.get("OPENAI_LLM_MODEL", "gpt-4o")


class OpenAIClient:
    def __init__(self, api_key: str | None = None):
        self._api_key = api_key or os.environ["OPENAI_API_KEY"]

    def generate_content(self, prompt: str, model: str = OPENAI_LLM_MODEL) -> str:
        max_retries = 5
        for attempt in range(max_retries):
            resp = requests.post(
                f"{OPENAI_BASE_URL}/chat/completions",
                headers={"Authorization": f"Bearer {self._api_key}", "Content-Type": "application/json"},
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 8192,
                    "temperature": 0.7,
                },
                timeout=300,
            )
            if resp.status_code == 429 and attempt < max_retries - 1:
                retry_after = 2 ** (attempt + 1)
                try:
                    retry_after = min(int(resp.headers.get("Retry-After", retry_after)), 60)
                except (TypeError, ValueError):
                    pass
                time.sleep(retry_after)
                continue
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]
