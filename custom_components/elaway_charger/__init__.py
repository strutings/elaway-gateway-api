"""Elaway EV Charger integration for Home Assistant."""
from __future__ import annotations

import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .elaway_charger import ElawayChargerIntegration

_LOGGER = logging.getLogger(__name__)
DOMAIN = "elaway_charger"


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Elaway charger integration."""
    charger_api_url = entry.data.get("charger_api_url")
    charger_start_url = entry.data.get("charger_start_url")
    charger_stop_url = entry.data.get("charger_stop_url")
    
    integration = ElawayChargerIntegration(
        hass,
        charger_api_url,
        charger_start_url,
        charger_stop_url
    )
    
    success = await integration.async_setup()
    if success:
        hass.data.setdefault(DOMAIN, {})
        hass.data[DOMAIN][entry.entry_id] = integration
    
    return success


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload Elaway charger integration."""
    if entry.entry_id in hass.data.get(DOMAIN, {}):
        await hass.data[DOMAIN][entry.entry_id].async_unload()
        del hass.data[DOMAIN][entry.entry_id]
    return True
