import logging
from app.config import settings
from app.services.llm.base import LLMProvider
from app.services.llm.gemini import GeminiProvider
from app.services.llm.groq import GroqProvider
from app.services.llm.deterministic import DeterministicEvidenceProvider

logger = logging.getLogger(__name__)


def get_llm_provider() -> LLMProvider:
    """Returns the configured LLM provider based on settings and available credentials."""
    provider_name = settings.LLM_PROVIDER.lower().strip()

    if provider_name == "gemini" and settings.GEMINI_API_KEY:
        return GeminiProvider(api_key=settings.GEMINI_API_KEY)
    elif provider_name == "groq" and settings.GROQ_API_KEY:
        return GroqProvider(api_key=settings.GROQ_API_KEY)
    elif settings.GEMINI_API_KEY:
        return GeminiProvider(api_key=settings.GEMINI_API_KEY)
    elif settings.GROQ_API_KEY:
        return GroqProvider(api_key=settings.GROQ_API_KEY)
    else:
        # Graceful fallback to deterministic evidence provider
        return DeterministicEvidenceProvider()
