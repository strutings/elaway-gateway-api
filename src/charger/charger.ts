import config from '../config.js';
import axios from 'axios';

const chargerData = (await axios.get(`${config.ampecoApiUrl}/personal/charge-points`)).data.data[0];

const chargerInfo = {
  chargerId: chargerData.id,
  evseId: chargerData.evses[0].id
}

export { chargerInfo };
