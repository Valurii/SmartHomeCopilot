"""Google provider implementation."""
from __future__ import annotations

import logging
import aiohttp

from ..const import (
    CONF_GOOGLE_API_KEY,
    CONF_GOOGLE_MODEL,
    CONF_GOOGLE_TEMPERATURE,
    DEFAULT_MODELS,
    DEFAULT_TEMPERATURE,
)
from . import BaseProvider, register

_LOGGER = logging.getLogger(__name__)


@register
class GoogleProvider(BaseProvider):
    """Provider for Google's generative language API."""

    name = "Google"

    async def generate(self, prompt: str) -> str | None:
        try:
            api_key = self._opt(CONF_GOOGLE_API_KEY)
            model = self._opt(CONF_GOOGLE_MODEL, DEFAULT_MODELS["Google"])
            in_budget, out_budget = self._budgets()
            temperature = self._opt(CONF_GOOGLE_TEMPERATURE, DEFAULT_TEMPERATURE)
            if not api_key:
                raise ValueError("Google API key not configured")

            if len(prompt) // 4 > in_budget:
                prompt = prompt[: in_budget * 4]

            body = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "temperature": temperature,
                    "maxOutputTokens": out_budget,
                    "topK": 40,
                    "topP": 0.95,
                },
            }
            endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
            timeout = aiohttp.ClientTimeout(total=900)

            async with self.session.post(endpoint, json=body, timeout=timeout) as resp:
                if resp.status != 200:
                    self.coordinator._last_error = (
                        f"Google error {resp.status}: {await resp.text()}"
                    )
                    _LOGGER.error(self.coordinator._last_error)
                    return None

                res = await resp.json()

            if not isinstance(res, dict):
                raise ValueError(f"Unexpected response format: {res}")

            if "candidates" not in res:
                raise ValueError(f"Response missing 'candidates' array: {res}")

            if not res["candidates"] or not isinstance(res["candidates"], list):
                raise ValueError(f"Empty or invalid 'candidates' array: {res}")

            if "content" not in res["candidates"][0]:
                raise ValueError(
                    f"First choice missing 'content': {res['candidates'][0]}"
                )

            if "parts" not in res["candidates"][0]["content"]:
                raise ValueError(
                    f"content missing 'parts': {res['candidates'][0]['message']}"
                )

            if not res["candidates"][0]["content"]["parts"] or not isinstance(
                res["candidates"][0]["content"]["parts"], list
            ):
                raise ValueError(
                    f"Empty or invalid 'parts' array: {res['candidates'][0]['content']}"
                )

            if "text" not in res["candidates"][0]["content"]["parts"][0]:
                raise ValueError(
                    f"parts missing 'text': {res['candidates'][0]['content']['parts']}"
                )

            return res["candidates"][0]["content"]["parts"][0]["text"]

        except Exception as err:
            self.coordinator._last_error = f"Google processing error: {str(err)}"
            _LOGGER.error(self.coordinator._last_error)
            _LOGGER.exception("Unexpected error in Google API call:")
            return None
