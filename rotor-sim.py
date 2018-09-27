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
    data = client_socket.recv(1024)
    print(data)


init()
