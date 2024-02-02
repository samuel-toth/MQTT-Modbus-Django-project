import argparse
import random
import paho.mqtt.client as mqtt
import time
import json
import requests
import os
from dotenv import load_dotenv
import logging

load_dotenv()

# MQTT Parameters
MQTT_USERNAME = os.getenv("MQTT_USERNAME")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD")


class MQTTCryptoClient:

    def __init__(self, broker, port, username, password, data_topic, command_topic):
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

        self.data_topic = data_topic + "/" + self.client._client_id.decode()
        self.command_topic = command_topic + "/" + self.client._client_id.decode()

        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

        logging.info("MQTT client initialized with ID `%s`" %
                     self.client._client_id.decode())

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            logging.info("Connected to broker `%s`" % self.broker)
            self.client.subscribe(self.command_topic)
        else:
            logging.error("Failed to connect with error: %s" % rc)

    def on_message(self, client, userdata, msg):

        logging.info("Received command `%s`" % msg.payload.decode()
                     )
        if msg.payload.decode() == "start":
            logging.info("Starting client via command")
            self.running = True
        elif msg.payload.decode() == "stop":
            logging.info("Stopping client via command")
            self.running = False
        elif msg.payload.decode() == "start_publish":
            logging.info("Starting publishing via command")
            self.publishing = True
        elif msg.payload.decode() == "stop_publish":
            logging.info("Stopping publishing via command")
            self.publishing = False
        else:
            logging.error("Invalid command `%s`" % msg.payload.decode())

    def run(self):
        self.client.connect(self.broker, self.port)
        self.client.loop_start()
        logging.info("Client loop started")
        try:
            while self.running:
                if self.publishing:
                    self.publish_data()
                time.sleep(120)
        except KeyboardInterrupt:
            logging.info("Client interrupted by keyboard")
        finally:
            self.loop_stop()
            self.client.disconnect()

    def publish_data(self):
        try:
            data = self.fetch_data()
            if data:
                self.client.publish(
                    self.data_topic, json.dumps(data))
                logging.info("Published data to topic `%s`" % self.data_topic)
        except Exception as e:
            logging.error("Failed to publish data with error: %s" % e)

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
            logging.error("Failed to fetch data with error: %s" % e)
            return None


if __name__ == '__main__':

    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s')

    parser = argparse.ArgumentParser(description="MQTT Crypto Client")
    parser.add_argument("--broker", type=str, default="localhost",
                        help="The MQTT broker address, default is localhost")
    parser.add_argument("--port", type=int, default=1883,
                        help="The MQTT broker port, default is 1883")
    parser.add_argument("--topic", type=str, default="crypto/data",
                        help="The MQTT topic to publish data, default is crypto/data")
    parser.add_argument("--command", type=str, default="crypto/command",
                        help="The MQTT topic to receive commands, default is crypto/command")
    args = parser.parse_args()

    client = MQTTCryptoClient(args.broker, args.port, MQTT_USERNAME,
                              MQTT_PASSWORD, args.topic, args.command)
    client.run()
