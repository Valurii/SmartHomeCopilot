"""Mistral AI provider implementation."""
from __future__ import annotations

import logging

from ..const import (
    CONF_MISTRAL_API_KEY,
    CONF_MISTRAL_MODEL,
    CONF_MISTRAL_TEMPERATURE,
    DEFAULT_MODELS,
    DEFAULT_TEMPERATURE,
    ENDPOINT_MISTRAL,
)
from . import BaseProvider, register

_LOGGER = logging.getLogger(__name__)


@register
class MistralProvider(BaseProvider):
    """Provider for Mistral AI."""

    name = "Mistral AI"

    async def generate(self, prompt: str) -> str | None:
        try:
            api_key = self._opt(CONF_MISTRAL_API_KEY)
            model = self._opt(CONF_MISTRAL_MODEL, DEFAULT_MODELS["Mistral AI"])
            temperature = self._opt(CONF_MISTRAL_TEMPERATURE, DEFAULT_TEMPERATURE)
            in_budget, out_budget = self._budgets()
            if not api_key:
                raise ValueError("Mistral API key not configured")

            if len(prompt) // 4 > in_budget:
                prompt = prompt[: in_budget * 4]

            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }
            body = {
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": temperature,
                "max_tokens": out_budget,
            }
            async with self.session.post(
                ENDPOINT_MISTRAL, headers=headers, json=body
            ) as resp:
                if resp.status != 200:
                    self.coordinator._last_error = (
                        f"Mistral error {resp.status}: {await resp.text()}"
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
            self.coordinator._last_error = f"Mistral processing error: {str(err)}"
            _LOGGER.error(self.coordinator._last_error)
            _LOGGER.exception("Unexpected error in Mistral API call:")
            return None
