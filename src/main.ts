import config from './config.js';
import express from 'express';
import chargerRouter from './charger/chargerRouter.js';
import axios from 'axios';
import { getValidCredentials } from './auth.js';

const port = config.port;
const app = express();
const token = await getValidCredentials();

if (!token) {
  throw new Error('Could not get valid credentials');
}

axios.interceptors.request.use(async (config) => {
  config.headers.Authorization = `Bearer ${token?.access_token}`;
  return config;
});

const chargerData = (await axios.get(`${config.ampecoApiUrl}/personal/charge-points`)).data.data[0];

const chargerInfo = {
  chargerId: chargerData.id,
  evseId: chargerData.evses[0].id
}

app.use(express.json());

app.use("/charger", chargerRouter);

app.listen(port, () => {
  console.info(`Server is running on http://localhost:${port}`);
});

export { chargerInfo };
