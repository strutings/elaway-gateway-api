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

async def validate_input(session: aiohttp.ClientSession, data: dict[str, Any]) -> dict[str, str]:
    """Validerer at vi i det minste får kontakt med URL-en."""
    errors: dict[str, str] = {}
    url = data[CONF_CHARGER_API_URL]

    if not url.startswith(("http://", "https://")):
        errors["base"] = "cannot_connect"
        _LOGGER.error("URL-en må starte med http:// eller https://")
        return errors

    try:
        # Vi gjør en kjapp sjekk med 10 sekunder timeout
        async with session.get(url, timeout=10) as resp:
            _LOGGER.debug("Elaway API svarte med statuskode: %s", resp.status)
            
            # Hvis du vet at API-et krever auth, kan du midlertidig godta 401/403 for å slippe forbi config flow
            if resp.status not in [200, 401, 403]:
                _LOGGER.error("API-et returnerte uventet statuskode: %s", resp.status)
                errors["base"] = "cannot_connect"
                return errors
                
    except aiohttp.ClientConnectorError as err:
        _LOGGER.error("Kunne ikke opprette tilkobling til %s: %s", url, err)
        errors["base"] = "cannot_connect"
    except asyncio.TimeoutError:
        _LOGGER.error("Tidsavbrudd (timeout) mot %s", url)
        errors["base"] = "cannot_connect"
    except Exception as err:  # pylint: disable=broad-except
        _LOGGER.exception("Uventet feil under validering av Elaway API: %s", err)
        errors["base"] = "cannot_connect"

    return errors


class ElawayChargerConfigFlow(config_entries.ConfigFlow, domain=DOMENE):
    """Håndterer config flow for Elaway EV Charger."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Håndterer det første steget når brukeren legger til integrasjonen."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Sikre at URL-ene ikke har unødvendige mellomrom
            user_input[CONF_CHARGER_API_URL] = user_input[CONF_CHARGER_API_URL].strip()
            user_input[CONF_CHARGER_START_URL] = user_input[CONF_CHARGER_START_URL].strip()
            user_input[CONF_CHARGER_STOP_URL] = user_input[CONF_CHARGER_STOP_URL].strip()

            await self.async_set_unique_id(user_input[CONF_CHARGER_API_URL])
            self._abort_if_unique_id_configured()

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
