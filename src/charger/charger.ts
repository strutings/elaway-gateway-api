import axios from "axios";
import config from "../config.js";

class Charger {
  private static instance: Charger;
  chargerId: string;
  evseId: number;

  private constructor(chargerId: string, evseId: number) {
    this.chargerId = chargerId;
    this.evseId = evseId;
  }

  static async getInstance(): Promise<Charger> {
    if (!Charger.instance) {
      const response = await axios.get(`${config.ampecoApiUrl}/personal/charge-points`);

      const chargerData = response.data.data[0];

      const chargePointData = chargerData;
      Charger.instance = new Charger(chargePointData.id, chargePointData.evses[0].id);
    }
    return Charger.instance;
  }

  public async checkSessionStatus(): Promise<number | undefined> {
    try {
      const response = await axios.get(`${config.ampecoApiUrl}/personal/charge-points/${this.chargerId}`);
      const currentSessionId = response?.data?.data?.evses[0]?.session?.id;
      return currentSessionId;

    } catch (error) {
      console.error('Error during session status check:', error);
    }

    return undefined;
  }

  startPeriodicCheck() {
    this.checkSessionStatus();

    setInterval(async () => {
      await this.checkSessionStatus();
    }, config.pollingInterval); // Sjekk hvert minutt (60000 ms)
  }

  public async getChargerInfo() {
    const response = await axios.get(`${config.ampecoApiUrl}/personal/charge-points/${this.chargerId}`);

    return response.data;
  }

  public async startCharging() {
    const response = await axios.post(`${config.ampecoApiUrl}/session/start`, {
      evseId: this.evseId
    });

    return response.data.session
  }

  public async stopCharging() {
    const charger = await axios.get(`${config.ampecoApiUrl}/personal/charge-points`);
    const currentSessionId = charger?.data?.data[0]?.evses[0]?.session?.id

    if (!currentSessionId) {
      throw new Error('No active session');
    }

    try {
      const response = await axios.post(`${config.ampecoApiUrl}/session/${currentSessionId}/end`);
      return response.data.data
    } catch (error) {
      throw new Error(`Failed to stop charging. ${error.message}`);
    }
  }
}

export default Charger;
