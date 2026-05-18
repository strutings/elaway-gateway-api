"""Støtte for Elaway sensorer."""
from __future__ import annotations

from datetime import timedelta
import logging
import aiohttp

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity, DataUpdateCoordinator, UpdateFailed

from .const import DOMENE

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Sett opp sensorer basert på Elaway API-struktur."""
    # Hent koordinatoren fra den sentrale lagringen i __init__.py
    coordinator = hass.data[DOMENE][entry.entry_id]["coordinator"]

    
    # 1. Hent ut API-klienten vi lagret i __init__.py
    api = hass.data[DOMENE][entry.entry_id]
    
    # 2. Definer oppdateringsfunksjonen som erstatter Docker-kallene
    async def _async_update_data():
        try:
            # Hent gyldig Bearer Token direkte fra vår nye asynkrone Python-klient
            token = await api.async_get_valid_credentials()
            
            # Dette er den nøyaktige URL-en som Node-appen din brukte i bakgrunnen
            url = f"{api.ampeco_api_url}/v1/user/chargers"
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "User-Agent": "insomnia/10.0.0"
            }
            
            # Hent rådataene direkte fra Elaway/Ampeco
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status != 200:
                        raise UpdateFailed(f"Feil status fra Elaway API: {response.status}")
                    
                    raw_data = await response.json()
                    
                    # Siden sensorene dine forventer strukturen d['data'][...],
                    # pakker vi dataene inn slik at lambda-funksjonene dine fungerer uendret.
                    # Hvis Ampeco-responsen din returnerer en liste, henter vi det første elementet.
                    if isinstance(raw_data, list):
                        return {"data": raw_data[0]}
                    return {"data": raw_data}
                    
        except Exception as err:
            raise UpdateFailed(f"Klarte ikke å oppdatere Elaway-data: {err}")

    # 3. Opprett koordinatoren lokalt her
    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="Elaway Sensor Coordinator",
        update_method=_async_update_data,
        update_interval=timedelta(seconds=30), # Juster oppdateringsfrekvensen her
    )

    # Hent første datapunkt umiddelbart under oppstart av HA
    await coordinator.async_config_entry_first_refresh()
    
    sensors = [
        # --- Eksisterende sensorer ---
        ElawaySensor(
            coordinator, entry, "price_per_kwh", "Price Per kWh", "NOK/kWh", SensorDeviceClass.MONETARY, 
            lambda d: d['data']['evses'][0]['tariff']['pricing']['pricePerKwh']
        ),
        ElawaySensor(
            coordinator, entry, "fixed_fee", "Fixed Fee Per kWh", "NOK/kWh", SensorDeviceClass.MONETARY, 
            lambda d: d['data']['evses'][0]['tariff']['pricing']['markupFixedFeePerKwh']
        ),
        ElawaySensor(
            coordinator, entry, "session_energy", "Current Session Energy", "kWh", SensorDeviceClass.ENERGY, 
            lambda d: d['data']['evses'][0]['session']['energy'] / 1000, SensorStateClass.TOTAL
        ),
        ElawaySensor(
            coordinator, entry, "session_power", "Current Session Power", "W", SensorDeviceClass.POWER, 
            lambda d: d['data']['evses'][0]['session']['power'], SensorStateClass.MEASUREMENT
        ),
        ElawaySensor(
            coordinator, entry, "session_total", "Session Total Cost", "NOK", SensorDeviceClass.MONETARY, 
            lambda d: d['data']['evses'][0]['session']['totalAmount']
        ),
        ElawaySensor(
            coordinator, entry, "time_started", "Session Started At", None, None, 
            lambda d: d['data']['evses'][0]['session']['startedAt']
        ),
        ElawaySensor(
            coordinator, entry, "tariff_name", "Tariff Name", None, None, 
            lambda d: d['data']['evses'][0]['tariff']['name']
        ),
        ElawaySensor(
            coordinator, entry, "month_energy", "Monthly Energy", "kWh", SensorDeviceClass.ENERGY, 
            lambda d: d['data']['last_month_energy_kwh'], SensorStateClass.TOTAL_INCREASING
        ),

        # --- NYE SENSORER FRA RELL DATA ---
        ElawaySensor(
            coordinator, entry, "charging_state", "Charging State", None, None, 
            lambda d: d['data']['evses'][0]['session']['chargingState'], icon="mdi:ev-station"
        ),
        ElawaySensor(
            coordinator, entry, "allowed_max_current", "Allowed Max Current", "A", SensorDeviceClass.CURRENT, 
            lambda d: d['data']['allowed_max_current_a'], SensorStateClass.MEASUREMENT
        ),
        ElawaySensor(
            coordinator, entry, "allowed_max_power", "Allowed Max Power", "kW", SensorDeviceClass.POWER, 
            lambda d: float(d['data']['allowed_max_power_kw']), SensorStateClass.MEASUREMENT
        ),
        ElawaySensor(
            coordinator, entry, "firmware_version", "Firmware Version", None, None, 
            lambda d: d['data']['firmware_version'], icon="mdi:firmware"
        ),
        ElawaySensor(
            coordinator, entry, "light_intensity", "Charger Light Intensity", "%", None, 
            lambda d: d['data']['light_intensity'] * 10, SensorStateClass.MEASUREMENT, icon="mdi:led-on"
        ),
    ]
    
    async_add_entities(sensors)


class ElawaySensor(CoordinatorEntity, SensorEntity):
    """Representasjon av en Elaway Sensor."""

    def __init__(self, coordinator, entry, key, name, unit, device_class, value_fn, state_class=None, icon=None):
        """Initialiser sensoren."""
        super().__init__(coordinator)
        self._key = key
        self._attr_name = name
        self._attr_unit_of_measurement = unit
        self._attr_device_class = device_class
        self._attr_state_class = state_class
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
    def native_value(self):
        """Returner nåværende verdi til Home Assistant med feilhåndtering."""
        if not self.coordinator.data:
            return None
        try:
            return self._value_fn(self.coordinator.data)
        except (KeyError, IndexError, TypeError):
            return None
