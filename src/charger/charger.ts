import axios from "axios";

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
      const response = await axios.get("https://no.eu-elaway.charge.ampeco.tech/api/v1/app/personal/charge-points");

      const chargerData = response.data.data[0];

      const chargePointData = chargerData;
      Charger.instance = new Charger(chargePointData.id, chargePointData.evses[0].id, chargePointData.evses[0].session?.id);
    }
    return Charger.instance;
  }

  public async get() {
    const response = await axios.get(`https://no.eu-elaway.charge.ampeco.tech/api/v1/app/personal/charge-points/${this.chargerId}`);

    return response.data;
  }

  public async startCharging() {
    const response = await axios.post('https://no.eu-elaway.charge.ampeco.tech/api/v1/app/session/start', {
      evseId: this.evseId
    });
    this.activeSessionId = response.data.session.id;

    return response.data.session
  }

  public async stopCharging() {
    const charger = await axios.get('https://no.eu-elaway.charge.ampeco.tech/api/v1/app/personal/charge-points');
    const currentSessionId = charger?.data?.data[0]?.evses[0]?.session?.id

    if (!currentSessionId) {
      throw new Error('No active session');
    }

    const response = await axios.post(`https://no.eu-elaway.charge.ampeco.tech/api/v1/app/session/${currentSessionId}/end`);
    return response.data.data
  }
}

export default Charger;
