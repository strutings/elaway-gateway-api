import config from './config.js';
import express from 'express';
import chargerRouter from './charger/chargerRouter.js';
import axios from 'axios';
import { getValidCredentials } from './auth.js';

const port = config.port;
const app = express();

let token = await getValidCredentials();

if (!token) {
  throw new Error('Could not get valid credentials');
}

axios.interceptors.request.use(async (config) => {
  // Check if the token is still valid, if not, get a new one
  if (token.expires_at < Date.now()) {
    token = await getValidCredentials();
    if (!token) {
      throw new Error('Could not get valid credentials');
    }
  }
  config.headers.Authorization = `Bearer ${token.access_token}`;
  return config;
});

app.use(express.json());

app.use("/charger", chargerRouter);

app.listen(port, () => {
  console.info(`Server is running on http://localhost:${port}`);
});
