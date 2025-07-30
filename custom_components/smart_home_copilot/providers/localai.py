"""LocalAI provider implementation."""
from __future__ import annotations

import logging

from ..const import (
    CONF_LOCALAI_IP_ADDRESS,
    CONF_LOCALAI_PORT,
    CONF_LOCALAI_HTTPS,
    CONF_LOCALAI_MODEL,
    CONF_LOCALAI_TEMPERATURE,
    DEFAULT_MODELS,
    DEFAULT_TEMPERATURE,
    ENDPOINT_LOCALAI,
)
from . import BaseProvider, register

_LOGGER = logging.getLogger(__name__)


@register
class LocalAIProvider(BaseProvider):
    """Provider for LocalAI deployments."""

    name = "LocalAI"

    async def generate(self, prompt: str) -> str | None:
        try:
            ip = self._opt(CONF_LOCALAI_IP_ADDRESS)
            port = self._opt(CONF_LOCALAI_PORT)
            https = self._opt(CONF_LOCALAI_HTTPS, False)
            model = self._opt(CONF_LOCALAI_MODEL, DEFAULT_MODELS["LocalAI"])
            temperature = self._opt(CONF_LOCALAI_TEMPERATURE, DEFAULT_TEMPERATURE)
            in_budget, out_budget = self._budgets()
            if not ip or not port:
                raise ValueError("LocalAI not fully configured")

            if len(prompt) // 4 > in_budget:
                prompt = prompt[: in_budget * 4]

            proto = "https" if https else "http"
            endpoint = ENDPOINT_LOCALAI.format(protocol=proto, ip_address=ip, port=port)

            body = {
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": out_budget,
                "temperature": temperature,
            }
            async with self.session.post(endpoint, json=body) as resp:
                if resp.status != 200:
                    self.coordinator._last_error = (
                        f"LocalAI error {resp.status}: {await resp.text()}"
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
            self.coordinator._last_error = f"LocalAI processing error: {str(err)}"
            _LOGGER.error(self.coordinator._last_error)
            _LOGGER.exception("Unexpected error in LocalAI API call:")
            return None
