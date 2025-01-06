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

# MQTT Configuration
MQTT_BROKER = ""
MQTT_PORT = 1883
MQTT_USER = "" 
MQTT_PASSWORD = "" 
MQTT_TOPIC_SENSOR = "homeassistant/sensor/charger/pricePerKwh"
MQTT_TOPIC_BUTTON_START = "homeassistant/button/charger/start"
MQTT_TOPIC_BUTTON_STOP = "homeassistant/button/charger/stop"

# Charger API
CHARGER_API_URL = "http://URL:PORT/charger"
CHARGER_START_URL = "http://URL:PORT/charger/start"
CHARGER_STOP_URL = "http://URL:PORT/charger/stop"

# MQTT Client Setup
client = mqtt.Client()
client.username_pw_set(MQTT_USER, MQTT_PASSWORD)

def on_connect(client, userdata, flags, rc):
    print(f"Connected with result code {rc}")
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
        "name": "Elway Charger Price Per Kwh",
        "state_topic": f"{MQTT_TOPIC_SENSOR}/state",
        "unit_of_measurement": "NOK/kWh",
        "device_class": "monetary"
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

# Fetch and Publish Charger Data
def fetch_and_publish():
    response = requests.get(CHARGER_API_URL)
    data = response.json()
    price_per_kwh = data['data']['evses'][0]['tariff']['pricing']['pricePerKwh']
    client.publish(f"{MQTT_TOPIC_SENSOR}/state", price_per_kwh)

publish_discovery()

# Main Loop
client.loop_start()
try:
    while True:
        fetch_and_publish()
        time.sleep(300)  # Fetch data every 5 minutes
except KeyboardInterrupt:
    client.loop_stop()
    client.disconnect()
#
#
#### Notes:
