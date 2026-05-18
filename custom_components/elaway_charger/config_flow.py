"""Config flow for Elaway EV Charger."""
from __future__ import annotations

from typing import Any
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult

from .const import CONF_CHARGER_API_URL, CONF_CHARGER_START_URL, CONF_CHARGER_STOP_URL, DOMENE


class ElawayChargerConfigFlow(config_entries.ConfigFlow, domain=DOMENE):
    """Håndterer config flow."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Første steg i oppsettet."""
        if user_input is not None:
            return self.async_create_entry(
                title="Elaway EV Charger",
                data=user_input,
            )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_CHARGER_API_URL, default="http://10.0.0.186:4000/charger"): str,
                    vol.Required(CONF_CHARGER_START_URL, default="http://10.0.0.186:4000/charger/start"): str,
                    vol.Required(CONF_CHARGER_STOP_URL, default="http://10.0.0.186:4000/charger/stop"): str,
                }
            )
        )
