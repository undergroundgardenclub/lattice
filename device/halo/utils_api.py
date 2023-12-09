import requests
from env import env_api_url


# RECORDINGS
def req_recording_submit(recording_file_path: str, recording_meta_dict: dict):
    """
    Send API a long recording that turns into an outline/email
    """
    print("[req_recording_submit] sending recording")
    try:
        # Open file
        with open(recording_file_path, 'rb') as file:
            # provide file
            files = {'file': (recording_file_path, file, 'video/mp4')}
            # post
            response = requests.post(env_api_url() + "/v1/intake/recording", files=files, data=recording_meta_dict)
            # parse response JSON
            response_json = response.json()
            print('[req_recording_submit] response: ', response_json)
            # return (no payload expected)
            return
    except Exception as err:
        print("[req_recording_submit] error: ", err)

def req_recording_submit_session_start(device_id, session_id):
    print("[req_recording_submit] sending recording")


# QUERY
def req_query(recording_file_path: str, recording_meta_dict: dict):
    """
    Send API a recording that queries LLMs, and returns an audio clip response to play to user
    """
    print("[req_query] sending recording")
    try:
        # Open file
        with open(recording_file_path, 'rb') as file:
            # provide file
            files = {'file': (recording_file_path, file, 'video/mp4')}
            # post
            response = requests.post(env_api_url() + "/v1/intake/query", files=files, data=recording_meta_dict)
            # parse response JSON
            response_json = response.json()
            print('[req_query] response: ', response_json)
            # return
            return response_json['data']
    except Exception as err:
        print("[req_query] error: ", err)
