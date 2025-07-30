import sys
from pathlib import Path
from inspect import signature
from unittest.mock import patch
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
from custom_components.shc_dashboard import CopilotActionView


class DummyCoordinator:
    def __init__(self):
        self.data = {"suggestions": []}

    def async_set_updated_data(self, data):
        self.data = data

    async def _async_save_suggestions(self):
        # No-op for tests
        pass


@pytest.mark.asyncio
async def test_placeholder_replacement(tmp_path):
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
        coordinator = DummyCoordinator()
        hass.data[DOMAIN] = {entry.entry_id: coordinator}
        hass.states.async_set("light.kitchen_light", "on", {"friendly_name": "Kitchen"})
        hass.services.async_register("automation", "reload", lambda call: None)

        yaml_block = (
            "- id: '1'\n"
            "  alias: test\n"
            "  trigger:\n"
            "    - platform: state\n"
            "      entity_id: <<LIGHT_KITCHEN>>\n"
            "  action: []\n"
        )

        coordinator.data["suggestions"].append({
            "title": "t",
            "description": "d",
            "yaml": yaml_block,
        })

        view = CopilotActionView()
        req = type("Req", (), {"app": {"hass": hass}})()
        with patch("homeassistant.components.persistent_notification.async_create") as mock_notify:
            await view.post(req, "accept", "0")
            content = Path(tmp_path / "automations.yaml").read_text()
            assert "<<LIGHT_KITCHEN>>" not in content
            assert "light.kitchen_light" in content
            assert mock_notify.called

        await hass.async_stop(force=True)


@pytest.mark.asyncio
async def test_placeholder_decline(tmp_path):
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
        coordinator = DummyCoordinator()
        hass.data[DOMAIN] = {entry.entry_id: coordinator}
        hass.services.async_register("automation", "reload", lambda call: None)

        yaml_block = (
            "- id: '1'\n"
            "  alias: test\n"
            "  trigger: []\n"
            "  action: []\n"
        )

        coordinator.data["suggestions"].append({
            "title": "t",
            "description": "d",
            "yaml": yaml_block,
        })

        view = CopilotActionView()
        req = type("Req", (), {"app": {"hass": hass}})()
        await view.post(req, "decline", "0")
        assert coordinator.data["suggestions"] == []
        assert not Path(tmp_path / "automations.yaml").exists()
        await hass.async_stop(force=True)
