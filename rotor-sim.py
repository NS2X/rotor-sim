"""
rotor-sim.py
https://github.com/sam210723/rotor-sim

Antenna rotor simulator for testing rotor driver software
"""

import argparse
from colorama import init as colorinit
from colorama import Fore, Back, Style
import cursor
import socket
from threading import Event, Thread
from queue import Queue

argparser = argparse.ArgumentParser(description="Antenna rotor simulator for testing rotor driver software")
argparser.add_argument("-p", action="store", help="Socket listen port, default 4000", default="4000")
argparser.add_argument("-pr", action="store", help="Rotor protocol (EASYCOMM/GS-232/SPID), default EASYCOMM", default="EASYCOMM")
argparser.add_argument("-ar", action="store", help="Azimuth rate (deg/second), default 5", default="5")
argparser.add_argument("-er", action="store", help="Elevation rate (deg/second), default 5", default="5")
argparser.add_argument("-fi", action="store", help="rotor position feedback interval (milliseconds), default 250", default="250")
args = argparser.parse_args()

ver = 1.0
maxClients = 1
termx = 80
termy = 16
dataColPos = int(termx / 2) - 1
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
logMsgs = []
tazq = Queue()
telq = Queue()
logClearStr = ""

az = 0.0
el = 0.0
taz = 0.0
tel = 0.0


def init():
    # Initialise Colorama module
    colorinit()

    # Tweak args
    args.pr = args.pr.upper()
    if args.pr == "EASYCOMM":
        args.pr = "EASYCOMM II"

    # Build UI elements
    build_interface()
    print_at("", termx, termy+1)

    # Initialise feedback thread variable
    fbThread = None

    # Configure TCP socket
    server.bind(('0.0.0.0', int(args.p)))
    server.listen(maxClients)
    text = "LISTENING"
    print_at(text, dataColPos - len(text), 10)

    # Accept connections forever
    try:
        while True:
            client_socket, address = server.accept()
            text = address[0]
            print_at(text, dataColPos - len(text), 10)

            # Handle each client socket connection
            try:
                while True:
                    handle(client_socket)

                    # Start feedback thread
                    if fbThread is None:
                        fbThread = Thread(target=set_interval, args=(feedback, client_socket, tazq, telq, int(args.fi) / 1000))
                        fbThread.start()
            except ConnectionResetError as e:
                text = "           LISTENING"
                print_at(text, dataColPos - len(text), 10)
    except KeyboardInterrupt:
        print_at("Exiting", 1, termy + 1)
        pass


# Handle client socket connection
def handle(client_socket):
    data = client_socket.recv(1024).decode("utf-8")

    if args.pr == "EASYCOMM II":
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
        log("[DRIVER] Move azimuth to {}°\n".format(arg))

        try:
            taz = float(arg)
            tazq.put(taz)
            text = "    " + str(taz) + "° "
            print_at(text, dataColPos - len(text) + 1, 5)
        except ValueError:
            pass
    elif cmd == "EL":
        log("[DRIVER] Move elevation to {}°\n".format(arg))

        try:
            tel = float(arg)
            telq.put(tel)
            text = "    " + str(tel) + "° "
            print_at(text, dataColPos - len(text) + 1, 7)
        except ValueError:
            pass
    elif cmd == "UP":
        log("[DRIVER] Uplink is {} MHz\n".format(int(arg)/1000000))
    elif cmd == "DN":
        log("[DRIVER] Downlink is {} MHz\n".format(int(arg)/1000000))
    elif cmd == "UM":
        log("[DRIVER] Uplink mode is {}\n".format(arg))
    elif cmd == "DM":
        log("[DRIVER] Downlink mode is {}\n".format(arg))
    elif cmd == "UR":
        log("[DRIVER] Use uplink radio #{}\n".format(arg))
    elif cmd == "DR":
        log("[DRIVER] Use downlink radio #{}\n".format(arg))
    elif cmd == "ML":
        log("[DRIVER] Move rotor left\n")
    elif cmd == "MR":
        log("[DRIVER] Move rotor right\n")
    elif cmd == "MU":
        log("[DRIVER] Move rotor up\n")
    elif cmd == "MD":
        log("[DRIVER] Move rotor down\n")
    elif cmd == "SA":
        log("[DRIVER] Stop moving azimuth\n")
    elif cmd == "SE":
        log("[DRIVER] Stop moving elevation\n")
    elif cmd == "AO":
        log("[DRIVER] Target AOS notification\n")
    elif cmd == "LO":
        log("[DRIVER] Target LOS notification\n")
    elif cmd == "OP":
        log("[DRIVER] Set output {}\n".format(arg))
    elif cmd == "IP":
        log("[DRIVER] Read input {}\n".format(arg))
    elif cmd == "AN":
        log("[DRIVER] Read analog input {}\n".format(arg))
    elif cmd == "ST":
        log("[DRIVER] Set time to {}\n".format(arg))
    elif cmd == "VE":
        log("[DRIVER] Version request".format(arg))

        send("VE{}\n".format(ver), client_socket)
        log("[ROTSIM] Version is {}\n".format(ver))
    else:
        log("[DRIVER] BAD COMMAND: {} {}\n".format(cmd, arg))


