"""Anthropic provider implementation."""
from __future__ import annotations

import logging

from ..const import (
    CONF_ANTHROPIC_API_KEY,
    CONF_ANTHROPIC_MODEL,
    CONF_ANTHROPIC_TEMPERATURE,
    DEFAULT_MODELS,
    DEFAULT_TEMPERATURE,
    ENDPOINT_ANTHROPIC,
    VERSION_ANTHROPIC,
)
from . import BaseProvider, register

_LOGGER = logging.getLogger(__name__)


@register
class AnthropicProvider(BaseProvider):
    """Provider for Anthropic's Claude models."""

    name = "Anthropic"

    async def generate(self, prompt: str) -> str | None:
        try:
            api_key = self._opt(CONF_ANTHROPIC_API_KEY)
            model = self._opt(CONF_ANTHROPIC_MODEL, DEFAULT_MODELS["Anthropic"])
            in_budget, out_budget = self._budgets()
            temperature = self._opt(CONF_ANTHROPIC_TEMPERATURE, DEFAULT_TEMPERATURE)
            if not api_key:
                raise ValueError("Anthropic API key not configured")

            if len(prompt) // 4 > in_budget:
                prompt = prompt[: in_budget * 4]

            headers = {
                "X-API-Key": api_key,
                "Content-Type": "application/json",
                "anthropic-version": VERSION_ANTHROPIC,
            }
            body = {
                "model": model,
                "messages": [
                    {"role": "user", "content": [{"type": "text", "text": prompt}]}
                ],
                "max_tokens": out_budget,
                "temperature": temperature,
            }

            async with self.session.post(
                ENDPOINT_ANTHROPIC, headers=headers, json=body
            ) as resp:
                if resp.status != 200:
                    self.coordinator._last_error = (
                        f"Anthropic error {resp.status}: {await resp.text()}"
                    )
                    _LOGGER.error(self.coordinator._last_error)
                    return None

                res = await resp.json()

            if not isinstance(res, dict):
                raise ValueError(f"Unexpected response format: {res}")

            if "content" not in res:
                raise ValueError(f"Response missing 'content' array: {res}")

            if not res["content"] or not isinstance(res["content"], list):
                raise ValueError(f"Empty or invalid 'content' array: {res}")

            if "text" not in res["content"][0]:
                raise ValueError(f"First choice missing 'text': {res['content'][0]}")

            return res["content"][0]["text"]

        except Exception as err:
            self.coordinator._last_error = f"Anthropic processing error: {str(err)}"
            _LOGGER.error(self.coordinator._last_error)
            _LOGGER.exception("Unexpected error in Anthropic API call:")
            return None
