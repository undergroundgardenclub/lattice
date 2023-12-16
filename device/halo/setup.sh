#!/bin/bash

# SETUP: initial app linux installs. Only should need to run once

# Virtual Env: required to not break RPi root packages. Need system site packages flag for camera lib issue https://github.com/raspberrypi/picamera2/issues/341#issuecomment-1268460969)
echo "[setup.sh] .venv"
python -m venv .venv --system-site-packages
source .venv/bin/activate

# LINUX
echo "[setup.sh] apt installs"
# --- dev/tools (needed for adafruit python pkgs)
sudo apt install -y python3-dev python3-setuptools
# --- camera
sudo apt install -y libpcap-dev
# --- audio (portaudio for pyaudio)
sudo apt install -y ffmpeg portaudio19-dev

# PYTHON
echo "[setup.sh] pip install"
# --- ensure we're in venv
source .venv/bin/activate
# --- install
pip install -r requirements.txt
