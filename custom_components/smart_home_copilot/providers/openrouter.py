"""OpenRouter provider implementation."""
from __future__ import annotations

import logging

from ..const import (
    CONF_OPENROUTER_API_KEY,
    CONF_OPENROUTER_MODEL,
    CONF_OPENROUTER_REASONING_MAX_TOKENS,
    CONF_OPENROUTER_TEMPERATURE,
    DEFAULT_MODELS,
    DEFAULT_TEMPERATURE,
    ENDPOINT_OPENROUTER,
)
from . import BaseProvider, register

_LOGGER = logging.getLogger(__name__)


@register
class OpenRouterProvider(BaseProvider):
    """Provider for the OpenRouter API."""

    name = "OpenRouter"

    async def generate(self, prompt: str) -> str | None:
        try:
            api_key = self._opt(CONF_OPENROUTER_API_KEY)
            model = self._opt(CONF_OPENROUTER_MODEL, DEFAULT_MODELS["OpenRouter"])
            reasoning_max_tokens = self._opt(CONF_OPENROUTER_REASONING_MAX_TOKENS, 0)
            in_budget, out_budget = self._budgets()

            if not api_key:
                raise ValueError("OpenRouter API key not configured")

            if len(prompt) // 4 > in_budget:
                prompt = prompt[: in_budget * 4]

            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }
            body = {
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": out_budget,
                "temperature": self._opt(
                    CONF_OPENROUTER_TEMPERATURE, DEFAULT_TEMPERATURE
                ),
            }

            if reasoning_max_tokens > 0:
                body["reasoning"] = {"max_tokens": reasoning_max_tokens}

            async with self.session.post(
                ENDPOINT_OPENROUTER, headers=headers, json=body
            ) as resp:
                if resp.status != 200:
                    self.coordinator._last_error = (
                        f"OpenRouter error {resp.status}: {await resp.text()}"
                    )
                    _LOGGER.error(self.coordinator._last_error)
                    return None

                res = await resp.json()

            if not isinstance(res, dict):
                raise ValueError(f"Unexpected response format: {res}")

            if "choices" not in res:
                raise ValueError(f"Response missing 'choices' array: {res}")

            if not res["choices"] or not isinstance(res["choices"], list):
                raise ValueError(f"Empty or invalid 'choices' array: {res}")

            if "message" not in res["choices"][0]:
                raise ValueError(f"First choice missing 'message': {res['choices'][0]}")

            if "content" not in res["choices"][0]["message"]:
                raise ValueError(
                    f"Message missing 'content': {res['choices'][0]['message']}"
                )

            return res["choices"][0]["message"]["content"]

        except Exception as err:
            self.coordinator._last_error = f"OpenRouter processing error: {str(err)}"
            _LOGGER.error(self.coordinator._last_error)
            _LOGGER.exception("Unexpected error in OpenRouter API call:")
            return None
