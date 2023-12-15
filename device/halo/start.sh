#!/bin/bash

# --- move into current directory
cd /home/pi/lattice/device/halo

# --- step into virtual env
source .venv/bin/activate

# --- start 
python -u /home/pi/lattice/device/halo/main.py
