#!/bin/bash


# DEVICE/STATS
# --- write out user running file for diagnosising cron/systemd issues
# whoami > /home/pi/lattice/device/halo/username.txt


# START
# --- cd to root
cd /home/pi/lattice/device/halo/

# --- step into virtual env
source .venv/bin/activate

# --- start 
# python -u /home/pi/lattice/device/halo/main.py
python /home/pi/lattice/device/halo/main.py
