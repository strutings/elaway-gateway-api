"""Elaway EV Charger integrasjon."""
from __future__ import annotations

from datetime import timedelta
import logging
import aiohttp

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import ElawayAPI
from .const import DOMENE

_LOGGER = logging.getLogger(__name__)

# Definer hvilke plattformer integrasjonen skal laste inn
PLATFORMS: list[str] = ["sensor", "binary_sensor", "button"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Setter opp Elaway fra en config entry (UI)."""
    config = entry.data

    # 1. Opprett API-instansen med lagret påloggingsdata fra config_flow
    api = ElawayAPI(
        username=config["elaway_user"],
        password=config["elaway_password"],
        client_id=config["client_id"],
        elaway_client_id=config["elaway_client_id"],
        elaway_client_secret=config["elaway_client_secret"],
        ampeco_api_url=config["ampeco_api_url"]
    )

    # 2. Definer oppdateringsfunksjonen for DataUpdateCoordinator sentralt
    async def _async_update_data():
        try:
            # Hent gyldig Bearer Token direkte fra vår asynkrone Python-klient
            token = await api.async_get_valid_credentials()
            
            url = f"{api.ampeco_api_url}/v1/user/chargers"
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "User-Agent": "insomnia/10.0.0"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status != 200:
                        raise UpdateFailed(f"Feil status fra Elaway API: {response.status}")
                    
                    raw_data = await response.json()
                    
                    # Pakk dataene inn i {"data": ...} så sensorenes lambdaer fungerer uendret
                    if isinstance(raw_data, list):
                        if not raw_data:
                            raise UpdateFailed("Ingen ladestasjoner funnet på denne kontoen.")
                        return {"data": raw_data[0]}
                    return {"data": raw_data}
                    
        except Exception as err:
            raise UpdateFailed(f"Klarte ikke å oppdatere data fra Elaway: {err}")

    # 3. Opprett koordinatoren sentralt
    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="Elaway Data Coordinator",
        update_method=_async_update_data,
        update_interval=timedelta(seconds=30),
    )

    # Hent første datapunkt umiddelbart under oppstart
    await coordinator.async_config_entry_first_refresh()

    # 4. Lagre både API og Koordinator i hass.data så alle plattformer har tilgang
    hass.data.setdefault(DOMENE, {})
    hass.data[DOMENE][entry.entry_id] = {
        "api": api,
        "coordinator": coordinator
    }

    # 5. Start opp sensor.py, binary_sensor.py og button.py
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Fjerner integrasjonen og stopper alle plattformer hvis brukeren sletter den."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMENE].pop(entry.entry_id)
    return unload_ok
