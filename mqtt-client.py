import random
import paho.mqtt.client as mqtt
import time
import json
import requests
import os
from dotenv import load_dotenv


class MQTTCryptoClient:

    def __init__(self, broker, port, username, password, publish_topic, command_topic):
        self.broker = broker
        self.port = port
        self.username = username
        self.password = password
        self.client = mqtt.Client("cryptodev" +
                                  time.strftime("%H%M") + str(random.randint(0, 1000)).zfill(4))
        self.client.username_pw_set(
            username=self.username, password=self.password)
        self.running = True
        self.publishing = True

        self.publish_topic = publish_topic + "/" + self.client._client_id.decode()
        self.command_topic = command_topic + "/" + self.client._client_id.decode()

        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

        print("MQTT client initialized with ID: " +
              self.client._client_id.decode())

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("Connection to broker successful")
            self.client.subscribe(self.command_topic)
        else:
            print(f"Connection to broker failed, return code {rc}")

    def on_message(self, client, userdata, msg):
        print("Received command `%s`" % msg.payload.decode() +
              " at " + time.strftime("%H:%M:%S", time.localtime()))
        print(msg.payload.decode())
        if msg.payload.decode() == "start":
            print("Starting client...")
            self.running = True
        elif msg.payload.decode() == "stop":
            print("Stopping client...")
            self.running = False
        elif msg.payload.decode() == "start_publish":
            print("Starting publishing...")
            self.publishing = True
        elif msg.payload.decode() == "stop_publish":
            print("Stopping publishing...")
            self.publishing = False
        else:
            print("Unknown command received")

    def run(self):
        """
        Runs the MQTT client.

        Connects to the broker, starts the client loop, and continuously publishes data if enabled.
        The client runs until interrupted by a keyboard interrupt or stopped by a command. 
        """
        self.client.connect(self.broker, self.port)
        self.client.loop_start()
        print("Running client...")
        try:
            while self.running:
                if self.publishing:
                    self.publish_data()
                time.sleep(120)
        except KeyboardInterrupt:
            print("Exiting...")
        finally:
            self.loop_stop()
            self.client.disconnect()

    def publish_data(self):
        """
        Publishes cryptocurrency data to the MQTT broker.

        Args:
            client (mqtt.Client): The MQTT client object.
        """
        try:
            data = self.fetch_data()
            if data:
                self.client.publish(
                    self.publish_topic, json.dumps(data))
                print("Published data to topic `%s`" % self.publish_topic +
                      " at " + time.strftime("%H:%M:%S", time.localtime()))
        except Exception as e:
            print("Publishing failed with error: %s" % e)

    def fetch_data(self):
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
            response = requests.get(
                "https://api.coincap.io/v2/assets?limit=10")
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


load_dotenv()

# MQTT Parameters
MQTT_BROKER = os.getenv("MQTT_BROKER")
MQTT_PORT = int(os.getenv("MQTT_PORT"))
MQTT_PUBLISH_TOPIC = os.getenv("MQTT_PUBLISH_TOPIC")
MQTT_COMMAND_TOPIC = os.getenv("MQTT_COMMAND_TOPIC")
MQTT_USERNAME = os.getenv("MQTT_USERNAME")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD")


if __name__ == '__main__':
    client = MQTTCryptoClient(MQTT_BROKER, MQTT_PORT, MQTT_USERNAME,
                              MQTT_PASSWORD, MQTT_PUBLISH_TOPIC, MQTT_COMMAND_TOPIC)
    client.run()
