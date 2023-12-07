import requests
from env import env_api_url


def send_api_recording(recording_file_path: str, recording_meta_dict: dict):
    print("[send_api_recording] sending recording")
    try:
        # Open file
        with open(recording_file_path, 'rb') as file:
            # provide file
            files = {'file': (recording_file_path, file, 'video/mp4')}
            # POST
            response = requests.post(env_api_url() + "/v1/intake/recording", files=files, data=recording_meta_dict)
            # return
            return response
    except Exception as err:
        print("[send_api_recording] error: ", err)
