#!/bin/bash

# --- cd to root
cd /home/pi/lattice/device/halo/
pwd

# --- step into virtual env
source .venv/bin/activate

# --- start 
python -u /home/pi/lattice/device/halo/main.py
