import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from .api import ElawayAPI

DOMAIN = "elaway_charger"

class ElawayConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Håndterer oppsett via Home Assistant UI."""
    
    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Kjøres når brukeren legger til integrasjonen manuelt."""
        errors = {}

        if user_input is not None:
            # Test om innloggingen fungerer før vi lagrer!
            api = ElawayAPI(
                username=user_input["elaway_user"],
                password=user_input["elaway_password"],
                client_id=user_input["client_id"],
                elaway_client_id=user_input["elaway_client_id"],
                elaway_client_secret=user_input["elaway_client_secret"],
                ampeco_api_url=user_input["ampeco_api_url"]
            )
            
            try:
                await api.async_get_valid_credentials()
                # Suksess! Opprett integrasjonen i HA
                return self.async_create_entry(
                    title=f"Elaway ({user_input['elaway_user']})", 
                    data=user_input
                )
            except Exception:
                errors["base"] = "cannot_connect"

        # Feltene brukeren ser på skjermen
        data_schema = vol.Schema({
            vol.Required("elaway_user"): str,
            vol.Required("elaway_password"): str,
            vol.Required("client_id"): str,
            vol.Required("elaway_client_id"): str,
            vol.Required("elaway_client_secret"): str,
            vol.Required("ampeco_api_url", default="https://api.ampeco.com"): str, # Juster default hvis nødvendig
        })

        return self.show_form(
            step_id="user", 
            data_schema=data_schema, 
            errors=errors
        )
