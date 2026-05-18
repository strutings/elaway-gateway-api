"""Støtte for Elaway knapper (handlinger)."""
from __future__ import annotations

import logging
import aiohttp
from homeassistant.components.button import ButtonEntity, ButtonDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo

from .const import DOMENE

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Sett opp knapper basert på Elaway API-struktur."""
    # Knapper trenger API-klienten for å sende POST-kall, ikke koordinatoren
    api = hass.data[DOMENE][entry.entry_id]["api"]

    buttons = [
        ElawayActionButton(
            api, entry, "start_charging", "Start Charging", "mdi:play-circle", "remote-action/start"
        ),
        ElawayActionButton(
            api, entry, "stop_charging", "Stop Charging", "mdi:stop-circle", "remote-action/stop"
        ),
    ]
    
    async_add_entities(buttons)


class ElawayActionButton(ButtonEntity):
    """En knapp som trigger en handling mot Elaway API."""

    def __init__(self, api, entry, key, name, icon, api_endpoint):
        """Initialiser knappen."""
        self._api = api
        self._entry = entry
        self._api_endpoint = api_endpoint
        self._attr_name = name
        self._attr_icon = icon
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMENE, "elaway_charger_device")},
            name="Elaway EV Charger",
            manufacturer="Utviklet av Eirik Skorstad",
            model="Zaptec Charger Station",
        )

    async def async_press(self) -> None:
        """Kjøres når brukeren trykker på knappen i Home Assistant."""
        _LOGGER.info(f"Trigger handling: {self._attr_name}")
        
        try:
            # 1. Hent gyldig token
            token = await self._api.async_get_valid_credentials()
            
            # 2. Send kommandoen direkte til Elaway/Ampeco
            # (Bytt ut URL-en under med det nøyaktige endepunktet Ampeco bruker for kommandoer)
            url = f"{self._api.ampeco_api_url}/v1/user/chargers/{self._api_endpoint}"
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            async with aiohttp.ClientSession() as session:
                # Ampeco krever ofte en tom JSON-body eller ID i post-kallet
                async with session.post(url, headers=headers, json={}) as response:
                    if response.status in [200, 201, 204]:
                        _LOGGER.info(f"Handling '{self._attr_name}' utført med suksess!")
                    else:
                        _LOGGER.error(f"Klarte ikke å utføre handling. Status: {response.status}")
                        
        except Exception as err:
            _LOGGER.error(f"Feil under trykk på knapp {self._attr_name}: {err}")
