"""Ollama provider implementation."""
from __future__ import annotations

import logging

from ..const import (
    CONF_OLLAMA_IP_ADDRESS,
    CONF_OLLAMA_PORT,
    CONF_OLLAMA_HTTPS,
    CONF_OLLAMA_MODEL,
    CONF_OLLAMA_TEMPERATURE,
    CONF_OLLAMA_DISABLE_THINK,
    DEFAULT_MODELS,
    DEFAULT_TEMPERATURE,
    ENDPOINT_OLLAMA,
)
from . import BaseProvider, register

_LOGGER = logging.getLogger(__name__)


@register
class OllamaProvider(BaseProvider):
    """Provider for Ollama deployments."""

    name = "Ollama"

    async def generate(self, prompt: str) -> str | None:
        try:
            ip = self._opt(CONF_OLLAMA_IP_ADDRESS)
            port = self._opt(CONF_OLLAMA_PORT)
            https = self._opt(CONF_OLLAMA_HTTPS, False)
            model = self._opt(CONF_OLLAMA_MODEL, DEFAULT_MODELS["Ollama"])
            temperature = self._opt(CONF_OLLAMA_TEMPERATURE, DEFAULT_TEMPERATURE)
            disable_think = self._opt(CONF_OLLAMA_DISABLE_THINK, False)
            in_budget, out_budget = self._budgets()
            if not ip or not port:
                raise ValueError("Ollama not fully configured")

            if len(prompt) // 4 > in_budget:
                prompt = prompt[: in_budget * 4]

            proto = "https" if https else "http"
            endpoint = ENDPOINT_OLLAMA.format(protocol=proto, ip_address=ip, port=port)

            messages = []
            if disable_think:
                messages.append({"role": "system", "content": "/no_think"})
            messages.append({"role": "user", "content": prompt})

            body = {
                "model": model,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": out_budget,
                },
            }
            async with self.session.post(endpoint, json=body) as resp:
                if resp.status != 200:
                    self.coordinator._last_error = (
                        f"Ollama error {resp.status}: {await resp.text()}"
                    )
                    _LOGGER.error(self.coordinator._last_error)
                    return None

                res = await resp.json()

            if not isinstance(res, dict):
                raise ValueError(f"Unexpected response format: {res}")

            if "message" not in res:
                raise ValueError(f"Response missing 'message' array: {res}")

            if "content" not in res["message"]:
                raise ValueError(f"Message missing 'content': {res['message']}")

            return res["message"]["content"]

        except Exception as err:
            self.coordinator._last_error = f"Ollama processing error: {str(err)}"
            _LOGGER.error(self.coordinator._last_error)
            _LOGGER.exception("Unexpected error in Ollama API call:")
            return None
