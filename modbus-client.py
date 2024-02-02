import time
import os
import argparse
from pymodbus import ModbusException
from pymodbus.client import ModbusTcpClient
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

load_dotenv()


# Argument parsing for command line options
parser = argparse.ArgumentParser(
    description="Modbus to MongoDB data transfer configuration.")
parser.add_argument("--modbus_host", type=str, default=os.getenv(
    "MODBUS_HOST", "localhost"), help="Host for the Modbus server")
parser.add_argument("--modbus_port", type=int, default=int(
    os.getenv("MODBUS_PORT", 5020)), help="Port for the Modbus server")
parser.add_argument("--mongo_host", type=str, default=os.getenv("MONGO_HOST",
                    "localhost"), help="Host for the MongoDB server")
parser.add_argument("--mongo_port", type=int, default=int(
    os.getenv("MONGO_PORT", 27017)), help="Port for the MongoDB server")
args = parser.parse_args()


def connect_to_modbus(host, port):
    """
    Connects to a Modbus server.

    Args:
        host (str): The IP address or hostname of the Modbus server.
        port (int): The port number of the Modbus server.

    Returns:
        ModbusTcpClient: The connected Modbus client object, or None if the connection failed.
    """
    try:
        client = ModbusTcpClient(host, port)
        if client.connect():
            return client
    except ModbusException as e:
        print(f"Modbus connection error: {e}")
        return None


def connect_to_mongodb(host, port):
    """
    Connects to MongoDB server.

    Args:
        host (str): The MongoDB server host.
        port (int): The MongoDB server port.

    Returns:
        MongoClient: The MongoDB client object if the connection is successful, None otherwise.
    """
    try:
        client = MongoClient(host, port)
        return client
    except ConnectionFailure as e:
        print(f"MongoDB connection error: {e}")
        return None


def read_and_store_data(client, mongo_collection):
    """
    Reads data from a Modbus client and stores it in a MongoDB collection.

    Args:
        client (ModbusClient): The Modbus client used to read data.
        mongo_collection (pymongo.collection.Collection): The MongoDB collection to store the data.

    Raises:
        KeyboardInterrupt: If the data collection is interrupted by the user.
        Exception: If an error occurs during data collection.

    """
    try:
        while True:
            response = client.read_holding_registers(
                address=0, count=100, slave=0x01)
            if not response.isError():
                value = response.registers
                print(f"Read value: {value}")
                data = {"value": value}
                mongo_collection.insert_one(data)
            else:
                print("Error reading register")
            time.sleep(10)
    except KeyboardInterrupt:
        print("Stopping data collection...")
    except Exception as e:
        print(f"Error during data collection: {e}")


def main():
    modbus_client = connect_to_modbus(args.modbus_host, args.modbus_port)
    if modbus_client is None:
        return

    mongo_client = connect_to_mongodb(args.mongo_host, args.mongo_port)
    if mongo_client is None:
        modbus_client.close()
        return

    db = mongo_client.modbus
    collection = db.data

    read_and_store_data(modbus_client, collection)

    modbus_client.close()
    mongo_client.close()


if __name__ == '__main__':
    main()
