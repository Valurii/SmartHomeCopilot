"""Simple API backend for the SmartHome Copilot dashboard card."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.components.http import HomeAssistantView
from homeassistant.components import persistent_notification
import yaml
from pathlib import Path
import re

from ..SmartHomeCopilot.const import DOMAIN as COPILOT_DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: dict[str, Any]) -> bool:
    """Register API views used by the dashboard."""
    hass.http.register_view(CopilotSuggestionsView)
    hass.http.register_view(CopilotActionView)
    return True


class CopilotSuggestionsView(HomeAssistantView):
    """Expose generated suggestions via REST."""

    url = "/api/SmartHome_Copilot/suggestions"
    name = "SmartHomeCopilotSuggestions"
    requires_auth = False

    async def get(self, request):
        hass = request.app["hass"]
        suggestions = []
        for coordinator in hass.data.get(COPILOT_DOMAIN, {}).values():
            data = getattr(coordinator, "data", {})
            if data.get("yaml_block"):
                suggestions.append(
                    {
                        "id": 0,
                        "title": "Automation Suggestion",
                        "shortDescription": data.get("description"),
                        "detailedDescription": data.get("description"),
                        "yamlCode": data.get("yaml_block"),
                        "showDetails": False,
                    }
                )
        return self.json(suggestions)


class CopilotActionView(HomeAssistantView):
    """Handle accept/decline actions for suggestions."""

    url = "/api/SmartHome_Copilot/{action}/{suggestion_id}"
    name = "SmartHomeCopilotAction"
    requires_auth = False

    async def post(self, request, action, suggestion_id):
        hass: HomeAssistant = request.app["hass"]
        coordinator = next(iter(hass.data.get(COPILOT_DOMAIN, {}).values()), None)
        if coordinator is None:
            return self.json({"success": False, "error": "No coordinator"})

        data = getattr(coordinator, "data", {})
        yaml_block = data.get("yaml_block")
        if action == "accept" and yaml_block:
            placeholders = re.findall(r"<<([^>]+)>>", yaml_block)
            replaced = {}
            for ph in placeholders:
                domain = ph.lower().split("_")[0]
                entities = hass.states.async_entity_ids(domain)
                if entities:
                    replacement = entities[0]
                    yaml_block = yaml_block.replace(f"<<{ph}>>", replacement)
                    replaced[ph] = replacement
            try:
                yaml.safe_load(yaml_block)
            except yaml.YAMLError as err:
                _LOGGER.error("Failed to parse YAML: %s", err)
                return self.json({"success": False, "error": "Invalid YAML"})

            if placeholders:
                msg_lines = [
                    "Placeholder mappings:",
                    *[f"{p} -> {replaced.get(p, 'unresolved')}" for p in placeholders],
                    "Please review the automation and adjust if needed.",
                ]
                persistent_notification.async_create(
                    hass,
                    "\n".join(msg_lines),
                    title="SmartHome Copilot Placeholder Mapping",
                    notification_id=f"ai_copilot_placeholder_{suggestion_id}",
                )

            file_path = Path(hass.config.path("automations.yaml"))
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, "a", encoding="utf-8") as f:
                if file_path.stat().st_size:
                    f.write("\n")
                f.write(yaml_block.rstrip() + "\n")

            await hass.services.async_call(
                "automation", "reload", blocking=True
            )
            _LOGGER.info("Suggestion %s accepted and automation reloaded", suggestion_id)
        elif action == "decline":
            _LOGGER.info("Suggestion %s declined", suggestion_id)

        # Mark suggestion as handled
        coordinator.data.update(
            {
                "suggestions": "No suggestions available",
                "description": None,
                "yaml_block": None,
                "entities_processed": [],
            }
        )
        coordinator.async_set_updated_data(coordinator.data)

        return self.json({"success": True})
