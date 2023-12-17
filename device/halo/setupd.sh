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
# --- create new systemd service
echo "[setupd.sh] write lattice.halo.service:"
sudo bash -c 'cat << EOF > /etc/systemd/system/lattice.halo.service
[Unit]
Description=Lattice Halo
After=multi-user.target sound.target

[Service]
Type=simple
User=pi
Group=audio
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
