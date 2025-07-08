import sys
from pathlib import Path

# Add the custom_components directory to the path so we can import the
# integration directly as ``SmartHomeCopilot`` during tests.
sys.path.append(
    str(Path(__file__).resolve().parents[1] / "custom_components")
)

import pytest
from unittest.mock import patch
from zoneinfo import ZoneInfo
from homeassistant.config_entries import ConfigEntryState
from homeassistant.loader import DATA_CUSTOM_COMPONENTS as LOADER_CUSTOM
from inspect import signature
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_test_home_assistant,
)

from SmartHomeCopilot.const import (
    DOMAIN,
    CONF_PROVIDER,
    CONFIG_VERSION,
)


@pytest.mark.parametrize("expected_lingering_timers", [True])
@pytest.mark.asyncio
async def test_async_setup_entry(expected_lingering_timers):
    """Test that the integration loads and creates sensors."""
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
            with patch("homeassistant.core_config.report_usage"):
                hass.config.set_time_zone("UTC")
            hass.data.pop(LOADER_CUSTOM, None)
            entry = MockConfigEntry(
                domain=DOMAIN,
                title="Test",
                data={CONF_PROVIDER: "OpenAI"},
                options={},
                version=CONFIG_VERSION,
            )
            entry.add_to_hass(hass)

        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        assert entry.state == ConfigEntryState.LOADED
        sensor_entities = [
            eid for eid in hass.states.async_entity_ids() if eid.startswith("sensor.")
        ]
        assert sensor_entities
        await hass.async_stop(force=True)
