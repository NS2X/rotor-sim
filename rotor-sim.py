"""
rotor-sim.py
https://github.com/sam210723/rotor-sim

Antenna rotor simulator for testing rotor driver software
"""

import argparse
from colorama import init as colorinit
import socket
import threading

argparser = argparse.ArgumentParser(description="Antenna rotor simulator for testing rotor driver software")
argparser.add_argument("-p", action="store", help="Socket listen port, default 4000", default=4000)
argparser.add_argument("-pr", action="store", help="Rotor protocol (EASYCOMM/GS-232/SPID), default EASYCOMM", default="EASYCOMM")
argparser.add_argument("-ar", action="store", help="Azimuth rate (deg/second), default 5", default=5)
argparser.add_argument("-er", action="store", help="Elevation rate (deg/second), default 5", default=5)
argparser.add_argument("-fi", action="store", help="rotor position feedback interval (milliseconds), default 250", default=250)
args = argparser.parse_args()

ver = 1.0
maxClients = 1
termx = 80
termy = 20
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

az = 0.0
el = 0.0
taz = 0.0
tel = 0.0


def init():
    # Initialise Colorama module
    colorinit()

    # Build UI elements
    build_interface()
    print_at("", termx, termy)
    return

    # Initialise feedback thread variable
    fbThread = None

    # Configure TCP socket
    server.bind(('0.0.0.0', int(args.p)))
    server.listen(maxClients)
    print("Listening on port {}\n".format(args.p))

    # Accept connections forever
    while True:
        client_socket, address = server.accept()
        print("Connection from {}\n".format(address[0]))

        # Handle each client socket connection
        try:
            while True:
                handle(client_socket)

                # Start feedback thread
                if fbThread is None:
                    fbThread = threading.Thread(target=set_interval, args=(feedback, client_socket, int(args.fi) / 1000))
                    fbThread.start()
        except ConnectionResetError as e:
            print("Connection to {} closed\n".format(address[0]))


# Handle client socket connection
def handle(client_socket):
    data = client_socket.recv(1024).decode("utf-8")

    if args.pr == "EASYCOMM":
        parse_easycomm(data, client_socket)


# EASYCOMM II Protocol parsing
def parse_easycomm(data, client_socket):
    # Tokenise (cmd always two characters)
    data = data.strip()
    cmd = data[0:2]
    if len(data) > 2:
        arg = data[2:]
    else:
        arg = ""

    # Switch command type
    if cmd == "AZ":
        print("[DRIVER] Move rotor azimuth to {}°\n".format(arg))
        taz = float(arg)
    elif cmd == "EL":
        print("[DRIVER] Move rotor elevation to {}°\n".format(arg))
        tel = float(arg)
    elif cmd == "UP":
        print("[DRIVER] Uplink is {} MHz\n".format(int(arg)/1000000))
    elif cmd == "DN":
        print("[DRIVER] Downlink is {} MHz\n".format(int(arg)/1000000))
    elif cmd == "UM":
        print("[DRIVER] Uplink mode is {}\n".format(arg))
    elif cmd == "DM":
        print("[DRIVER] Downlink mode is {}\n".format(arg))
    elif cmd == "UR":
        print("[DRIVER] Use uplink radio #{}\n".format(arg))
    elif cmd == "DR":
        print("[DRIVER] Use downlink radio #{}\n".format(arg))
    elif cmd == "ML":
        print("[DRIVER] Move rotor left\n")
    elif cmd == "MR":
        print("[DRIVER] Move rotor right\n")
    elif cmd == "MU":
        print("[DRIVER] Move rotor up\n")
    elif cmd == "MD":
        print("[DRIVER] Move rotor down\n")
    elif cmd == "SA":
        print("[DRIVER] Stop moving azimuth\n")
    elif cmd == "SE":
        print("[DRIVER] Stop moving elevation\n")
    elif cmd == "AO":
        print("[DRIVER] Target AOS notification\n")
    elif cmd == "LO":
        print("[DRIVER] Target LOS notification\n")
    elif cmd == "OP":
        print("[DRIVER] Set output {}\n".format(arg))
    elif cmd == "IP":
        print("[DRIVER] Read input {}\n".format(arg))
    elif cmd == "AN":
        print("[DRIVER] Read analog input {}\n".format(arg))
    elif cmd == "ST":
        print("[DRIVER] Set time to {}\n".format(arg))
    elif cmd == "VE":
        print("[DRIVER] Version request".format(arg))

        send("VE{}\n".format(ver), client_socket)
        print("[ROTSIM] Version is {}\n".format(ver))
    else:
        print("[DRIVER] UNRECOGNISED COMMAND: {} {}\n".format(cmd, arg))


# Send position feedback data
def feedback(client_socket):
    if args.pr == "Easycomm":
        send("AZ{}\n".format(az), client_socket)
        send("EL{}\n".format(az), client_socket)
        print_at("Target Azimuth: {}".format(taz), 3, 4)
        print("[ROTSIM] AZ: {} ({})   EL: {} ({})".format(az, taz, el, tel))


def build_interface():
    # Top border
    print("┌", end="")
    for i in range(termx-2):
        print("─", end="")
    print("┐")

    # Side borders
    for i in range(termy-1):
        print("│", end="")
        for j in range(termx - 2):
            print(" ", end="")
        print("│")

    # Bottom border
    print_at("└", 1, termy)
    for i in range(termx - 2):
        print("─", end="")
    print("┘", end="")

    # Header border
    print_at("├", 1, 3)
    for i in range(termx - 2):
        print_at("─", i+2, 3)
    print_at("┤", termx, 3)

    # Header
    header = "Rotor Simulator v{}  •  github.com/sam210723/rotor-sim".format(ver)
    headerPos = (termx / 2) - (len(header) / 2)
    print_at(header, int(headerPos), 2)

    # Center divider
    print_at("┬", int(termx / 2), 3)
    for i in range(termy-4):
        print_at("│", int(termx / 2), i+4)
    print_at("┴", int(termx / 2), termy)

    # Initial readouts
    print_at("AZIMUTH:", 3, 4)
    print_at("ELEVATION:", 3, 5)
    print_at("TARGET AZIMUTH:", 3, 6)
    print_at("TARGET ELEVATION:", 3, 7)


# Send data to client
def send(data, client_socket):
    client_socket.send(bytes(data, encoding="utf-8"))


# Call function at regular interval
def set_interval(func, arg, time):
    e = threading.Event()
    while not e.wait(time):
        func(arg)


# Print string at coordinate
def print_at(s, x, y):
    print("\033[" + str(y) + ";" + str(x) + "H" + s, end="")


init()
