from dotenv import load_dotenv
import os
from utils_device import get_device_identifier

# SETUP
# --- init .env file
load_dotenv()
# --- getter
def _env_getter(key):
    # if (os.environ.get(key) == None):
    #     set_secrets_on_env()
    return os.environ.get(key)


# AWS
def env_aws_access_key_id():
    return _env_getter('AWS_ACCESS_KEY_ID')
def env_aws_secret_access_key():
    return _env_getter('AWS_SECRET_ACCESS_KEY')
def env_aws_s3_files_bucket():
    return _env_getter('AWS_FILES_BUCKET')

# DEVICE
def env_device_id():
    return get_device_identifier()
    
def env_directory_data():
    this_path = os.path.dirname(os.path.abspath(__file__))
    return this_path + "/data"

# RECORDING
def env_recording_frame_rate():
    # 12 fps had blur from movement, so try to inch upwards. default is 25 but trying to reduce long capture file size. because h264 doesnt hold fps we need to copy into a mp4 med container w/ fps info (https://github.com/waveform80/picamera/issues/253#issuecomment-163593379)
    # 25 (default) threw timings off harddddd
    return 15 # 15 seems like it has the least drift

def env_recording_sample_rate():
    return 48000 # 44100 somehow is not acceptable for the PortAudio lib, I think it may be related to device? https://discourse.psychopy.org/t/sound-engine-ptb-causes-sampling-rate-error/26095

# SERVICES
def env_api_url():
    return "http://lattice.ngrok.app"
