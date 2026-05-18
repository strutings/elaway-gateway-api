"""Støtte for Elaway start og stopp knapper."""
from __future__ import annotations

import logging
import aiohttp
from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity import DeviceInfo

from .const import CONF_CHARGER_START_URL, CONF_CHARGER_STOP_URL, DOMENE

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Sett opp knappene."""
    session = async_get_clientsession(hass)
    
    start_url = entry.data[CONF_CHARGER_START_URL]
    stop_url = entry.data[CONF_CHARGER_STOP_URL]

    async_add_entities([
        ElawayButton(session, entry, "start", "Start Charging", start_url, "mdi:play"),
        ElawayButton(session, entry, "stop", "Stop Charging", stop_url, "mdi:stop"),
    ])


class ElawayButton(ButtonEntity):
    """Knapp for å sende kommandoer over HTTP."""

    def __init__(self, session: aiohttp.ClientSession, entry, key, name, url, icon):
        """Initialiser knappen."""
        self.session = session
        self.url = url
        self._attr_name = name
        self._attr_icon = icon
        self._attr_unique_id = f"{entry.entry_id}_button_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMENE, "elaway_charger_device")},
            name="Elaway EV Charger",
            manufacturer="Utviklet av Eirik Skorstad",
            model="Zaptec Charger Station",
        )

    async def async_press(self) -> None:
        """Sende HTTP POST når knappen trykkes i UI."""
        _LOGGER.info("Sender kommando til: %s", self.url)
        try:
            async with self.session.post(self.url) as response:
                if response.status == 200:
                    _LOGGER.info("Kommando utført suksessfullt (%s)", self.name)
                else:
                    _LOGGER.error("Feil ved utføring av kommando mot %s: %s", self.url, response.status)
        except Exception as err:
            _LOGGER.error("Krasj ved sending av kommando til %s: %s", self.url, err)
