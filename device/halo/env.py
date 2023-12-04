import board
import os
from utils_device import get_device_identifier

# PINS
PIN_RECORD_BUTTON = board.D14
PIN_LED = board.D23

# VARS
def env_device_id():
    return get_device_identifier()

def env_directory_data():
    this_path = os.path.dirname(os.path.abspath(__file__))
    return this_path + "/data"

def env_recording_frame_rate():
    # 12 fps had blur from movement, so try to inch upwards. default is 25 but trying to reduce long capture file size. because h264 doesnt hold fps we need to copy into a mp4 med container w/ fps info (https://github.com/waveform80/picamera/issues/253#issuecomment-163593379)
    return 15

def env_recording_sample_rate():
    return 44100
