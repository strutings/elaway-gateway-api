"""Elaway EV Charger integrasjon via HTTP API."""
from __future__ import annotations

import datetime
import logging
import async_timeout
import aiohttp

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import CONF_CHARGER_API_URL, DOMENE

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor", "binary_sensor", "button"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Sette opp integrasjonen fra en config entry."""
    session = async_get_clientsession(hass)
    
    coordinator = ElawayDataUpdateCoordinator(hass, session, entry.data[CONF_CHARGER_API_URL])
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMENE, {})
    hass.data[DOMENE][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Fjerne integrasjonen."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMENE].pop(entry.entry_id)
    return unload_ok


class ElawayDataUpdateCoordinator(DataUpdateCoordinator):
    """Klasse for å håndtere effektiv henting av API-data."""

    def __init__(self, hass: HomeAssistant, session: aiohttp.ClientSession, url: str):
        """Initialiser coordinator."""
        self.url = url
        self.session = session
        super().__init__(
            hass,
            _LOGGER,
            name="Elaway Charger API",
            update_interval=datetime.timedelta(seconds=60),
        )

    async def _async_update_data(self):
        """Hent data fra API-et."""
        try:
            async with async_timeout.timeout(10):
                async with self.session.get(self.url) as response:
                    if response.status != 200:
                        raise UpdateFailed(f"Ugyldig statuskode fra API: {response.status}")
                    return await response.json()
        except Exception as err:
            raise UpdateFailed(f"Kunne ikke kontakte Elaway API: {err}") from err
