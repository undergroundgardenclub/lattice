#!/bin/bash

# SETUP: systemd setup scripts (run w/ sudo)

# dependencies
# --- init virtual env
echo "[setupd.sh] .venv"
source .venv/bin/activate

# start.sh
# --- make start.sh executable
echo "[setupd.sh] chmod start.sh"
chmod +x ./start.sh

# systemd
# --- create new systemd service (XDG SHIT IS CRITICAL FOR PLAYBACK AUDIO FFFFFFFSS)
echo "[setupd.sh] write lattice.halo.service:"
sudo bash -c 'cat << EOF > /etc/systemd/system/lattice.halo.service
[Unit]
Description=Lattice Halo
After=multi-user.target

[Service]
Type=simple
User=pi
Group=audio
Environment="DISPLAY=:0"
Environment="XDG_RUNTIME_DIR=/run/user/1000"
WorkingDirectory=/home/pi/lattice/device/halo/
ExecStart=bash /home/pi/lattice/device/halo/start.sh
Restart=on-abort

[Install]
WantedBy=multi-user.target
EOF'
echo "---"
cat /etc/systemd/system/lattice.halo.service
echo "---"
echo "[setupd.sh] chmod lattice.halo.service + start.sh"
sudo chmod 644 /etc/systemd/system/lattice.halo.service
sudo chmod 744 /home/pi/lattice/device/halo/start.sh

# --- permissions for files/folders/etc
echo "[setupd.sh] chowns"
sudo chown pi:pi /home/pi/lattice/device/halo/logs
# TODO: I commented out !root user lines on pipewire service configs, not sure if this will be needed https://www.reddit.com/r/pipewire/comments/mibuu9/pipewire_as_root/

# --- delist service if exists
echo "[setupd.sh] lattice.halo.service: disable"
sudo systemctl stop lattice.halo.service
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
