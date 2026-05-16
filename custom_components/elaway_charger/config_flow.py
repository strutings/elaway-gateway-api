"""Config flow for Elaway EV Charger."""
from __future__ import annotations

import logging
from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import CONF_CHARGER_API_URL, CONF_CHARGER_START_URL, CONF_CHARGER_STOP_URL, DOMENE

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_CHARGER_API_URL): str,
        vol.Required(CONF_CHARGER_START_URL): str,
        vol.Required(CONF_CHARGER_STOP_URL): str,
    }
)

async def validate_input(session: aiohttp.ClientSession, data: dict[str, Any]) -> dict[str, Any]:
    """Validerer at API-URL-en faktisk fungerer og svarer."""
    try:
        async with session.get(data[CONF_CHARGER_API_URL], timeout=10) as resp:
            if resp.status != 200:
                return {"base": "cannot_connect"}
            # Sjekk om det er gyldig JSON og har riktig struktur
            json_data = await resp.json()
            if "data" not in json_data or "evses" not in json_data["data"]:
                return {"base": "invalid_auth"}  # Eller ugyldig datarespons
    except Exception:  # pylint: disable=broad-except
        _LOGGER.exception("Feil under validering av Elaway API")
        return {"base": "cannot_connect"}

    return {}


class ElawayChargerConfigFlow(config_entries.ConfigFlow, domain=DOMENE):
    """Håndterer config flow for Elaway EV Charger."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Håndterer det første steget når brukeren legger til integrasjonen."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Sjekk om integrasjonen allerede er satt opp (hindre duplikater)
            await self.async_set_unique_id(user_input[CONF_CHARGER_API_URL])
            self._abort_if_unique_id_configured()

            # Valider URL-ene
            session = async_get_clientsession(self.hass)
            errors = await validate_input(session, user_input)

            if not errors:
                return self.async_create_entry(
                    title="Elaway EV Charger",
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )
