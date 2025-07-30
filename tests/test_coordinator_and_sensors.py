import sys
from pathlib import Path

# Add the custom_components directory to the path so the integration can be
# imported directly as ``SmartHomeCopilot`` in tests.
sys.path.append(str(Path(__file__).resolve().parents[1] / "custom_components"))

from datetime import datetime
from unittest.mock import patch
from zoneinfo import ZoneInfo

import pytest
from homeassistant.loader import DATA_CUSTOM_COMPONENTS as LOADER_CUSTOM
from inspect import signature
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_test_home_assistant,
)

from smart_home_copilot.const import (
    DOMAIN,
    CONF_PROVIDER,
    CONFIG_VERSION,
    CONF_MAX_INPUT_TOKENS,
    CONF_MAX_OUTPUT_TOKENS,
    CONF_MAX_TOKENS,
    CONF_OPENAI_MODEL,
    PROVIDER_STATUS_CONNECTED,
    PROVIDER_STATUS_ERROR,
    SENSOR_KEY_SUGGESTIONS,
    SENSOR_KEY_STATUS,
    SENSOR_KEY_INPUT_TOKENS,
    SENSOR_KEY_OUTPUT_TOKENS,
    SENSOR_KEY_MODEL,
    SENSOR_KEY_LAST_ERROR,
)
from smart_home_copilot.coordinator import AIAutomationCoordinator
from smart_home_copilot.sensor import (
    SENSOR_DESCRIPTIONS,
    AISuggestionsSensor,
    AIProviderStatusSensor,
    MaxInputTokensSensor,
    MaxOutputTokensSensor,
    AIModelSensor,
    AILastErrorSensor,
)


@pytest.mark.asyncio
async def test_coordinator_budgets():
    repo_root = Path(__file__).resolve().parents[1]
    kwargs = {
        (
            "storage_dir"
            if "storage_dir" in signature(async_test_home_assistant).parameters
            else "config_dir"
        ): str(repo_root)
    }
    with patch("homeassistant.util.dt.get_time_zone", return_value=ZoneInfo("UTC")):
        async with async_test_home_assistant(**kwargs) as hass:
            await hass.config.async_set_time_zone("UTC")
            hass.data.pop(LOADER_CUSTOM, None)
            entry = MockConfigEntry(
                domain=DOMAIN,
                title="Test",
                data={
                    CONF_PROVIDER: "OpenAI",
                    CONF_MAX_TOKENS: 50,
                },
                options={
                    CONF_MAX_INPUT_TOKENS: 100,
                    CONF_MAX_OUTPUT_TOKENS: 200,
                },
                version=CONFIG_VERSION,
            )
        entry.add_to_hass(hass)
        coordinator = AIAutomationCoordinator(hass, entry)
        assert coordinator._budgets() == (100, 200)

        entry2 = MockConfigEntry(
            domain=DOMAIN,
            title="Test",
            data={
                CONF_PROVIDER: "OpenAI",
                CONF_MAX_TOKENS: 30,
            },
            options={},
            version=CONFIG_VERSION,
        )
        entry2.add_to_hass(hass)
        coordinator2 = AIAutomationCoordinator(hass, entry2)
        assert coordinator2._budgets() == (30, 30)
        await hass.async_stop(force=True)


@pytest.mark.asyncio
async def test_sensor_updates():
    repo_root = Path(__file__).resolve().parents[1]
    kwargs = {
        (
            "storage_dir"
            if "storage_dir" in signature(async_test_home_assistant).parameters
            else "config_dir"
        ): str(repo_root)
    }
    with patch("homeassistant.util.dt.get_time_zone", return_value=ZoneInfo("UTC")):
        async with async_test_home_assistant(**kwargs) as hass:
            await hass.config.async_set_time_zone("UTC")
            hass.data.pop(LOADER_CUSTOM, None)
            entry = MockConfigEntry(
                domain=DOMAIN,
                title="Test",
                data={CONF_PROVIDER: "OpenAI", CONF_OPENAI_MODEL: "model-a"},
                options={},
                version=CONFIG_VERSION,
            )
        entry.add_to_hass(hass)
        coordinator = AIAutomationCoordinator(hass, entry)
        # Initialize sensors
        desc_map = {d.key: d for d in SENSOR_DESCRIPTIONS}
        sugg = AISuggestionsSensor(coordinator, entry, desc_map[SENSOR_KEY_SUGGESTIONS])
        status = AIProviderStatusSensor(coordinator, entry, desc_map[SENSOR_KEY_STATUS])
        in_tok = MaxInputTokensSensor(
            coordinator, entry, desc_map[SENSOR_KEY_INPUT_TOKENS]
        )
        out_tok = MaxOutputTokensSensor(
            coordinator, entry, desc_map[SENSOR_KEY_OUTPUT_TOKENS]
        )
        model = AIModelSensor(coordinator, entry, desc_map[SENSOR_KEY_MODEL])
        err = AILastErrorSensor(coordinator, entry, desc_map[SENSOR_KEY_LAST_ERROR])

        assert status.native_value == PROVIDER_STATUS_CONNECTED
        assert sugg.native_value == "No Suggestions"
        assert in_tok.native_value == entry.options.get(
            CONF_MAX_INPUT_TOKENS,
            entry.data.get(CONF_MAX_INPUT_TOKENS, 500),
        )
        assert out_tok.native_value == entry.options.get(
            CONF_MAX_OUTPUT_TOKENS,
            entry.data.get(CONF_MAX_OUTPUT_TOKENS, 500),
        )
        assert model.native_value == "model-a"
        assert err.native_value == "No Error"

        now = datetime.now()
        new_data = {
            "suggestions": [
                {"title": "t", "description": "desc", "yaml": "yaml", "provider": "OpenAI"}
            ],
            "last_update": now,
            "entities_processed": ["sensor.test"],
            "provider": "OpenAI",
            "last_error": None,
        }
        coordinator.data = new_data
        sugg._update_state_and_attributes()
        status._update_state_and_attributes()
        err._update_state_and_attributes()

        assert sugg.native_value == "New Suggestions Available"
        assert sugg.extra_state_attributes["entities_processed_count"] == 1
        assert sugg.extra_state_attributes["suggestions"] == new_data["suggestions"]
        assert status.native_value == PROVIDER_STATUS_CONNECTED
        assert err.native_value == "No Error"

        # Simulate error
        new_data["last_error"] = "boom"
        coordinator.data = new_data
        err._update_state_and_attributes()
        status._update_state_and_attributes()
        assert err.native_value == "boom"
        assert status.native_value == PROVIDER_STATUS_ERROR
        await hass.async_stop(force=True)
