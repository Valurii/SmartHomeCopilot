"""Custom OpenAI provider implementation."""
from __future__ import annotations

import logging

from ..const import (
    CONF_CUSTOM_OPENAI_ENDPOINT,
    CONF_CUSTOM_OPENAI_API_KEY,
    CONF_CUSTOM_OPENAI_MODEL,
    CONF_CUSTOM_OPENAI_TEMPERATURE,
    DEFAULT_MODELS,
    DEFAULT_TEMPERATURE,
)
from . import BaseProvider, register

_LOGGER = logging.getLogger(__name__)


@register
class CustomOpenAIProvider(BaseProvider):
    """Provider for custom OpenAI-compatible endpoints."""

    name = "Custom OpenAI"

    async def generate(self, prompt: str) -> str | None:
        try:
            endpoint = self._opt(CONF_CUSTOM_OPENAI_ENDPOINT) + "/v1/chat/completions"
            if not endpoint:
                raise ValueError("Custom OpenAI endpoint not configured")

            if not endpoint.endswith("/v1/chat/completions"):
                endpoint = endpoint.rstrip("/") + "/v1/chat/completions"

            api_key = self._opt(CONF_CUSTOM_OPENAI_API_KEY)
            model = self._opt(CONF_CUSTOM_OPENAI_MODEL, DEFAULT_MODELS["Custom OpenAI"])
            temperature = self._opt(CONF_CUSTOM_OPENAI_TEMPERATURE, DEFAULT_TEMPERATURE)
            in_budget, out_budget = self._budgets()

            if len(prompt) // 4 > in_budget:
                prompt = prompt[: in_budget * 4]

            headers = {"Content-Type": "application/json"}
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"

            body = {
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": out_budget,
                "temperature": temperature,
            }
            async with self.session.post(endpoint, headers=headers, json=body) as resp:
                if resp.status != 200:
                    self.coordinator._last_error = (
                        f"Custom OpenAI error {resp.status}: {await resp.text()}"
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
            self.coordinator._last_error = f"Custom OpenAI processing error: {str(err)}"
            _LOGGER.error(self.coordinator._last_error)
            _LOGGER.exception("Unexpected error in Custom OpenAI API call:")
            return None
