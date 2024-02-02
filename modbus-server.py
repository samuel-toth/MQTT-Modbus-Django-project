import random
import threading
import time
import argparse
import signal
from pymodbus.datastore import ModbusSequentialDataBlock, ModbusServerContext, ModbusSlaveContext
from pymodbus.server import StartTcpServer

# Argument parsing for command line options
parser = argparse.ArgumentParser(description='Modbus server configuration.')
parser.add_argument('--host', type=str, default='localhost',
                    help='Host for the Modbus server, default is localhost')
parser.add_argument('--port', type=int, default=5020,
                    help='Port for the Modbus server, default is 5020')
args = parser.parse_args()

# Global variable to control the server running state
server_running = True


def setup_server_context():
    """
    Set up the server context for the Modbus server.

    Returns:
        ModbusServerContext: The server context with initialized slave context.
    """
    initial_values = [0] * 100
    datablock = ModbusSequentialDataBlock(0, initial_values)

    context = ModbusSlaveContext(
        di=datablock, co=datablock, hr=datablock, ir=datablock)
    return ModbusServerContext(slaves=context, single=True)


def update_registers(context):
    global server_running
    while server_running:
        address = 0
        value = [random.randint(0, 100) for _ in range(100)]
        context[0x01].setValues(3, address, value)
        time.sleep(10)


def signal_handler(sig, frame):
    global server_running
    print('Shutting down server...')
    server_running = False


def main():
    context = setup_server_context()

    update_thread = threading.Thread(target=update_registers, args=(context,))
    update_thread.start()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        print(f"Starting Modbus server at {args.host}:{args.port}")
        print("Press Ctrl+C to stop the server")
        StartTcpServer(context=context, address=(
            args.host, args.port), broadcast_enable=True)
    finally:
        global server_running
        server_running = False
        update_thread.join()


if __name__ == '__main__':
    main()
