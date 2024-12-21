import express from "express";
import Charger from "./charger.js";

const router = express.Router();

router.get("/", async (_req, res) => {
  res.send(await Charger.getInstance())
});

router.post("/start", async (_req, res) => {
  const charger = await Charger.getInstance();
  res.send(await charger.startCharging());
});

router.post("/stop", async (_req, res) => {
  const charger = await Charger.getInstance();
  res.send(await charger.stopCharging());
});

export default router;
