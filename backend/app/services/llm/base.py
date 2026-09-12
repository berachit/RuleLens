from abc import ABC, abstractmethod
from typing import List, Dict, Any, AsyncGenerator


class LLMProvider(ABC):
    """Abstract interface for LLM providers (Groq, Gemini, Deterministic Fallback)."""

    @abstractmethod
    async def generate(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Asynchronously generates a complete text completion."""
        pass

    @abstractmethod
    async def stream(self, messages: List[Dict[str, str]], **kwargs) -> AsyncGenerator[str, None]:
        """Asynchronously streams response tokens/chunks."""
        pass
