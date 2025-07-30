import sys
from pathlib import Path
from types import SimpleNamespace
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
from smart_home_copilot.coordinator import AIAutomationCoordinator, YAML_RE
from custom_components.shc_dashboard import CopilotActionView


@pytest.mark.asyncio
async def test_build_prompt_contains_entity(tmp_path):
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
        coordinator = AIAutomationCoordinator(hass, entry)
        coordinator.entity_registry = None
        coordinator.device_registry = None
        coordinator.area_registry = None

        entities = {
            "light.test_light": {
                "friendly_name": "Test Light",
                "state": "on",
                "attributes": {"friendly_name": "Test Light"},
                "last_changed": "now",
                "last_updated": "now",
            }
        }

        prompt = await coordinator._build_prompt(entities)
        assert "light.test_light" in prompt
        assert "on" in prompt
        await hass.async_stop(force=True)


def test_yaml_regex_extraction():
    text = "Some text\n```yaml\n- id: '1'\n  alias: test\n```\nmore"
    matches = YAML_RE.findall(text)
    assert len(matches) == 1
    assert "alias: test" in matches[0]


@pytest.mark.asyncio
async def test_accept_logic_writes_file(tmp_path):
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
        coordinator = AIAutomationCoordinator(hass, entry)
        hass.data[DOMAIN] = {entry.entry_id: coordinator}
        hass.services.async_register("automation", "reload", lambda call: None)

        coordinator.data = {
            "suggestions": [
                {
                    "title": "t",
                    "description": "desc",
                    "yaml": "- id: 'a'\n  alias: t\n  trigger: []\n  action: []\n",
                    "provider": "OpenAI",
                }
            ]
        }

        view = CopilotActionView()
        req = SimpleNamespace(app={"hass": hass})
        await view.post(req, "accept", "0")
        assert coordinator.data["suggestions"] == []
        content = Path(tmp_path / "automations.yaml").read_text()
        assert "alias: t" in content
        await hass.async_stop(force=True)
