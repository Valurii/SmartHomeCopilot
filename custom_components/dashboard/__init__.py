"""Simple API backend for the SmartHome Copilot dashboard card."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.components.http import HomeAssistantView

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
    """Dummy endpoint for accept/decline actions."""

    url = "/api/SmartHome_Copilot/{action}/{suggestion_id}"
    name = "SmartHomeCopilotAction"
    requires_auth = False

    async def post(self, request, action, suggestion_id):
        _LOGGER.debug("Received %s for suggestion %s", action, suggestion_id)
        return self.json({"success": True})
