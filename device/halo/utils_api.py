import json
import logging
from typing import List
import requests
from env import env_api_url, env_device_id


# RECORDINGS
# --- series
def req_recording_series_send(media_file_dict: dict, series_id: str):
    logging.info("[req_recording_series_send] sending recording")
    try:
        response = requests.post(env_api_url() + "/v1/device/ingest/recording", data=json.dumps({ "device_id": env_device_id(), "series_id": series_id, "media_file_dict": media_file_dict }))
        response_json = response.json()
        logging.info('[req_recording_series_send] response: ', response_json)
        return
    except Exception as err:
        logging.error("[req_recording_series_send] error: %s", err)
        return


# QUERY
def req_query(query_media_file_dict: dict, series_id: str = None):
    logging.info("[req_query] sending query recording/file")
    try:
        response = requests.post(env_api_url() + "/v1/actor/act", data=json.dumps({ "device_id": env_device_id(), "series_id": series_id, "media_file_dict": query_media_file_dict }))
        response_json = response.json()
        logging.info("[req_query] response: ", response_json)
        return response_json.get("data")
    except Exception as err:
        logging.error("[req_query] error: %s", err)
        return None


# DEVICE MESSAGES
def req_get_device_messages():
    logging.debug("[req_get_device_messages] checking device messages") # kinda spammy
    try:
        response = requests.get(env_api_url() + "/v1/device/messages", data=json.dumps({ "device_id": env_device_id() }))
        response_json = response.json()
        if len(response_json.get("data").get("messages", [])) > 0:
            logging.info("[req_get_device_messages] new device messages: ", response_json)
            return response_json.get("data").get("messages", [])
        return []
    except Exception as err:
        logging.error("[req_get_device_messages] error: %s", err)
        return []


# EVENTS
def req_tracking_event(event: dict) -> None:
    try:
        logging.info("[req_tracking_event] => %s", event)
        response = requests.post(env_api_url() + "/v1/tracking/event", data=json.dumps({ "event": { "device_id": env_device_id(), **event } }))
        return
    except Exception as err:
        logging.error("[req_tracking_event] error: %s", err)
        return
