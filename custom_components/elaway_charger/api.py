import logging
import time
from urllib.parse import urlparse, parse_qs
import aiohttp
from bs4 import BeautifulSoup

_LOGGER = logging.getLogger(__name__)

OAUTH_SCOPE = "openid profile email"
STATE = "randomstate"
REDIRECT_URI = "io.elaway.no.app://auth.elaway.io/ios/io.elaway.no.app/callback"
AUTH_URL = "https://auth.elaway.io/authorize"
ELAWAY_TOKEN_URL = "https://auth.elaway.io/oauth/token"

class ElawayAPI:
    """Python-erstatning for Node.js Auth-logikken."""

    def __init__(self, username, password, client_id, elaway_client_id, elaway_client_secret, ampeco_api_url):
        self.username = username
        self.password = password
        self.client_id = client_id
        self.elaway_client_id = elaway_client_id
        self.elaway_client_secret = elaway_client_secret
        self.ampeco_api_url = ampeco_api_url
        self.access_token = None
        self.expires_at = 0

    async def async_get_valid_credentials(self) -> str:
        """Sjekker om vi har gyldig token, hvis ikke kjøres OAuth-flyten."""
        if self.access_token and self.expires_at > time.time():
            _LOGGER.debug("Bruker eksisterende bearer-token")
            return self.access_token

        _LOGGER.info("Ingen gyldig token funnet. Starter påloggingsflyt.")
        token_data = await self._async_start_oauth()
        
        if token_data:
            self.access_token = token_data.get("access_token")
            self.expires_at = time.time() + token_data.get("expires_in", 3600)
            return self.access_token
        
        raise Exception("Klarte ikke å hente token fra Elaway")

    async def _async_start_oauth(self):
        """Simulerer nettleseren og henter token uten Puppeteer."""
        # Vi må tillate omdirigeringer (redirects) manuelt for å fange opp koden
        jar = aiohttp.CookieJar(unsafe=True)
        async with aiohttp.ClientSession(cookie_jar=jar) as session:
            
            # 1. Gå til autorisasjonssiden for å hente form-cookies og sjekke stien
            params = {
                "response_type": "code",
                "client_id": self.client_id,
                "redirect_uri": REDIRECT_URI,
                "scope": OAUTH_SCOPE,
                "state": STATE
            }
            
            async with session.get(AUTH_URL, params=params) as response:
                html = await response.text()
                # Hvis Auth0 bruker en dynamisk POST-url (f.eks. /usernamepassword/login)
                # fanger vi den opp via form action. Ofte er den statisk.
                soup = BeautifulSoup(html, "html.parser")
                form = soup.find("form")
                login_url = response.url
                if form and form.get("action"):
                    login_url = response.url.join(urlparse(form.get("action")))

            # 2. Post brukernavn og passord (tilsvarer page.type og Enter)
            # Merk: Noen Auth0-sider krever 'state' eller 'wctx' i payload. Hvis dette feiler,
            # må vi trekke ut hidden-felter fra 'soup' over.
            payload = {
                "username": self.username,
                "password": self.password,
                "client_id": self.client_id,
                "grant_type": "password"
            }
            
            # Vi skrur av 'allow_redirects' her fordi vi VIL fange opp 302-redirecten selv!
            async with session.post(login_url, data=payload, allow_redirects=False) as response:
                location = response.headers.get("Location")
                
                # Hvis vi ikke fikk omdirigering umiddelbart, sjekk om vi må følge en mellomside
                if response.status == 200:
                    # Noen ganger returnerer Auth0 en side som gjør en JS-redirect eller har en ny form
                    html = await response.text()
                    soup = BeautifulSoup(html, "html.parser")
                    # Sjekk om det finnes en form som poster videre automatisk
                    form = soup.find("form")
                    if form:
                        action_url = form.get("action")
                        inputs = {i.get("name"): i.get("value") for i in form.find_all("input") if i.get("name")}
                        async with session.post(action_url, data=inputs, allow_redirects=False) as redir_resp:
                            location = redir_resp.headers.get("Location")

            if not location or not location.startswith(REDIRECT_URI):
                _LOGGER.error("Klarte ikke å fange opp omdirigerings-URL med auth-kode.")
                return None

            # 3. Trekk ut autorisasjonskoden fra URL-en
            parsed_url = urlparse(location)
            query_params = parse_qs(parsed_url.query)
            code = query_params.get("code", [None])[0]
            
            if not code:
                _LOGGER.error("Fant ingen 'code' i redirect-URL-en.")
                return None

            _LOGGER.info("Fant autorisasjonskode. Vekslar inn i tokens.")

            # 4. Bytt kode mot ID- og Auth-token (Svarer til exchangeCodeForIdAndAuthToken)
            token_payload = {
                "grant_type": "authorization_code",
                "client_id": self.client_id,
                "redirect_uri": REDIRECT_URI,
                "code": code
            }
            async with session.post(ELAWAY_TOKEN_URL, json=token_payload) as token_resp:
                if token_resp.status != 200:
                    return None
                tokens = await token_resp.json()

            # 5. Hent Ampeco/Elaway token (Svarer til getElawayToken)
            import json
            ampeco_payload = {
                "token": json.dumps({
                    "accessToken": tokens.get("access_token"),
                    "idToken": tokens.get("id_token"),
                    "scope": OAUTH_SCOPE,
                    "expiresIn": 100,
                    "tokenType": "Bearer"
                }),
                "type": "auth0",
                "grant_type": "third-party",
                "client_id": self.elaway_client_id,
                "client_secret": self.elaway_client_secret
            }
            
            headers = {"User-Agent": "insomnia/10.0.0"}
            async with session.post(self.ampeco_api_url, json=ampeco_payload, headers=headers) as ampeco_resp:
                if ampeco_resp.status != 200:
                    _LOGGER.error("Feil ved henting av Ampeco-token")
                    return None
                return await ampeco_resp.json()
