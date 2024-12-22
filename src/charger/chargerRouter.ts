import express from "express";
import axios from "axios";
import config from "../config.js";
import { chargerInfo } from "../main.js";

const router = express.Router();

router.get("/", async (_req, res) => {
  const response = await axios.get(`${config.ampecoApiUrl}/personal/charge-points/${chargerInfo.chargerId}`);

  res.send(response.data)
});

router.post("/start", async (_req, res) => {
  const response = await axios.post(`${config.ampecoApiUrl}/session/start`, {
    evseId: chargerInfo.evseId
  });

  res.send(response.data.session)
});

router.post("/stop", async (_req, res) => {
  const charger = await axios.get(`${config.ampecoApiUrl}/personal/charge-points`);
  const currentSessionId = charger?.data?.data[0]?.evses[0]?.session?.id

  if (!currentSessionId) {
    res.status(404).send("No active session found");
    return
  }

  try {
    const response = await axios.post(`${config.ampecoApiUrl}/session/${currentSessionId}/end`);
    res.send(response.data);
  } catch (error) {
    res.send(error.response.data);
  }
});

export default router;
