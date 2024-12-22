import config from './config.js';
import puppeteer, { type Page } from 'puppeteer';
import axios from 'axios';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const oauthScope = "openid profile email";
const state = "randomstate";
const redirectUri = "io.elaway.no.app://auth.elaway.io/ios/io.elaway.no.app/callback";
const elawayAuthorizationUrl = "https://auth.elaway.io/authorize";
const ampecoApiUrl = `${config.ampecoApiUrl}/oauth/token`;
const elawayTokenUrl = "https://auth.elaway.io/oauth/token";
const tokenFilePath = path.resolve(__dirname, 'tokens.json');

interface IdTokenResponse {
  access_token: string;
  id_token: string;
  expires_in: number;
}

interface ElawayTokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: "Bearer",
  expires_in: number,
}

interface StoredElawayToken {
  access_token: string;
  refresh_token: string;
  token_type: "Bearer",
  expires_at: number,
}

async function getAuthorizationCode(page: Page): Promise<string | null> {
  return new Promise((resolve, reject) => {
    page.on('response', async (response) => {
      try {
        const status = response.status();
        if (status >= 300 && status < 400) {
          const headers = response.headers();
          if (headers.location?.startsWith('io.elaway.no.app://')) {
            const urlObj = new URL(headers.location);
            const returnedCode = urlObj.searchParams.get('code');
            const returnedState = urlObj.searchParams.get('state');

            if (returnedCode && returnedState === state) {
              resolve(returnedCode);
            }
          }
        }
      } catch (error) {
        reject(error);
      }
    });
  });
}

async function exchangeCodeForIdAndAuthToken(code: string): Promise<IdTokenResponse> {
  const response = await axios.post(elawayTokenUrl, {
    grant_type: "authorization_code",
    client_id: config.clientId,
    redirect_uri: redirectUri,
    code: code
  }, {
    headers: {
      "Content-Type": "application/json"
    }
  });

  if (response.status !== 200) {
    console.error("Error during token exchange:", response.data);
  }

  return response.data;
}


// TODO: Figure out how to refresh the access token
// async function refreshAccessToken(refreshToken: string): Promise<ElawayTokenResponse> {

//   console.log(refreshToken)

// const response = await axios.post(elawayTokenUrl, {
//   grant_type: "refresh_token",
//   client_id: clientId,
//   refresh_token: refreshToken
// }, {
//   headers: {
//     "Content-Type": "application/json"
//   }
// });

// return response.data;
// }

async function getElawayToken(accessToken: string, idToken: string): Promise<ElawayTokenResponse | null> {
  try {
    const response = await axios.post(ampecoApiUrl, {
      token: JSON.stringify({
        accessToken: accessToken,
        idToken: idToken,
        scope: "openid profile email",
        expiresIn: 100,
        tokenType: "Bearer"
      }),
      type: "auth0",
      grant_type: "third-party",
      client_id: config.elawayClientId,
      client_secret: config.elawayClientSecret
    }, {
      headers: {
        "Content-Type": "application/json",
        "User-Agent": "insomnia/10.0.0"
      }
    });

    saveTokens(response.data);

    return response.data;
  } catch (error) {
    console.error(error.message);
    return null;
  }
}

function saveTokens(tokenResponse: ElawayTokenResponse): StoredElawayToken {
  const expiresAt = Date.now() + tokenResponse.expires_in * 1000;

  const storedToken: StoredElawayToken = {
    token_type: tokenResponse.token_type,
    access_token: tokenResponse.access_token,
    refresh_token: tokenResponse.refresh_token,
    expires_at: expiresAt
  };
  fs.writeFileSync(tokenFilePath, JSON.stringify(storedToken));

  console.info("New bearer token saved");

  return storedToken;
}

function loadTokens(): StoredElawayToken | null {
  if (fs.existsSync(tokenFilePath)) {
    const storedToken = JSON.parse(fs.readFileSync(tokenFilePath, 'utf-8')) as StoredElawayToken;

    return storedToken;
  }
  return null;
}

async function startOauth(): Promise<ElawayTokenResponse | null> {
  let tokenResponse: ElawayTokenResponse | null = null;
  let accessIdResponse: null | IdTokenResponse = null;
  const authUrl = `${elawayAuthorizationUrl}?response_type=code&client_id=${encodeURIComponent(config.clientId)}&redirect_uri=${encodeURIComponent(redirectUri)}&scope=${encodeURIComponent(oauthScope)}&state=${encodeURIComponent(state)}`;

  const browser = await puppeteer.launch({ headless: true, args: ['--no-sandbox'] });
  const page = await browser.newPage();

  try {
    await page.goto(authUrl, { waitUntil: 'domcontentloaded', timeout: 10000 });

    const errorMessage = await page.evaluate(() => {
      const errorElement = document.querySelector('p.error-message');
      return errorElement ? (errorElement as HTMLElement).innerText : null;
    });

    if (errorMessage) {
      console.error("Error on login page:", errorMessage);
      throw new Error("Error during login. You most likely have the wrong CLIENT_ID")
    }

    await page.waitForSelector('input[name="username"]');
    await page.waitForSelector('input[name="password"]');
    await page.type('input[name="username"]', config.elawayUser, { delay: 50 });
    await page.type('input[name="password"]', config.elawayPassword, { delay: 50 });
    await page.keyboard.press('Enter');

    const code = await getAuthorizationCode(page);
    if (code) {
      console.info("Found authorization code.");
      await browser.close();

      accessIdResponse = await exchangeCodeForIdAndAuthToken(code);

      tokenResponse = await getElawayToken(accessIdResponse.access_token, accessIdResponse.id_token);
    }
  } catch (error) {
    console.error(error.message);
  } finally {
    await browser.close();
  }
  return tokenResponse
}

async function getValidCredentials(): Promise<StoredElawayToken | null> {
  const storedToken = loadTokens();

  const validBearerToken = storedToken && storedToken.expires_at > Date.now();

  // Sjekk om token går ut om mindre enn 5 minutter
  // Forleng tokenet

  // const refreshedToken = await refreshAccessToken(storedToken.refresh_token);


  // if (storedToken && storedToken.expires_at - Date.now() < 5 * 60 * 1000) {
  //   const refreshedToken = await refreshAccessToken(storedToken.refresh_token);
  //   if (refreshedToken) {
  //     saveTokens(refreshedToken);
  //   }
  // }

  if (!validBearerToken) {
    console.info("No existing bearer token found. Attempting to get new token.");
    const newToken = await startOauth();

    if (!newToken) {
      throw new Error("Could not get valid credentials");
    }
    return loadTokens();
  }

  console.info("Using stored bearer token");

  return storedToken;
}

export { getValidCredentials };
