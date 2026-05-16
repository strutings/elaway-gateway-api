"""MQTT integrasjon for Elaway EV Charger i Home Assistant."""
from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

import aiohttp

from homeassistant.components import mqtt
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import CONF_CHARGER_API_URL, CONF_CHARGER_START_URL, CONF_CHARGER_STOP_URL, DOMENE

_LOGGER = logging.getLogger(__name__)

# MQTT Topics
MQTT_TOPIC_SENSOR = "homeassistant/sensor/charger/pricePerKwh"
MQTT_TOPIC_FIXEDFEE = "homeassistant/sensor/charger/markupFixedFeePerKwh"
MQTT_TOPIC_SESSIONENERGY = "homeassistant/sensor/charger/sessionenergy"
MQTT_TOPIC_SESSIONPOWER = "homeassistant/sensor/charger/sessionpower"
MQTT_TOPIC_SESSIONTOTAL = "homeassistant/sensor/charger/totalAmount"
MQTT_TOPIC_TIMESTARTED = "homeassistant/sensor/charger/startedAt"
MQTT_TOPIC_TARIFF = "homeassistant/sensor/charger/tariff"
MQTT_TOPIC_MONTHENERGY = "homeassistant/sensor/charger/monthenergy"
MQTT_TOPIC_BINARY_SENSOR_STATUS = "homeassistant/binary_sensor/charger/available"

MQTT_TOPIC_BUTTON_START = "homeassistant/button/charger/start"
MQTT_TOPIC_BUTTON_STOP = "homeassistant/button/charger/stop"


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Setter opp Elaway fra en config entry (Config Flow)."""
    # Hent URL-er fra config flow lagringen
    charger_api_url = entry.data[CONF_CHARGER_API_URL]
    charger_start_url = entry.data[CONF_CHARGER_START_URL]
    charger_stop_url = entry.data[CONF_CHARGER_STOP_URL]

    charger_manager = ElawayChargerIntegration(
        hass, charger_api_url, charger_start_url, charger_stop_url
    )

    success = await charger_manager.async_setup()
    
    if success:
        # Lagre instansen i hass.data så vi kan fjerne den ved avinnstallering
        hass.data.setdefault(DOMENE, {})
        hass.data[DOMENE][entry.entry_id] = charger_manager
        return True
        
    return False


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Fjerner en Elaway-konfigurasjon (bruker trykker 'Slett')."""
    charger_manager: ElawayChargerIntegration = hass.data[DOMENE].get(entry.entry_id)
    
    if charger_manager:
        await charger_manager.async_unload()
        hass.data[DOMENE].pop(entry.entry_id)
        
    return True


