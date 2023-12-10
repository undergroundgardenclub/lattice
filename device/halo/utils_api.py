import json
from typing import List
import requests
from env import env_api_url


# RECORDINGS
def req_recording_submit(recording_file_path: str, recording_meta_dict: dict):
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

def req_recording_series_submit(files: List[dict]):
    print("[req_recording_series_submit] sending recording")
    # post w/ files array of already uploaded files (using json.dumps to convert python dicts to JSON friendly objs?)
    response = requests.post(env_api_url() + "/v1/intake/recording/series", data=json.dumps({ 'files': files }))
    # parse response JSON
    response_json = response.json()
    print('[req_recording_series_submit] response: ', response_json)
    # return (no payload expected)
    return


# QUERY
def req_query(query_file: dict):
    print("[req_query] sending query recording")
    # post
    response = requests.post(env_api_url() + "/v1/intake/query", data=json.dumps({ 'file': query_file }))
    # parse response JSON
    response_json = response.json()
    print('[req_query] response: ', response_json)
    # return
    return response_json['data']
