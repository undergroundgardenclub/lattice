# Strategy



# Setup

### Pinouts

The pinout setup (that worked for my board at least)
https://www.electrorules.com/raspberry-pi-4-gpio-pnout/

### SSHing + Remote VS Code

SSHing into the Pi via WiFi:
https://www.youtube.com/watch?v=naDYXkI5UYE

Using the VS Code Remote-SSH setup to code:
https://help.rc.ufl.edu/doc/SSH_Using_VSCode#:~:text=Visual%20Studio%20Code%20will%20connect,connected%20to%20a%20login%20node.

# Installs

Update and upgrade your system:
```
sudo apt update
sudo apt full-upgrade
```

virtual environment aka .venv (so we don't break root python libs. Need system site packages for camera lib issue https://github.com/raspberrypi/picamera2/issues/341#issuecomment-1268460969)
```
python -m venv .venv --system-site-packages
source .venv/bin/activate
```

### Audio (via USB)
Install binaries for use of pyaudio, then install pyaudio
```
sudo apt-get install portaudio19-dev
pip install pyaudio
```

Detecting devices with audio input can be done:
```
arecord -l
```

### Camera (Picamera2)
```
pip install picamera2
```
FFMPEG seems to already exist but in any case. To wrap H264 in containers like MP4 to include frame rate info (not re-encoding), we need ffmpeg (might already installed with picamera)
```
sudo apt install ffmpeg
```

If you hit some issues, maybe these will help. My issue ultimately was with the --system-site-packages flag above:
Was getting an error with libcap development headers needing to be installed, so ran command here: https://github.com/raspberrypi/picamera2/issues/383#issuecomment-1296844749
Had some other errors: https://stackoverflow.com/questions/70961915/error-while-installing-pytq5-with-pip-preparing-metadata-pyproject-toml-did-n
Did installation with pip: https://github.com/raspberrypi/picamera2

### Cirtcuit Python?
Install the required packages for CircuitPython:
```
pip install RPI.GPIO
```


# Wifi

FYI, need to set for multiple locations if moving between spaces: https://raspberrypi.stackexchange.com/questions/11631/how-to-setup-multiple-wifi-networks


# Env

