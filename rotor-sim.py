"""
rotor-sim.py
https://github.com/sam210723/rotor-sim

Antenna rotor simulator for testing rotor driver software
"""

import argparse
import socket

argparser = argparse.ArgumentParser(description="Antenna rotor simulator for testing rotor driver software")
argparser.add_argument("-p", action="store", help="Socket listen port, default 4000", default=4000)
argparser.add_argument("-pr", action="store", help="Rotor protocol (Easycomm/GS-232/SPID), default Easycomm", default="Easycomm")
argparser.add_argument("-ar", action="store", help="Azimuth rate (deg/second), default 5", default=5)
argparser.add_argument("-er", action="store", help="Elevation rate (deg/second), default 5", default=5)
args = argparser.parse_args()

ver = 1.0
maxClients = 1
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)


def init():
    print("Rotor Sim v{}\n".format(ver))

    # Print argument info
    print("Protocol: {}\n".format(args.pr))
    print("Axis Rates:")
    print("  - Azimuth:   {}°/s".format(args.ar))
    print("  - Elevation: {}°/s\n".format(args.er))

    # Configure TCP socket
    server.bind(('0.0.0.0', int(args.p)))
    server.listen(maxClients)
    print("Listening on port {}\n".format(args.p))

    # Accept connections forever
    while True:
        client_socket, address = server.accept()
        print("Connection from {}".format(address[0]))

        # Handle each client socket connection
        try:
            while True:
                handle(client_socket)
        except ConnectionResetError as e:
            print("Connection to {} closed\n".format(address[0]))


# Handle client socket connection
def handle(client_socket):
    data = client_socket.recv(1024).decode("utf-8")

    if args.pr == "Easycomm":
        parseEasycomm(data, client_socket)


# EASYCOMM II Protocol parsing
def parseEasycomm(data, client_socket):
    # Tokenise (cmd always two characters)
    data = data.strip()
    cmd = data[0:2]
    if len(data) > 2:
        arg = data[2:]
    else:
        arg = ""

    if cmd == "AZ":
        print("[DRIVER] Move rotor azimuth to {}°".format(arg))
    elif cmd == "EL":
        print("[DRIVER] Move rotor elevation to {}°".format(arg))
    elif cmd == "UP":
        print("[DRIVER] Uplink is {} MHz".format(int(arg)/1000000))
    elif cmd == "DN":
        print("[DRIVER] Downlink is {} MHz".format(int(arg)/1000000))
    elif cmd == "UM":
        print("[DRIVER] Uplink mode is {}".format(arg))
    elif cmd == "DM":
        print("[DRIVER] Downlink mode is {}".format(arg))
    elif cmd == "UR":
        print("[DRIVER] Use uplink radio #{}".format(arg))
    elif cmd == "DR":
        print("[DRIVER] Use downlink radio #{}".format(arg))
    elif cmd == "ML":
        print("[DRIVER] Move rotor left")
    elif cmd == "MR":
        print("[DRIVER] Move rotor right")
    elif cmd == "MU":
        print("[DRIVER] Move rotor up")
    elif cmd == "MD":
        print("[DRIVER] Move rotor down")
    elif cmd == "SA":
        print("[DRIVER] Stop moving azimuth")
    elif cmd == "SE":
        print("[DRIVER] Stop moving elevation")
    elif cmd == "AO":
        print("[DRIVER] Target AOS notification")
    elif cmd == "LO":
        print("[DRIVER] Target LOS notification")
    elif cmd == "OP":
        print("[DRIVER] Set output {}".format(arg))
    elif cmd == "IP":
        print("[DRIVER] Read input {}".format(arg))
    elif cmd == "AN":
        print("[DRIVER] Read analog input {}".format(arg))
    elif cmd == "ST":
        print("[DRIVER] Set time to {}".format(arg))
    elif cmd == "VE":
        print("[DRIVER] Version request".format(arg))
    else:
        print("[DRIVER] UNRECOGNISED COMMAND: {} {}".format(cmd, arg))


def send(data, client_socket):
    client_socket.send(bytes(data, encoding="utf-8"))


init()
