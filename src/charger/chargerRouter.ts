import express from "express";
import axios from "axios";
import config from "../config.js";
import { chargerInfo } from "./charger.js";

const router = express.Router();

router.get("/", async (_req, res) => {
  try {
    const response = await axios.get(`${config.ampecoApiUrl}/personal/charge-points/${chargerInfo.chargerId}`);
    res.send(response.data);
  } catch (error) {
    console.error("Error fetching charger info:", error);
    res.status(500).send("Failed to fetch charger info");
  }
});

router.post("/start", async (_req, res) => {
  try {
    const response = await axios.post(`${config.ampecoApiUrl}/session/start`, {
      evseId: chargerInfo.evseId
    });
    res.send(response.data.session);
  } catch (error) {
    console.error("Error starting session:", error);
    res.status(500).send(error.response.data);
  }
});

router.post("/stop", async (_req, res) => {
  try {
    const charger = await axios.get(`${config.ampecoApiUrl}/personal/charge-points`);
    const currentSessionId = charger?.data?.data[0]?.evses[0]?.session?.id;

    if (!currentSessionId) {
      res.status(404).send("No active session found");
      return;
    }

    const response = await axios.post(`${config.ampecoApiUrl}/session/${currentSessionId}/end`);
    res.send(response.data);
  } catch (error) {
    console.error("Error stopping session:", error);
    res.status(500).send(error.response.data);
  }
});

export default router;
