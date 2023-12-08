import requests
from env import env_api_url


# RECORDINGS
def send_api_recording(recording_file_path: str, recording_meta_dict: dict):
    """
    Send API a long recording that turns into an outline/email
    """
    print("[send_api_recording] sending recording")
    try:
        # Open file
        with open(recording_file_path, 'rb') as file:
            # provide file
            files = {'file': (recording_file_path, file, 'video/mp4')}
            # post
            response = requests.post(env_api_url() + "/v1/intake/recording", files=files, data=recording_meta_dict)
            # parse response JSON
            response_json = response.json()
            print('[send_api_recording] response: ', response_json)
            # return
            return response_json['data']
    except Exception as err:
        print("[send_api_recording] error: ", err)

# QUERY
def send_api_query(recording_file_path: str, recording_meta_dict: dict):
    """
    Send API a recording that queries LLMs, and returns an audio clip response to play to user
    """
    print("[send_api_query] sending recording")
    try:
        # Open file
        with open(recording_file_path, 'rb') as file:
            # provide file
            files = {'file': (recording_file_path, file, 'video/mp4')}
            # post
            response = requests.post(env_api_url() + "/v1/intake/query", files=files, data=recording_meta_dict)
            # parse response JSON
            response_json = response.json()
            print('[send_api_query] response: ', response_json)
            # return
            return response_json['data']
    except Exception as err:
        print("[send_api_query] error: ", err)
