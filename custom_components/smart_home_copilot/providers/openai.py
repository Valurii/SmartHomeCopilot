"""OpenAI provider implementation."""
from __future__ import annotations

import logging

from aiohttp import ClientSession

from ..const import (
    CONF_OPENAI_API_KEY,
    CONF_OPENAI_MODEL,
    CONF_OPENAI_TEMPERATURE,
    DEFAULT_MODELS,
    DEFAULT_TEMPERATURE,
    ENDPOINT_OPENAI,
)
from . import BaseProvider, register

_LOGGER = logging.getLogger(__name__)


@register
class OpenAIProvider(BaseProvider):
    """Provider for OpenAI's API."""

    name = "OpenAI"

    async def generate(self, prompt: str) -> str | None:  # noqa: C901
        try:
            api_key = self._opt(CONF_OPENAI_API_KEY)
            model = self._opt(CONF_OPENAI_MODEL, DEFAULT_MODELS["OpenAI"])
            temperature = self._opt(CONF_OPENAI_TEMPERATURE, DEFAULT_TEMPERATURE)
            in_budget, out_budget = self._budgets()
            if not api_key:
                raise ValueError("OpenAI API key not configured")

            if len(prompt) // 4 > in_budget:
                prompt = prompt[: in_budget * 4]

            body = {
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": out_budget,
                "temperature": temperature,
            }
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }

            async with self.session.post(
                ENDPOINT_OPENAI, headers=headers, json=body
            ) as resp:
                if resp.status != 200:
                    self.coordinator._last_error = (
                        f"OpenAI error {resp.status}: {await resp.text()}"
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

        except Exception as err:  # noqa: BLE001
            self.coordinator._last_error = f"OpenAI processing error: {str(err)}"
            _LOGGER.error(self.coordinator._last_error)
            _LOGGER.exception("Unexpected error in OpenAI API call:")
            return None
