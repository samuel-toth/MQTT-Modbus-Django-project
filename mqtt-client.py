import paho.mqtt.client as mqtt
import time
import json
import requests
import os
from dotenv import load_dotenv

load_dotenv()

# CoinCap API Parameters
CC_API_URL = "https://api.coincap.io/v2/assets?limit=10"

# MQTT Parameters
MQTT_BROKER = os.getenv("MQTT_BROKER")
MQTT_PORT = int(os.getenv("MQTT_PORT"))
MQTT_TOPIC = os.getenv("MQTT_TOPIC")
MQTT_USERNAME = os.getenv("MQTT_USERNAME")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD")
MQTT_CLIENT_ID = os.getenv("MQTT_CLIENT_ID")


def fetch_data():
    """
    Fetches the top 10 cryptocurrency data from the CoinCap API.

    Returns:
        dict: A dictionary containing the timestamp and a list of cryptocurrencies,
              each with id, symbol, and USD price. The dictionary has the following structure:
            {
                'timestamp': <timestamp>,
                'crypto': [
                    {
                        'id': <id>,
                        'symbol': <symbol>,
                        'priceUsd': <priceUsd>
                    },
                    ...
                ]
            }
    """
    try:
        response = requests.get(CC_API_URL)
        data = response.json()
        timestamp = data.get("timestamp")
        cryptos = [
            {'id': item['id'], 'symbol': item['symbol'],
                'priceUsd': item['priceUsd']}
            for item in data.get("data", [])
        ]
        return {'timestamp': timestamp, 'crypto': cryptos}
    except requests.RequestException as e:
        print(f"Failed to fetch data with error: {e}")


def connect_mqtt():
    """
    Establishes connection to the MQTT broker.

    Returns:
        mqtt.Client: An instance of the MQTT client.
    """
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT Broker!")
        else:
            print(f"Failed to connect, return code {rc}")

    client = mqtt.Client(MQTT_CLIENT_ID)
    client.username_pw_set(username=MQTT_USERNAME, password=MQTT_PASSWORD)
    client.on_connect = on_connect
    client.connect(MQTT_BROKER, MQTT_PORT)

    return client


def publish_data(client):
    """
    Publishes cryptocurrency data to the MQTT broker.

    Args:
        client (mqtt.Client): The MQTT client object.
    """
    try:
        data = fetch_data()
        if data:
            client.publish(MQTT_TOPIC, json.dumps(data))
            print("Published data to topic `%s`" % MQTT_TOPIC +
                  " at " + time.strftime("%H:%M:%S", time.localtime()))
    except Exception as e:
        print("Publishing failed with error: %s" % e)


if __name__ == '__main__':

    client = connect_mqtt()
    client.loop_forever()

    try:
        while True:
            publish_data(client)
            time.sleep(120)
    except KeyboardInterrupt:
        client.loop_stop()
        print("Exiting...")
