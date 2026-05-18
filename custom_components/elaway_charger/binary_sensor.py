"""Støtte for Elaway binærsensor (Status)."""
from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMENE


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Sett opp status-sensor."""
    coordinator = hass.data[DOMENE][entry.entry_id]
    async_add_entities([ElawayBinarySensor(coordinator, entry)])


class ElawayBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Status-sensor."""

    def __init__(self, coordinator, entry):
        """Initialiser."""
        super().__init__(coordinator)
        self._attr_name = "Status"
        self._attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
        self._attr_unique_id = f"{entry.entry_id}_available"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMENE, "elaway_charger_device")},
            name="Elaway EV Charger",
            manufacturer="Utviklet av Eirik Skorstad",
            model="Zaptec Charger Station",
        )

    @property
    def is_on(self) -> bool:
        """Returner true hvis laderen er tilgjengelig."""
        if not self.coordinator.data:
            return False
        try:
            status = self.coordinator.data['data']['status']
            return status == 'available'
        except (KeyError, TypeError):
            return False
