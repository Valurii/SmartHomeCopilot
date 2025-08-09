import sys
from pathlib import Path
from inspect import signature
from unittest.mock import patch
from zoneinfo import ZoneInfo

import pytest
from homeassistant.loader import DATA_CUSTOM_COMPONENTS as LOADER_CUSTOM
from pytest_homeassistant_custom_component.common import (
    async_test_home_assistant,
)

import threading

def teardown_module(module):
    for thread in threading.enumerate():
        if thread.name.startswith("Thread-3 (_run_safe_shutdown_loop)") and thread.is_alive():
            thread.join(timeout=1)

sys.path.append(str(Path(__file__).resolve().parents[1] / "custom_components"))

from smart_home_copilot.const import (
    CONF_OPENAI_API_KEY,
    CONF_OPENAI_MODEL,
    CONF_OPENAI_TEMPERATURE,
    CONF_MAX_INPUT_TOKENS,
    CONF_MAX_OUTPUT_TOKENS,
)
from smart_home_copilot.config_flow import AIAutomationConfigFlow, ProviderValidator


@pytest.mark.asyncio
async def test_config_flow_creates_entry(tmp_path):
    kwargs = {
        (
            "storage_dir"
            if "storage_dir" in signature(async_test_home_assistant).parameters
            else "config_dir"
        ): str(tmp_path)
    }
    with patch("homeassistant.util.dt.get_time_zone", return_value=ZoneInfo("UTC")):
        async with async_test_home_assistant(**kwargs) as hass:
            await hass.config.async_set_time_zone("UTC")
            hass.data.pop(LOADER_CUSTOM, None)
            flow = AIAutomationConfigFlow()
            flow.hass = hass
            with patch.object(ProviderValidator, "validate_openai", return_value=None):
                result = await flow.async_step_openai(
                    {
                        CONF_OPENAI_API_KEY: "fake",
                        CONF_OPENAI_MODEL: "gpt",
                        CONF_OPENAI_TEMPERATURE: 0.7,
                        CONF_MAX_INPUT_TOKENS: 100,
                        CONF_MAX_OUTPUT_TOKENS: 100,
                    }
                )
    assert result["type"] == "create_entry"
    await hass.async_stop(force=True)
    for thread in threading.enumerate():
        if thread.name.startswith("Thread-3 (_run_safe_shutdown_loop)") and thread.is_alive():
            thread.join(timeout=1)

