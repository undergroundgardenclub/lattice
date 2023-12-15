import json
import logging
from typing import List
import requests
from env import env_api_url, env_device_id


# RECORDINGS
# --- series
def req_recording_series_submit(file: dict, series_id: str):
    logging.info("[req_recording_series_submit] sending recording")
    try:
        response = requests.post(env_api_url() + "/v1/intake/recording/series", data=json.dumps({ "device_id": env_device_id(), "file": file, "series_id": series_id }))
        response_json = response.json()
        logging.info('[req_recording_series_submit] response: ', response_json)
        return
    except Exception as err:
        logging.error("[req_recording_series_submit] error: ", err)
        return


# QUERY
def req_query(query_file: dict, series_id: str = None):
    logging.info("[req_query] sending query recording/file")
    try:
        response = requests.post(env_api_url() + "/v1/intake/query", data=json.dumps({ "device_id": env_device_id(), "file": query_file, "series_id": series_id }))
        response_json = response.json()
        logging.info("[req_query] response: ", response_json)
        return response_json.get("data")
    except Exception as err:
        logging.error("[req_query] error: ", err)
        return None


# DEVICE MESSAGES
def req_get_device_messages():
    logging# .info("[req_get_device_messages] checking device messages") # kinda spammy
    try:
        response = requests.get(env_api_url() + "/v1/device/messages", data=json.dumps({ "device_id": env_device_id() }))
        response_json = response.json()
        if len(response_json.get("data").get("messages", [])) > 0:
            logging.info("[req_get_device_messages] new device messages: ", response_json)
            return response_json.get("data").get("messages", [])
        return []
    except Exception as err:
        logging.error("[req_get_device_messages] error: ", err)
        return []


# EVENTS
def req_tracking_event(event: dict) -> None:
    try:
        logging.info("[req_tracking_event] => ", event)
        response = requests.post(env_api_url() + "/v1/tracking/event", data=json.dumps({ "event": { "device_id": env_device_id(), **event } }))
        return
    except Exception as err:
        logging.error("[req_get_device_messages] error: ", err)
        return
