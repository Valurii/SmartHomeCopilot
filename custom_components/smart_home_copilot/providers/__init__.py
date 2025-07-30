"""Provider implementations for Smart Home Copilot."""
from __future__ import annotations

from typing import TYPE_CHECKING, Callable, Dict, Type

if TYPE_CHECKING:  # pragma: no cover
    from ..coordinator import AIAutomationCoordinator


class BaseProvider:
    """Base class for AI providers."""

    name: str = "base"

    def __init__(self, coordinator: "AIAutomationCoordinator") -> None:
        self.coordinator = coordinator
        self.session = coordinator.session
        self._opt = coordinator._opt
        self._budgets = coordinator._budgets

    async def generate(self, prompt: str) -> str | None:
        raise NotImplementedError


PROVIDERS: Dict[str, Type[BaseProvider]] = {}


def register(cls: Type[BaseProvider]) -> Type[BaseProvider]:
    """Class decorator to register providers by name."""
    PROVIDERS[cls.name] = cls
    return cls

# Import provider implementations so they register themselves
from .openai import OpenAIProvider
from .azure import OpenAIAzureProvider
from .anthropic import AnthropicProvider
from .google import GoogleProvider
from .groq import GroqProvider
from .localai import LocalAIProvider
from .ollama import OllamaProvider
from .custom_openai import CustomOpenAIProvider
from .mistral import MistralProvider
from .perplexity import PerplexityProvider
from .openrouter import OpenRouterProvider

__all__ = [
    "BaseProvider",
    "PROVIDERS",
    "OpenAIProvider",
    "OpenAIAzureProvider",
    "AnthropicProvider",
    "GoogleProvider",
    "GroqProvider",
    "LocalAIProvider",
    "OllamaProvider",
    "CustomOpenAIProvider",
    "MistralProvider",
    "PerplexityProvider",
    "OpenRouterProvider",
]
