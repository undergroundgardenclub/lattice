#!/bin/bash

# NOT IN USE: Kept for reference if needed later
# Made this script to setup boot scripts/files. RUN WITH SUDO

# MANUAL TODOS
# --- disabling pulseaudio, which conflicts with pyaudio (https://learn.foundry.com/nuke/content/timeline_environment/managetimelines/audio_pulse.html)
echo "[setupd.sh] pulse audio config needs editing, autospawn should equal 'no'."
cat /etc/pulse/client.conf | grep autospawn
pulseaudio --kill

# dependencies
# --- set virtual env
echo "[setupd.sh] .venv"
source .venv/bin/activate
# --- linux deps??? (fix audio output issues when using systemd)
# --- python (can comment/uncomment to speed up restart)
echo "[setupd.sh] pip install"
# pip install -r requirements.txt

# start.sh
# --- make start.sh executable
echo "[setupd.sh] chmod start.sh"
chmod +x ./start.sh

# systemd
# --- create new systemd service
echo "[setupd.sh] write lattice.halo.service:"
sudo bash -c 'cat << EOF > /etc/systemd/system/lattice.halo.service
[Unit]
Description=Lattice Halo
After=multi-user.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/lattice/device/halo/
ExecStart=sudo bash /home/pi/lattice/device/halo/start.sh
Restart=on-abort

[Install]
WantedBy=multi-user.target
EOF'
echo "---"
cat /etc/systemd/system/lattice.halo.service
echo "---"
echo "[setupd.sh] chmod lattice.halo.service"
sudo chmod 644 /etc/systemd/system/lattice.halo.service

# --- delist service if exists
echo "[setupd.sh] lattice.halo.service: disable"
sudo systemctl disable lattice.halo.service

# --- restart daemon (needed when changing service config file)
echo "[setupd.sh] reload daemon"
sudo systemctl daemon-reload

# --- enable/start service (debug with cmd: "systemctl status lattice.halo.service")
echo "[setupd.sh] lattice.halo.service: enable"
sudo systemctl enable lattice.halo.service

echo "[setupd.sh] lattice.halo.service: (re)start"
sudo systemctl restart lattice.halo.service

# --- status check service
echo "[setupd.sh] lattice.halo.service: status"
systemctl status lattice.halo.service

# --- follow logs
echo "[setupd.sh] lattice.halo.service: logs"
journalctl -fu lattice.halo.service
