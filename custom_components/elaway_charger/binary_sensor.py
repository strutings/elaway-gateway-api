"""Støtte for Elaway binærsensorer (Av/På)."""
from __future__ import annotations

import logging
from homeassistant.components.binary_sensor import BinarySensorEntity, BinarySensorDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMENE

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Sett opp binærsensorer basert på koordinatoren."""
    # Hent koordinatoren fra den sentrale lagringen i __init__.py
    coordinator = hass.data[DOMENE][entry.entry_id]["coordinator"]

#async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
#    """Sett opp binærsensorer basert på koordinatoren."""
#    api = hass.data[DOMENE][entry.entry_id]
    
    # Finn koordinatoren som ble opprettet i sensor.py (eller lagret i hass.data i __init__.py)
    # For enkelhets skyld antar vi her at sensorene deler samme data.
    # Hvis du flyttet koordinatoren til __init__.py, henter du den derfra.
    
    # Siden koordinatoren foreløpig lages i sensor.py, er det best å flytte 
    # selve DataUpdateCoordinator-oppsettet til __init__.py etter hvert.
    # Men her er strukturen for hvordan binærsensoren henter data:
    
    binary_sensors = [
        ElawayBinarySensor(
            coordinator, entry, "cable_connected", "Cable Connected", BinarySensorDeviceClass.PLUG,
            lambda d: d['data']['evses'][0]['session']['isCableConnected']
        ),

#    binary_sensors = [
#        ElawayBinarySensor(
#            None, entry, "cable_connected", "Cable Connected", BinarySensorDeviceClass.PLUG,
#            lambda d: d['data']['evses'][0]['session']['isCableConnected']
#        ),
        ElawayBinarySensor(
            None, entry, "auth_required", "Authentication Required", None,
            lambda d: d['data']['evses'][0]['auth_required'], icon="mdi:lock"
        ),
    ]
    
    # Merk: Hvis koordinatoren din ligger lagret på hass.data[DOMENE][entry.entry_id + "_coordinator"],
    # bytter du ut 'None' over med den koordinatoren.
    
#    async_add_entities(binary_sensors)

    ]
    async_add_entities(binary_sensors)

class ElawayBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Representasjon av en Elaway Binærsensor."""

    def __init__(self, coordinator, entry, key, name, device_class, value_fn, icon=None):
        """Initialiser binærsensoren."""
        super().__init__(coordinator) if coordinator else None
        self._key = key
        self._attr_name = name
        self._attr_device_class = device_class
        self._value_fn = value_fn
        if icon:
            self._attr_icon = icon
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMENE, "elaway_charger_device")},
            name="Elaway EV Charger",
            manufacturer="Utviklet av Eirik Skorstad",
            model="Zaptec Charger Station",
        )

    @property
    def is_on(self) -> bool | None:
        """Returner True hvis binærsensoren er aktiv/på."""
        if not self.coordinator or not self.coordinator.data:
            return None
        try:
            return bool(self._value_fn(self.coordinator.data))
        except (KeyError, IndexError, TypeError):
            return False
