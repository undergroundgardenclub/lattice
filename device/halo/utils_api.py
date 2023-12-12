import json
from typing import List
import requests
from env import env_api_url, env_device_id


# RECORDINGS
# --- batch
def req_recording_batch_submit(files: List[dict]):
    print("[req_recording_batch_submit] sending recording")
    try:
        response = requests.post(env_api_url() + "/v1/intake/recording/batch", data=json.dumps({ "device_id": env_device_id(), "files": files }))
        response_json = response.json()
        print('[req_recording_batch_submit] response: ', response_json)
        return
    except Exception as err:
        print("[req_recording_batch_submit] error: ", err)
        return

# --- series
def req_recording_series_submit(file: dict, series_id: str):
    print("[req_recording_series_submit] sending recording")
    try:
        response = requests.post(env_api_url() + "/v1/intake/recording/series", data=json.dumps({ "device_id": env_device_id(), "file": file, "series_id": series_id }))
        response_json = response.json()
        print('[req_recording_series_submit] response: ', response_json)
        return
    except Exception as err:
        print("[req_recording_series_submit] error: ", err)
        return

def req_recording_series_done(series_id: str):
    print("[req_recording_series_done] sending recording")
    try:
        response = requests.post(env_api_url() + "/v1/intake/recording/series/done", data=json.dumps({ "device_id": env_device_id(), "series_id": series_id }))
        response_json = response.json()
        print('[req_recording_series_done] response: ', response_json)
        return
    except Exception as err:
        print("[req_recording_series_done] error: ", err)
        return


# QUERY
def req_query(query_file: dict, series_id: str = None):
    print("[req_query] sending query recording/file")
    try:
        response = requests.post(env_api_url() + "/v1/intake/query", data=json.dumps({ "device_id": env_device_id(), "file": query_file, "series_id": series_id }))
        response_json = response.json()
        print("[req_query] response: ", response_json)
        return response_json.get("data")
    except Exception as err:
        print("[req_query] error: ", err)
        return None


# DEVICE MESSAGES
def req_get_device_messages():
    # print("[req_get_device_messages] checking device messages") # kinda spammy
    try:
        response = requests.get(env_api_url() + "/v1/device/messages", data=json.dumps({ "device_id": env_device_id() }))
        response_json = response.json()
        if len(response_json.get("data").get("messages", [])) > 0:
            print("[req_get_device_messages] new device messages: ", response_json)
            return response_json.get("data").get("messages", [])
        return []
    except Exception as err:
        print("[req_get_device_messages] error: ", err)
        return []