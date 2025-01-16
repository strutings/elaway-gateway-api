#################################################################
# Dirty script to fetch current charging price and add          #
# start and stop buttons i Home Assistant                       #
#                                                               #
#    strutings@https://github.com/strutings/elaway-gateway-api/ #
#                                                               #
#################################################################

import requests
import json
import paho.mqtt.client as mqtt
import time

#@pyscript_compile
# MQTT Configuration
MQTT_BROKER = "10.0.0.186"
MQTT_PORT = 1883
MQTT_USER = "" 
MQTT_PASSWORD = "" 
MQTT_TOPIC_SENSOR = "homeassistant/sensor/charger/pricePerKwh"
MQTT_TOPIC_SESSIONENERGY = "homeassistant/sensor/charger/sessionenergy"
MQTT_TOPIC_BUTTON_START = "homeassistant/button/charger/start"
MQTT_TOPIC_BUTTON_STOP = "homeassistant/button/charger/stop"
MQTT_TOPIC_SESSIONPOWER = "homeassistant/sensor/charger/sessionpower"
MQTT_TOPIC_FIXEDFEE = "homeassistant/sensor/charger/markupFixedFeePerKwh"
MQTT_TOPIC_SESSIONTOTAL = "homeassistant/sensor/charger/totalAmount"
MQTT_TOPIC_TIMESTARTED = "homeassistant/sensor/charger/startedAt"
MQTT_TOPIC_TARIFF = "homeassistant/sensor/charger/tariff"
MQTT_TOPIC_MONTHENERGY = "homeassistant/sensor/charger/monthenergy"
MQTT_TOPIC_BINARY_SENSOR_STATUS = "homeassistant/binary_sensor/charger/available"


# Charger API
CHARGER_API_URL = "http://10.0.0.186:4000/charger"
CHARGER_START_URL = "http://10.0.0.186:4000/charger/start"
CHARGER_STOP_URL = "http://10.0.0.186:4000/charger/stop"

# MQTT Client Setup
client = mqtt.Client()
client.username_pw_set(MQTT_USER, MQTT_PASSWORD)


def on_connect(client, userdata, flags, rc):
#    print(f"Connected with result code {rc}")
    # Subscribe to switch topics to listen for commands
    client.subscribe(MQTT_TOPIC_BUTTON_START)
    client.subscribe(MQTT_TOPIC_BUTTON_STOP)

def on_message(client, userdata, msg):
    if msg.topic == MQTT_TOPIC_BUTTON_START:
        requests.post(CHARGER_START_URL)
    elif msg.topic == MQTT_TOPIC_BUTTON_STOP:
        requests.post(CHARGER_STOP_URL)


client.on_connect = on_connect
client.on_message = on_message
client.connect(MQTT_BROKER, MQTT_PORT, 60)

# Home Assistant MQTT Discovery
def publish_discovery():
    sensor_config = {
        "name": "Elaway Charger Price Per Kwh",
        "state_topic": f"{MQTT_TOPIC_SENSOR}/state",
        "unit_of_measurement": "NOK/kWh",
        "device_class": "monetary"
    }
    fixedfee_config = {
        "name": "Elaway Charger Fixed fee per Kwh",
        "state_topic": f"{MQTT_TOPIC_FIXEDFEE}/state",
        "unit_of_measurement": "NOK/kWh",
        "device_class": "monetary"
    }
    sessionenergy_config = {
        "name": "Elaway Current session energy",
        "state_topic": f"{MQTT_TOPIC_SESSIONENERGY}/state",
        "unit_of_measurement": "Wh",
        "device_class": "energy_storage"
    }
    sessionpower_config = {
        "name": "Elaway Current session Power",
        "state_topic": f"{MQTT_TOPIC_SESSIONPOWER}/state",
        "unit_of_measurement": "W",
        "device_class": "energy"
    }
    sessiontotal_config = {
        "name": "Elaway Session total NOK",
        "state_topic": f"{MQTT_TOPIC_SESSIONTOTAL}/state",
        "unit_of_measurement": "NOK",
        "device_class": "monetary"
    }
    timestarted_config = {
        "name": "Elaway Session start",
        "state_topic": f"{MQTT_TOPIC_TIMESTARTED}/state",
    }
    tariff_config = {
        "name": "Elaway tariff",
        "state_topic": f"{MQTT_TOPIC_TARIFF}/state",
    }
    monthenergy_config = {
        "name": "Elaway Monthly Energy",
        "state_topic": f"{MQTT_TOPIC_MONTHENERGY}/state",
        "unit_of_measurement": "kWh",
        "device_class": "energy"
    }
    available_config = {
        "name": "Elaway Charger Status",
        "state_topic": f"{MQTT_TOPIC_BINARY_SENSOR_STATUS}/state",
        "device_class": "connectivity"
    }

    client.publish(f"homeassistant/sensor/charger/config", json.dumps(sensor_config), retain=True)
    switch_start_config = {
        "name": "Start Elaway Charging",
        "command_topic": MQTT_TOPIC_BUTTON_START
    }
    client.publish(f"homeassistant/button/charger_start/config", json.dumps(switch_start_config), retain=True)

    switch_stop_config = {
        "name": "Stop Elaway Charging",
        "command_topic": MQTT_TOPIC_BUTTON_STOP
    }
    client.publish(f"homeassistant/button/charger_stop/config", json.dumps(switch_stop_config), retain=True)    
    client.publish(f"homeassistant/sensor/charger/fixedfee/config", json.dumps(fixedfee_config), retain=True)
    client.publish(f"homeassistant/sensor/charger/sessionenergy/config", json.dumps(sessionenergy_config), retain=True)    
    client.publish(f"homeassistant/sensor/charger/sessionpower/config", json.dumps(sessionpower_config), retain=True)
    client.publish(f"homeassistant/sensor/charger/sessiontotal/config", json.dumps(sessiontotal_config), retain=True)
    client.publish(f"homeassistant/sensor/charger/timestarted/config", json.dumps(timestarted_config), retain=True)
    client.publish(f"homeassistant/sensor/charger/tariff/config", json.dumps(tariff_config), retain=True)
    client.publish(f"homeassistant/sensor/charger/monthenergy/config", json.dumps(monthenergy_config), retain=True)
    client.publish(f"homeassistant/binary_sensor/charger/available/config", json.dumps(available_config), retain=True)