class ElawayChargerIntegration:
    """Integrasjon for Elaway EV Charger."""
    
    def __init__(self, hass: HomeAssistant, charger_api_url: str, charger_start_url: str, charger_stop_url: str):
        """Initialize the Elaway charger integration."""
        self.hass = hass
        self.charger_api_url = charger_api_url
        self.charger_start_url = charger_start_url
        self.charger_stop_url = charger_stop_url
        self._fetch_task = None
        self._session: aiohttp.ClientSession = None

    async def async_setup(self) -> bool:
        """Set up the integration."""
        try:
            self._session = async_get_clientsession(self.hass)
            await self.publish_discovery()
            
            # Subscribe to button topics
            await mqtt.async_subscribe(
                self.hass,
                MQTT_TOPIC_BUTTON_START,
                self._handle_start_button,
                1
            )
            await mqtt.async_subscribe(
                self.hass,
                MQTT_TOPIC_BUTTON_STOP,
                self._handle_stop_button,
                1
            )
            
            # Start fetching loop
            self._fetch_task = asyncio.create_task(self._fetch_loop())
            _LOGGER.info("Elaway charger integration set up successfully")
            return True
        except Exception as e:
            _LOGGER.error(f"Failed to set up Elaway charger integration: {e}")
            return False

    async def async_unload(self) -> None:
        """Unload the integration."""
        if self._fetch_task:
            self._fetch_task.cancel()
            try:
                await self._fetch_task
            except asyncio.CancelledError:
                pass

    @callback
    async def _handle_start_button(self, msg) -> None:
        """Handle start button press."""
        _LOGGER.debug("Start button pressed")
        try:
            async with self._session.post(self.charger_start_url) as resp:
                if resp.status == 200:
                    _LOGGER.info("Charger started successfully")
                else:
                    _LOGGER.error(f"Failed to start charger: {resp.status}")
        except Exception as e:
            _LOGGER.error(f"Error starting charger: {e}")

    @callback
    async def _handle_stop_button(self, msg) -> None:
        """Handle stop button press."""
        _LOGGER.debug("Stop button pressed")
        try:
            async with self._session.post(self.charger_stop_url) as resp:
                if resp.status == 200:
                    _LOGGER.info("Charger stopped successfully")
                else:
                    _LOGGER.error(f"Failed to stop charger: {resp.status}")
        except Exception as e:
            _LOGGER.error(f"Error stopping charger: {e}")

    async def publish_discovery(self) -> None:
        """Publish Home Assistant MQTT Discovery configs."""
        # ... (Behold all den eksisterende koden din for publish_discovery her uendret) ...
        sensor_config = {
            "name": "Elaway Charger Price Per Kwh",
            "state_topic": f"{MQTT_TOPIC_SENSOR}/state",
            "unit_of_measurement": "NOK/kWh",
            "device_class": "monetary"
        }
        fixedfee_config = {
            "name": "Elaway Charger Fixed fee per Kwh",
            "state_topic": f"{MQTT_TOPIC_FIXEDFEE}/state",
            "unit_of_measurement": "NOK/kWh",
            "device_class": "monetary"
        }
        sessionenergy_config = {
            "name": "Elaway Current session energy",
            "state_topic": f"{MQTT_TOPIC_SESSIONENERGY}/state",
            "unit_of_measurement": "kWh",
            "device_class": "energy_storage"
        }
        sessionpower_config = {
            "name": "Elaway Current session Power",
            "state_topic": f"{MQTT_TOPIC_SESSIONPOWER}/state",
            "unit_of_measurement": "W",
            "device_class": "energy"
        }
        sessiontotal_config = {
            "name": "Elaway Session total NOK",
            "state_topic": f"{MQTT_TOPIC_SESSIONTOTAL}/state",
            "unit_of_measurement": "NOK",
            "device_class": "monetary"
        }
        timestarted_config = {
            "name": "Elaway Session start",
            "state_topic": f"{MQTT_TOPIC_TIMESTARTED}/state",
        }
        tariff_config = {
            "name": "Elaway tariff",
            "state_topic": f"{MQTT_TOPIC_TARIFF}/state",
        }
        monthenergy_config = {
            "name": "Elaway Monthly Energy",
            "state_topic": f"{MQTT_TOPIC_MONTHENERGY}/state",
            "unit_of_measurement": "kWh",
            "device_class": "energy"
        }
        available_config = {
            "name": "Elaway EV Charger Status",
            "state_topic": f"{MQTT_TOPIC_BINARY_SENSOR_STATUS}/state",
            "device_class": "connectivity",
            "payload_on": "1",
            "payload_off": "0"
        }

        await mqtt.async_publish(self.hass, "homeassistant/sensor/charger/config", json.dumps(sensor_config), retain=True)
        
        switch_start_config = {"name": "Start Elaway Charging", "command_topic": MQTT_TOPIC_BUTTON_START}
        await mqtt.async_publish(self.hass, "homeassistant/button/charger_start/config", json.dumps(switch_start_config), retain=True)

        switch_stop_config = {"name": "Stop Elaway Charging", "command_topic": MQTT_TOPIC_BUTTON_STOP}
        await mqtt.async_publish(self.hass, "homeassistant/button/charger_stop/config", json.dumps(switch_stop_config), retain=True)
        
        await mqtt.async_publish(self.hass, "homeassistant/sensor/charger/fixedfee/config", json.dumps(fixedfee_config), retain=True)
        await mqtt.async_publish(self.hass, "homeassistant/sensor/charger/sessionenergy/config", json.dumps(sessionenergy_config), retain=True)
        await mqtt.async_publish(self.hass, "homeassistant/sensor/charger/sessionpower/config", json.dumps(sessionpower_config), retain=True)
        await mqtt.async_publish(self.hass, "homeassistant/sensor/charger/sessiontotal/config", json.dumps(sessiontotal_config), retain=True)
        await mqtt.async_publish(self.hass, "homeassistant/sensor/charger/timestarted/config", json.dumps(timestarted_config), retain=True)
        await mqtt.async_publish(self.hass, "homeassistant/sensor/charger/tariff/config", json.dumps(tariff_config), retain=True)
        await mqtt.async_publish(self.hass, "homeassistant/sensor/charger/monthenergy/config", json.dumps(monthenergy_config), retain=True)
        await mqtt.async_publish(self.hass, "homeassistant/binary_sensor/charger/available/config", json.dumps(available_config), retain=True)

    async def _fetch_loop(self) -> None:
        """Main fetch loop - runs every 60 seconds."""
        while True:
            try:
                await self.fetch_and_publish()
                await asyncio.sleep(60)
            except asyncio.CancelledError:
                break
            except Exception as e:
                _LOGGER.error(f"Error in fetch loop: {e}")
                await asyncio.sleep(60)

    async def fetch_and_publish(self) -> None:
        """Fetch charger data and publish to MQTT."""
        # ... (Behold resten av fetch_and_publish koden din helt uendret her) ...
        try:
            async with self._session.get(self.charger_api_url) as resp:
                if resp.status != 200:
                    _LOGGER.error(f"Failed to fetch charger data: {resp.status}")
                    return
                
                data = await resp.json()
                evse = data['data']['evses'][0]
                
                try:
                    price_per_kwh = evse['tariff']['pricing']['pricePerKwh']
                    await mqtt.async_publish(self.hass, f"{MQTT_TOPIC_SENSOR}/state", price_per_kwh)
                except KeyError:
                    _LOGGER.warning("Could not find pricePerKwh in response")
                
                try:
                    fixedfee = evse['tariff']['pricing']['markupFixedFeePerKwh']
                    await mqtt.async_publish(self.hass, f"{MQTT_TOPIC_FIXEDFEE}/state", fixedfee)
                except KeyError:
                    _LOGGER.warning("Could not find markupFixedFeePerKwh in response")
                
                try:
                    sessionenergy = evse['session']['energy']
                    await mqtt.async_publish(self.hass, f"{MQTT_TOPIC_SESSIONENERGY}/state", sessionenergy / 1000)
                except KeyError:
                    await mqtt.async_publish(self.hass, f"{MQTT_TOPIC_SESSIONENERGY}/state", "0")
                
                try:
                    sessionpower = evse['session']['power']
                    await mqtt.async_publish(self.hass, f"{MQTT_TOPIC_SESSIONPOWER}/state", sessionpower)
                except KeyError:
                    await mqtt.async_publish(self.hass, f"{MQTT_TOPIC_SESSIONPOWER}/state", "0")
                
                try:
                    session_total = evse['session']['totalAmount']
                    await mqtt.async_publish(self.hass, f"{MQTT_TOPIC_SESSIONTOTAL}/state", session_total)
                except KeyError:
                    await mqtt.async_publish(self.hass, f"{MQTT_TOPIC_SESSIONTOTAL}/state", "0")
                
                try:
                    time_started = evse['session']['startedAt']
                    await mqtt.async_publish(self.hass, f"{MQTT_TOPIC_TIMESTARTED}/state", time_started)
                except KeyError:
                    await mqtt.async_publish(self.hass, f"{MQTT_TOPIC_TIMESTARTED}/state", "not_started")
                
                try:
                    tariff = evse['tariff']['name']
                    await mqtt.async_publish(self.hass, f"{MQTT_TOPIC_TARIFF}/state", tariff)
                except KeyError:
                    _LOGGER.warning("Could not find tariff name in response")
                
                try:
                    monthenergy = data['data']['last_month_energy_kwh']
                    await mqtt.async_publish(self.hass, f"{MQTT_TOPIC_MONTHENERGY}/state", monthenergy)
                except KeyError:
                    _LOGGER.warning("Could not find last_month_energy_kwh in response")
                
                try:
                    status = data['data']['status']
                    payload = '1' if status == 'available' else '0'
                    await mqtt.async_publish(self.hass, f"{MQTT_TOPIC_BINARY_SENSOR_STATUS}/state", payload)
                except KeyError:
                    _LOGGER.warning("Could not find status in response")
                
                _LOGGER.debug("Charger data published successfully")
        
        except asyncio.TimeoutError:
            _LOGGER.error("Timeout fetching charger data")
        except Exception as e:
            _LOGGER.error(f"Error fetching charger data: {e}")
