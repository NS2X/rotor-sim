"""
rotor-sim.py
https://github.com/sam210723/rotor-sim

Antenna rotor simulator for testing rotor driver software
"""

import argparse

argparser = argparse.ArgumentParser(description="Antenna rotor simulator for testing rotor driver software")
argparser.add_argument("-p", action="store", help="Rotor protocol (Easycomm/GS-232/SPID), default Easycomm", default="Easycomm")
argparser.add_argument("-ar", action="store", help="Azimuth rate (deg/second), default 5", default=5)
argparser.add_argument("-er", action="store", help="Elevation rate (deg/second), default 5", default=5)
args = argparser.parse_args()

ver = 1.0


def init():
    print("Rotor Sim v{0}".format(ver))


init()