# Fetch and Publish Charger Data
def fetch_and_publish():
  try:
    response = requests.get(CHARGER_API_URL)
    data = response.json()
    price_per_kwh = data['data']['evses'][0]['tariff']['pricing']['pricePerKwh']
    client.publish(f"{MQTT_TOPIC_SENSOR}/state", price_per_kwh)
  except requests.exceptions.RequestException as e:
    print(f"Error fetching data: {e}")
    return None
  try:
    response = requests.get(CHARGER_API_URL)
    data = response.json()
    fixedfee = data['data']['evses'][0]['tariff']['pricing']['markupFixedFeePerKwh']
    client.publish(f"{MQTT_TOPIC_FIXEDFEE}/state", fixedfee)
  except requests.exceptions.RequestException as e:
    print(f"Error fetching data: {e}")
    return None
  try:
    response = requests.get(CHARGER_API_URL)
    data = response.json()
    sessionenergy = data['data']['evses'][0]['session']['energy']
    client.publish(f"{MQTT_TOPIC_SESSIONENERGY}/state", sessionenergy)
  except KeyError:
    client.publish(f"{MQTT_TOPIC_SESSIONENERGY}/state", "0")

  try:
    response = requests.get(CHARGER_API_URL)
    data = response.json()
    sessionpower = data['data']['evses'][0]['session']['power']
    client.publish(f"{MQTT_TOPIC_SESSIONPOWER}/state", sessionpower)
  except KeyError:
    client.publish(f"{MQTT_TOPIC_SESSIONPOWER}/state", "0")
  try:
    response = requests.get(CHARGER_API_URL)
    data = response.json()
    session_total_kwh = data['data']['evses'][0]['session']['totalAmount']
    client.publish(f"{MQTT_TOPIC_SESSIONTOTAL}/state", session_total_kwh)
  except KeyError:
    client.publish(f"{MQTT_TOPIC_SESSIONTOTAL}/state", "0")
  try:
    response = requests.get(CHARGER_API_URL)
    data = response.json()
    time_started = data['data']['evses'][0]['session']['startedAt']
    client.publish(f"{MQTT_TOPIC_TIMESTARTED}/state", time_started)
  except KeyError:
    client.publish(f"{MQTT_TOPIC_TIMESTARTED}/state", "not_started")
  try:
    response = requests.get(CHARGER_API_URL)
    data = response.json()
    tariff = data['data']['evses'][0]['tariff']['name']
    client.publish(f"{MQTT_TOPIC_TARIFF}/state", tariff)
  except requests.exceptions.RequestException as e:
    print(f"Error fetching data: {e}")
    return None
  try:
    response = requests.get(CHARGER_API_URL)
    data = response.json()
    monthenergy = data['data']['last_month_energy_kwh']
    client.publish(f"{MQTT_TOPIC_MONTHENERGY}/state", monthenergy)
  except requests.exceptions.RequestException as e:
    print(f"Error fetching data: {e}")
    return None
  try:
    response = requests.get(CHARGER_API_URL)
    data = response.json()
    status = data['data']['status']
    if status == 'available':
      payload = 'online'
    else:
      payload = 'offline'
    client.publish(f"{MQTT_TOPIC_BINARY_SENSOR_STATUS}/state", payload)
  except requests.exceptions.RequestException as e:
    return None


#    if data.get('status') == 'available':


publish_discovery()

# Main Loop
client.loop_start()
try:
    while True:
        fetch_and_publish()
        time.sleep(60)  # Fetch data every 5 minutes
except KeyboardInterrupt:
    client.loop_stop()
    client.disconnect()
