import axios from "axios";

class Charger {
  private static instance: Charger;
  chargerId: string;
  evseId: number;
  activeSessionId?: string;

  private constructor(chargerId: string, evseId: number) {
    this.chargerId = chargerId;
    this.evseId = evseId;
  }

  static async getInstance(): Promise<Charger> {
    if (!Charger.instance) {
      const response = await axios.get("https://no.eu-elaway.charge.ampeco.tech/api/v1/app/personal/charge-points");

      const chargerData = response.data.data[0];

      const chargePointData = chargerData;
      Charger.instance = new Charger(chargePointData.id, chargePointData.evses[0].id);
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
    this.activeSessionId = response.data.data.id;

    return response
  }

  public async stopCharging() {
    const response = await axios.post(`https://no.eu-elaway.charge.ampeco.tech/api/v1/app/session/${this.activeSessionId}/end`, {
      evseId: this.evseId
    });
    return response
  }
}

export default Charger;
