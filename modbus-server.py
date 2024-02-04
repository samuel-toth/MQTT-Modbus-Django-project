import os
import ssl
import time
import logging
import argparse
from pymodbus import ModbusException
import requests
import threading

from pymodbus.server import StartTlsServer
from pymodbus.payload import BinaryPayloadBuilder, Endian
from pymodbus.datastore import (
    ModbusSequentialDataBlock,
    ModbusServerContext,
    ModbusSlaveContext,
)
from dotenv import load_dotenv

load_dotenv()


def setup_server_context():
    initial_values = [0]
    datablock = ModbusSequentialDataBlock(0, initial_values)

    slave_context = ModbusSlaveContext(
        di=datablock, co=datablock, hr=datablock, ir=datablock
    )
    return ModbusServerContext(slaves=slave_context, single=True)


def update_registers(context, interval):
    while True:
        address = 0x00
        price = fetch_data()

        builder = BinaryPayloadBuilder(byteorder=Endian.LITTLE)
        builder.add_32bit_float(float(price))
        payload = builder.to_registers()

        context[0x01].setValues(3, address, payload)
        logging.info(
            f"Updated register values at address {address} with payload {payload}"
        )
        time.sleep(interval)


def fetch_data():
    try:
        response = requests.get(os.getenv("COINCAP_API_URL") + "/bitcoin")
        data = response.json()
        price = data.get("data").get("priceUsd")
        return price
    except requests.RequestException as e:
        logging.error(f"Failed to fetch data with error: {e}")
        return None


if __name__ == "__main__":

    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )

    parser = argparse.ArgumentParser(
        description="Modbus server for fetching and storing Bitcoin price to registers"
    )
    parser.add_argument(
        "--host",
        type=str,
        default="localhost",
        help="Host for the Modbus server, default is localhost",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=5020,
        help="Port for the Modbus server, default is 5020",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=60,
        help="Interval in seconds to update register values, default is 60",
    )
    args = parser.parse_args()

    try:
        ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        ssl_context.load_cert_chain(
            certfile=os.getenv("MODBUS_SERVER_CERT_PATH"),
            keyfile=os.getenv("MODBUS_SERVER_KEY_PATH"),
        )
        context = setup_server_context()

        thread = threading.Thread(
            target=update_registers, args=(context, args.interval)
        )
        thread.start()

        StartTlsServer(
            context=context,
            identity=None,
            address=(args.host, args.port),
            sslctx=ssl_context,
        )

    except ModbusException as e:
        logging.error(f"Modbus error: {e}")
    except KeyboardInterrupt:
        logging.info(f"Modbus server stopped by user.")
        thread.join()
