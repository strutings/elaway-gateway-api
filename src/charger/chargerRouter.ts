import express from "express";
import Charger from "./charger.js";

const router = express.Router();

router.get("/", async (_req, res) => {
  res.send(await Charger.getInstance())
});

router.post("/start", async (_req, res) => {
  const charger = await Charger.getInstance();

  try {
    res.send(await charger.startCharging());
  } catch (error) {
    res.status(400).send(error.message);
  }
});

router.post("/stop", async (_req, res) => {
  const charger = await Charger.getInstance();
  try {
    res.send(await charger.stopCharging());
  } catch (error) {
    res.status(400).send(error.message);
  }
});

export default router;
