#!/bin/bash

echo "[setupc.sh] setup"
START_SCRIPT_PATH="/home/pi/lattice/device/halo/start.sh"
RUN_COMMAND="bash $START_SCRIPT_PATH"

# Clear existing crons
echo "[setupc.sh] deleting existing crons"
crontab -u pi -r

# Adding the cron job to the crontab of user 'pi'
(crontab -l -u pi 2>/dev/null; echo "@reboot $RUN_COMMAND") | crontab -u pi -
echo "[setupc.sh] cron job added to run $START_SCRIPT_PATH at boot."

# Verify cron will run at boot via
echo "[setupc.sh] verifying"
crontab -l -u pi
