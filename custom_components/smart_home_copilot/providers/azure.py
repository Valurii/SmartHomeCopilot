"""OpenAI Azure provider implementation."""
from __future__ import annotations

import logging

from ..const import (
    CONF_OPENAI_AZURE_API_KEY,
    CONF_OPENAI_AZURE_DEPLOYMENT_ID,
    CONF_OPENAI_AZURE_API_VERSION,
    CONF_OPENAI_AZURE_ENDPOINT,
    CONF_OPENAI_AZURE_TEMPERATURE,
    DEFAULT_TEMPERATURE,
)
from . import BaseProvider, register

_LOGGER = logging.getLogger(__name__)


@register
class OpenAIAzureProvider(BaseProvider):
    """Provider for Azure-hosted OpenAI."""

    name = "OpenAI Azure"

    async def generate(self, prompt: str) -> str | None:
        try:
            endpoint_base = self._opt(CONF_OPENAI_AZURE_ENDPOINT)
            api_key = self._opt(CONF_OPENAI_AZURE_API_KEY)
            deployment_id = self._opt(CONF_OPENAI_AZURE_DEPLOYMENT_ID)
            api_version = self._opt(CONF_OPENAI_AZURE_API_VERSION, "2025-01-01-preview")
            in_budget, out_budget = self._budgets()
            temperature = self._opt(CONF_OPENAI_AZURE_TEMPERATURE, DEFAULT_TEMPERATURE)

            if not endpoint_base or not deployment_id or not api_version or not api_key:
                raise ValueError(
                    "OpenAI Azure endpoint, deployment, api version or API key not configured"
                )

            if len(prompt) // 4 > in_budget:
                prompt = prompt[: in_budget * 4]

            endpoint = f"https://{endpoint_base}/openai/deployments/{deployment_id}/chat/completions?api-version={api_version}"

            headers = {
                "api-key": api_key,
                "Content-Type": "application/json",
            }
            body = {
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": out_budget,
                "temperature": temperature,
            }

            async with self.session.post(endpoint, headers=headers, json=body) as resp:
                if resp.status != 200:
                    self.coordinator._last_error = (
                        f"OpenAI Azure error {resp.status}: {await resp.text()}"
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
            self.coordinator._last_error = f"OpenAI Azure processing error: {str(err)}"
            _LOGGER.error(self.coordinator._last_error)
            _LOGGER.exception("Unexpected error in OpenAI Azure API call:")
            return None
