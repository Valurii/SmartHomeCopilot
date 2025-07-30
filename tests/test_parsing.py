import sys
from pathlib import Path
from unittest.mock import patch
from inspect import signature
from zoneinfo import ZoneInfo

import pytest
from homeassistant.loader import DATA_CUSTOM_COMPONENTS as LOADER_CUSTOM
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_test_home_assistant,
)

repo_root = Path(__file__).resolve().parents[1]
sys.path.append(str(repo_root))
sys.path.append(str(repo_root / "custom_components"))

from smart_home_copilot.const import DOMAIN, CONF_PROVIDER, CONFIG_VERSION
from smart_home_copilot.coordinator import AIAutomationCoordinator


@pytest.mark.asyncio
async def test_async_update_parses_yaml_blocks(tmp_path):
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
            entry = MockConfigEntry(
                domain=DOMAIN,
                title="Test",
                data={CONF_PROVIDER: "OpenAI"},
                options={},
                version=CONFIG_VERSION,
            )
        entry.add_to_hass(hass)
        hass.states.async_set("light.test_light", "on", {"friendly_name": "Test"})
        coordinator = AIAutomationCoordinator(hass, entry)
        coordinator.previous_entities = {}

        response = (
            "First suggestion:\n"
            "```yaml\n- id: '1'\n  alias: first\n  trigger: []\n  action: []\n```\n"
            "Second suggestion:\n"
            "```yaml\n- id: '2'\n  alias: second\n  trigger: []\n  action: []\n```\n"
        )

        with patch.object(coordinator, "_build_prompt", return_value="ignored"), patch.object(
            coordinator,
            "_dispatch",
            return_value=response,
        ), patch("homeassistant.components.persistent_notification.async_create") as mock_notify:
            data = await coordinator._async_update_data()

        assert len(data["suggestions"]) == 2
        assert data["suggestions"][0]["description"].startswith("First suggestion")
        assert "alias: first" in data["suggestions"][0]["yaml"]
        assert data["suggestions"][1]["description"].startswith("Second suggestion")
        assert "alias: second" in data["suggestions"][1]["yaml"]
        assert mock_notify.called
        await hass.async_stop(force=True)
