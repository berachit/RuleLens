import json
import logging
from typing import List, Dict, Any, AsyncGenerator
import httpx
from app.services.llm.base import LLMProvider

logger = logging.getLogger(__name__)


class GeminiProvider(LLMProvider):
    """Google Gemini LLM provider via official REST API."""

    def __init__(self, api_key: str, model: str = "gemini-1.5-flash"):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"

    def _convert_messages(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """Converts standard chat messages to Gemini API contents format."""
        contents = []
        system_instruction = None

        for msg in messages:
            role = msg["role"]
            text = msg["content"]

            if role == "system":
                system_instruction = {"parts": [{"text": text}]}
            elif role == "user":
                contents.append({"role": "user", "parts": [{"text": text}]})
            elif role == "assistant":
                contents.append({"role": "model", "parts": [{"text": text}]})

        payload: Dict[str, Any] = {"contents": contents}
        if system_instruction:
            payload["systemInstruction"] = system_instruction
        return payload

    async def generate(self, messages: List[Dict[str, str]], **kwargs) -> str:
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is not set.")

        payload = self._convert_messages(messages)
        url = f"{self.base_url}/models/{self.model}:generateContent?key={self.api_key}"

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, json=payload)
            if resp.status_code != 200:
                raise RuntimeError(f"Gemini API error {resp.status_code}: {resp.text}")

            data = resp.json()
            try:
                candidate = data["candidates"][0]
                text = candidate["content"]["parts"][0]["text"]
                return text.strip()
            except (KeyError, IndexError) as e:
                raise RuntimeError(f"Failed to parse Gemini response: {e}")

    async def stream(self, messages: List[Dict[str, str]], **kwargs) -> AsyncGenerator[str, None]:
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is not set.")

        payload = self._convert_messages(messages)
        url = f"{self.base_url}/models/{self.model}:streamGenerateContent?alt=sse&key={self.api_key}"

        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream("POST", url, json=payload) as response:
                if response.status_code != 200:
                    yield f"Error: Gemini returned status {response.status_code}"
                    return

                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:].strip()
                        if data_str == "[DONE]":
                            break
                        try:
                            chunk = json.loads(data_str)
                            part = chunk["candidates"][0]["content"]["parts"][0]["text"]
                            yield part
                        except Exception:
                            continue
