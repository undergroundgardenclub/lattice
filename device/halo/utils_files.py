import boto3
import io
import json
import os
import requests
from env import env_aws_access_key_id, env_aws_secret_access_key, env_aws_s3_files_bucket

# DEVICE-LEVEL
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

def delete_file(file_path: str):
    try:
        print("[delete_file] deleting: ", file_path)
        os.remove(file_path)
    except IOError as e:
        print(f"[delete_file] failed deleting ", file_path)

def write_file_json(file_path, data):
    print("[write_data] json -> ", file_path)
    with open(file_path, "w") as json_file:
        json.dump(data, json_file, indent=4)

def read_file_json(file_path):
    with open(file_path, "r") as json_file:
        data = json.load(json_file)
        return data


# CLOUD-LEVEL
# --- setup
s3 = boto3.client("s3", aws_access_key_id=env_aws_access_key_id(), aws_secret_access_key= env_aws_secret_access_key())
bucket = env_aws_s3_files_bucket()

# --- uploaders
def store_file_from_pyfile(pyfile, file_key: str) -> None:
    print(f"[store_file_from_pyfile] upload start: '{bucket}/{file_key}'")
    s3.upload_fileobj(io.BytesIO(pyfile.body), bucket, file_key)
    print(f"[store_file_from_pyfile] upload finish: '{bucket}/{file_key}'")

def store_file_from_bytes(bytesio: io.BytesIO, file_key: str) -> None:
    print(f"[store_file_from_bytes] upload start: '{bucket}/{file_key}'")
    s3.upload_fileobj(bytesio, bucket, file_key)
    print(f"[store_file_from_bytes] upload finish: '{bucket}/{file_key}'")

def store_file_from_path(file_path: str, file_key: str) -> None:
    print(f"[store_file_from_path] upload start: '{bucket}/{file_key}'")
    with open(file_path, 'rb') as file_data:
        s3.upload_fileobj(file_data, bucket, file_key)
    print(f"[store_file_from_path] upload finish: '{bucket}/{file_key}'")

# --- getters
def get_stored_file_url(file_key: str) -> str:
    return f"https://s3.amazonaws.com/{bucket}/{file_key}"

def get_stored_file_bytes(file_key: str) -> bytes:
    byte_array = io.BytesIO()
    print(f"[get_store_file] downloading '{bucket}/{file_key}'...")
    s3.download_fileobj(Bucket=bucket, Key=file_key, Fileobj=byte_array)
    print(f"[get_store_file] downloaded '{bucket}/{file_key}'")
    # returns a python File obj, not our model
    return byte_array.getvalue()
