"""Perplexity AI provider implementation."""
from __future__ import annotations

import logging

from ..const import (
    CONF_PERPLEXITY_API_KEY,
    CONF_PERPLEXITY_MODEL,
    CONF_PERPLEXITY_TEMPERATURE,
    DEFAULT_MODELS,
    DEFAULT_TEMPERATURE,
    ENDPOINT_PERPLEXITY,
)
from . import BaseProvider, register

_LOGGER = logging.getLogger(__name__)


@register
class PerplexityProvider(BaseProvider):
    """Provider for Perplexity AI."""

    name = "Perplexity AI"

    async def generate(self, prompt: str) -> str | None:
        try:
            api_key = self._opt(CONF_PERPLEXITY_API_KEY)
            model = self._opt(CONF_PERPLEXITY_MODEL, DEFAULT_MODELS["Perplexity AI"])
            temperature = self._opt(CONF_PERPLEXITY_TEMPERATURE, DEFAULT_TEMPERATURE)
            in_budget, out_budget = self._budgets()
            if not api_key:
                raise ValueError("Perplexity API key not configured")

            if len(prompt) // 4 > in_budget:
                prompt = prompt[: in_budget * 4]

            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            }
            body = {
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": out_budget,
                "temperature": temperature,
            }
            async with self.session.post(
                ENDPOINT_PERPLEXITY, headers=headers, json=body
            ) as resp:
                if resp.status != 200:
                    self.coordinator._last_error = (
                        f"Perplexity error {resp.status}: {await resp.text()}"
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
            self.coordinator._last_error = f"Perplexity processing error: {str(err)}"
            _LOGGER.error(self.coordinator._last_error)
            _LOGGER.exception("Unexpected error in Perplexity API call:")
            return None
