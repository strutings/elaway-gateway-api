import 'dotenv/config';
import express from 'express';
import chargerRouter from './charger/chargerRouter.js';
import axios from 'axios';
import { getValidCredentials } from './auth.js';

const port = process.env.PORT || 3000;
const app = express();

const token = await getValidCredentials();

axios.interceptors.request.use(async (config) => {

dotenv.config();

const port = process.env.PORT || 3000;
const app = express();

axios.interceptors.request.use(async (config) => {
  const token = await getValidCredentials();
  config.headers.Authorization = `Bearer ${token?.access_token}`;

  return config;
});

app.use(express.json());

app.use("/charger", chargerRouter);

app.listen(port, () => {
  console.log(`Server is running on http://localhost:${port}`);
});
