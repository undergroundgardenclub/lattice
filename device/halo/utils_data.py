import io
import json
import requests

def get_file_bytes(path_or_url: str):
    print(f"[get_file_bytes] fetching file -> bytes (path/url: {path_or_url})")
    is_url = path_or_url.startswith("http")
    # ... fetch/download to bytes (aka we're in memory)
    if is_url == True:
        response = requests.get(path_or_url)
        if response.status_code == 200:
            return io.BytesIO(response.content)
        else:
            raise Exception(f"Failed to download audio: {response.status_code}")
    # ... or open file to bytes (aka we're in memory)
    else:
        try:
            with open(path_or_url, 'rb') as file:
                return io.BytesIO(file.read())
        except IOError as e:
            raise Exception(f"Failed to load audio from path '{path_or_url}': {e}")

def write_file_json(file_path, data):
    print('[write_data] json -> ', file_path)
    with open(file_path, 'w') as json_file:
        json.dump(data, json_file, indent=4)

def read_file_json(file_path):
    with open(file_path, 'r') as json_file:
        data = json.load(json_file)
        return data
