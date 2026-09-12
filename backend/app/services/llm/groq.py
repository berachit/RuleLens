import json
import logging
from typing import List, Dict, Any, AsyncGenerator
import httpx
from app.services.llm.base import LLMProvider

logger = logging.getLogger(__name__)


class GroqProvider(LLMProvider):
    """Groq LLM provider via OpenAI-compatible completions API."""

    def __init__(self, api_key: str, model: str = "openai/gpt-oss-20b"):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://api.groq.com/openai/v1/chat/completions"

    async def generate(self, messages: List[Dict[str, str]], **kwargs) -> str:
        if not self.api_key:
            raise ValueError("GROQ_API_KEY is not set.")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": kwargs.get("temperature", 0.0),
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(self.base_url, headers=headers, json=payload)
            if resp.status_code != 200:
                raise RuntimeError(f"Groq API error {resp.status_code}: {resp.text}")

            data = resp.json()
            return data["choices"][0]["message"]["content"].strip()

    async def stream(self, messages: List[Dict[str, str]], **kwargs) -> AsyncGenerator[str, None]:
        if not self.api_key:
            raise ValueError("GROQ_API_KEY is not set.")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": kwargs.get("temperature", 0.0),
            "stream": True,
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream("POST", self.base_url, headers=headers, json=payload) as response:
                if response.status_code != 200:
                    yield f"Error: Groq returned status {response.status_code}"
                    return

                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:].strip()
                        if data_str == "[DONE]":
                            break
                        try:
                            chunk = json.loads(data_str)
                            delta = chunk["choices"][0]["delta"].get("content", "")
                            if delta:
                                yield delta
                        except Exception:
                            continue
