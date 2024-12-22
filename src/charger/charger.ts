import axios from "axios";
import config from "../config.js";

class Charger {
  private static instance: Charger;
  chargerId: string;
  evseId: number;
  activeSessionId?: number;

  private constructor(chargerId: string, evseId: number, activeSessionId?: number) {
    this.chargerId = chargerId;
    this.evseId = evseId;
    this.activeSessionId = activeSessionId;
  }

  static async getInstance(): Promise<Charger> {
    if (!Charger.instance) {
      const response = await axios.get(`${config.ampecoApiUrl}/personal/charge-points`);

      const chargerData = response.data.data[0];

      const chargePointData = chargerData;
      Charger.instance = new Charger(chargePointData.id, chargePointData.evses[0].id, chargePointData.evses[0].session?.id);
    }
    return Charger.instance;
  }

  public async checkSessionStatus() {
    try {
      const response = await axios.get(`${config.ampecoApiUrl}/personal/charge-points/${this.chargerId}`);
      const currentSessionId = response?.data?.data?.evses[0]?.session?.id;

      if (this.activeSessionId && !currentSessionId) {
        console.info('Charging session stopped externally');
        this.activeSessionId = undefined;
      } else if (!this.activeSessionId && currentSessionId) {
        console.info('Charging session started externally');
        this.activeSessionId = currentSessionId;
      }
    } catch (error) {
      console.error('Error during session status check:', error);
    }
  }

  startPeriodicCheck() {
    // Utfør en umiddelbar sjekk ved oppstart
    this.checkSessionStatus();

    // Sett opp et intervall for periodiske sjekker
    setInterval(async () => {
      await this.checkSessionStatus();
    }, config.pollingInterval); // Sjekk hvert minutt (60000 ms)
  }

  public async get() {
    const response = await axios.get(`${config.ampecoApiUrl}/personal/charge-points/${this.chargerId}`);

    return response.data;
  }

  public async startCharging() {
    const response = await axios.post(`${config.ampecoApiUrl}/session/start`, {
      evseId: this.evseId
    });
    this.activeSessionId = response.data.session.id;

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
      this.activeSessionId = undefined;
      return response.data.data
    } catch (error) {
      throw new Error(`Failed to stop charging. ${error.message}`);
    }
  }
}

export default Charger;