# Send position feedback data
def feedback(client_socket, tazq, telq):
    global az
    global el
    global taz
    global tel

    # Send target position cross-thread
    if not tazq.empty():
        taz = tazq.get()

    if not telq.empty():
        tel = telq.get()

    # No negative elevation
    if tel < 0:
        tel = 0.0

    azDiff = az - taz
    elDiff = el - tel
    fiSec = int(args.fi) / 1000
    azRate = float(args.ar) * fiSec
    elRate = float(args.er) * fiSec

    # Azimuth movement logic
    if abs(azDiff) < azRate:  # If rotor within rate to target
        az = taz  # Move to target
    else:
        # Determine if CW or CCW is shortest path to target
        if az < taz:
            if abs(az - taz) < 180:
                az += azRate
            else:
                az -= azRate
        else:
            if abs(az - taz) < 180:
                az -= azRate
            else:
                az += azRate

    # Shift azimuth by 360 if below 0
    az = az % 360
    if az < 0:
        az += 360

    # Elevation movement logic
    if abs(elDiff) < elRate:  # If rotor within rate to target
        el = tel  # Move to target
    elif el < tel:
        el += elRate
    elif el > tel:
        el -= elRate

    if args.pr == "EASYCOMM II":
        send("AZ{}\n".format(az), client_socket)
        send("EL{}\n".format(el), client_socket)

        text = "    " + str(az) + "° "
        print_at(text, dataColPos - len(text) + 1, 4)
        # log("[ROTSIM] Azimuth is {}\n".format(az))

        text = "    " + str(el) + "° "
        print_at(text, dataColPos - len(text) + 1, 6)
        # log("[ROTSIM] Elevation is {}\n".format(el))


# Build user interface
def build_interface():
    global logClearStr

    # Clear console
    print("\033[H\033[J")

    # Hide cursor
    cursor.hide()

    # Top border
    print_at("┌", 1, 1)
    for i in range(termx-2):
        print_at("─", i + 2, 1)
    print_at("┐", termx, 1)

    # Side borders
    for i in range(termy-1):
        print_at("│", 1, i + 2)
        for j in range(termx - 2):
            print(" ", end="")
        print_at("│", termx, i + 2)

    # Bottom border
    print_at("└", 1, termy)
    for i in range(termx - 2):
        print_at("─", i + 2, termy)
    print_at("┘", termx, termy)

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
    print_at(Fore.LIGHTGREEN_EX + "Azimuth:" + Style.RESET_ALL, 3, 4)
    text = str(az) + "°"
    print_at(text, dataColPos - len(text), 4)

    print_at(Fore.LIGHTGREEN_EX + "Target Azimuth:" + Style.RESET_ALL, 3, 5)
    text = "---°"
    print_at(text, dataColPos - len(text), 5)

    print_at(Fore.LIGHTGREEN_EX + "Elevation:" + Style.RESET_ALL, 3, 6)
    text = str(el) + "°"
    print_at(text, dataColPos - len(text), 6)

    print_at(Fore.LIGHTGREEN_EX + "Target Elevation:" + Style.RESET_ALL, 3, 7)
    text = "---°"
    print_at(text, dataColPos - len(text), 7)

    print_at(Fore.LIGHTGREEN_EX + "Socket status:" + Style.RESET_ALL, 3, 10)
    text = "NO CLIENT"
    print_at(text, dataColPos - len(text), 10)

    print_at(Fore.LIGHTGREEN_EX + "Socket listen port:" + Style.RESET_ALL, 3, 11)
    print_at(args.p, dataColPos-len(args.p), 11)

    print_at(Fore.LIGHTGREEN_EX + "Rotor protocol:" + Style.RESET_ALL, 3, 12)
    print_at(args.pr, dataColPos - len(args.pr), 12)

    print_at(Fore.LIGHTGREEN_EX + "Feedback interval:" + Style.RESET_ALL, 3, 13)
    text = args.fi + " ms"
    print_at(text, dataColPos - len(text), 13)

    print_at(Fore.LIGHTGREEN_EX + "Azimuth rate:" + Style.RESET_ALL, 3, 14)
    text = args.ar + "°/s"
    print_at(text, dataColPos - len(text), 14)

    print_at(Fore.LIGHTGREEN_EX + "Elevation rate:" + Style.RESET_ALL, 3, 15)
    text = args.er + "°/s"
    print_at(text, dataColPos - len(text), 15)

    # Create clearing string
    for j in range(termx - 42):
        logClearStr += " "


# Add message to log list
def log(message):
    global logClearStr
    logMsgs.append(message)
    logLen = len(logMsgs)
    maxLogLen = termy-4

    # Remove oldest log message if too long
    if len(logMsgs) > maxLogLen:
        del logMsgs[0]
        logLen -= 1

    # Clear line and write new message
    for i in range(logLen):
        print_at(logClearStr, 42, termy-1-i)
        print_at(Style.BRIGHT + logMsgs[logLen - i - 1] + Style.RESET_ALL, 42, termy-1-i)


# Send data to client
def send(data, client_socket):
    try:
        client_socket.send(bytes(data, encoding="utf-8"))
    except ConnectionResetError:
        pass


# Call function at regular interval
def set_interval(func, arg1, arg2, arg3, time):
    e = Event()
    while not e.wait(time):
        func(arg1, arg2, arg3)


# Print string at coordinate
def print_at(s, x, y):
    print("\033[" + str(y) + ";" + str(x) + "H", end="")
    print(s, end="")

    # Reset cursor
    #print("\033[" + str(termy+1) + ";" + str(1) + "H", end="")


init()
