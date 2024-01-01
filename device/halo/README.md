# Halo


## Setup Board

### Raspberry Pi OS

Find latest OS: https://www.raspberrypi.com/software/operating-systems/#raspberry-pi-os-64-bit

Install via Raspberry Pi installer. You can use the xz files, you don't need to unzip. Be sure to customize settings for initial WiFi connection and turn on the ssh connections setting. DO NOT use Lite version for now. Even though we don't need desktop packages, there are things such as pipewire's `pw-play`.

### SSHing + Remote VS Code

Grab the VS code [Remote-SSH plugin](https://help.rc.ufl.edu/doc/SSH_Using_VSCode#:~:text=Visual%20Studio%20Code%20will%20connect,connected%20to%20a%20login%20node).

Connect to `pi@raspberrypi.local`, add to your ssh config in the plugin extension list. If you reinstall the RPi OS, you will need to re-add. You will also need to remove prior connection keys in `~/.ssh/known_hosts` for the `raspberrypi.local`. Be sure to include the user in your ssh path (likely the default "pi" unless you manually changed on OS install)


### Wifi

The 'bookworm' Raspberry Pi OS has apparently drastically changed wifi configs to no longer use wpa_supplicant: https://www.jeffgeerling.com/blog/2023/nmcli-wifi-on-raspberry-pi-os-12-bookworm + https://forums.raspberrypi.com/viewtopic.php?t=357739#p2145139

Code to add a new WiFi network:
```
sudo nmcli c add type wifi con-name <connection-name> ifname wlan0 ssid <yourssid>
sudo nmcli c modify <connection-name> wifi-sec.key-mgmt wpa-psk wifi-sec.psk <wifipassword>
```
Connect:
```
sudo nmcli c up <connection-name>
```


## Setup Application

# Installs

Update and upgrade your system:
```
sudo apt update
sudo apt full-upgrade
```

### Git

To allow git pulls/pushes, authenticate with a key file. Save it at the path: `ssh-add ~/.ssh/id_rsa`.

Then add a new file to config ssh keys at `~/.ssh/config`.
```
Host *
  IdentityFile ~/.ssh/id_rsa
```

When cloning the repo, if you get a too open permissions error, run the command: `chmod 400 ~/.ssh/id_rsa`

Also set global config name/email.
```
git config --global user.name "<name<>"
git config --global user.email "you@example.com"
```

### Linux Deps

These can be installed by calling `bash setup.sh` in the root.

### Audio (via USB)

Check audio recording/output devices can be detected:
```
arecord -l
aplay -l
```

Test playing an audio file with pipewire (wave, mp3, etc.)
```
pw-play path-to-file.mp3
```

### Camera (Picamera2)

Check camera devices can be detected
```
# TODO
```

### Pinouts

The pinout setup (that worked for my board at least)
https://www.electrorules.com/raspberry-pi-4-gpio-pnout/


## Debugging

At the moment, not everything makes it to log files but everything makes it to stdout. When in doubt, just run `sudo bash setupd.sh` which will restart the service and get you listening to output. You may see exceptions crashing processes there.