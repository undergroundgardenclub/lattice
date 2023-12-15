import boto3
import io
import json
import logging
import os
import requests
from env import env_aws_access_key_id, env_aws_secret_access_key, env_aws_s3_files_bucket

# DEVICE-LEVEL
def get_file_bytes(path_or_url: str):
    logging.info("[get_file_bytes] fetching file -> bytes: %s", path_or_url)
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
            raise Exception(f"Failed to load audio from path '{path_or_url}': ", e)

def delete_file(file_path: str):
    try:
        logging.info("[delete_file] deleting: %s", file_path)
        os.remove(file_path)
    except IOError as e:
        logging.error("[delete_file] failed deleting %s", file_path)

def write_file_json(file_path, data):
    logging.info("[write_data] json -> %s", file_path)
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
    logging.info("[store_file_from_pyfile] upload start: '%s/%s'", bucket, file_key)
    s3.upload_fileobj(io.BytesIO(pyfile.body), bucket, file_key)
    logging.info("[store_file_from_pyfile] upload finish: '%s/%s'", bucket, file_key)

def store_file_from_bytes(bytesio: io.BytesIO, file_key: str) -> None:
    logging.info("[store_file_from_bytes] upload start: '%s/%s'", bucket, file_key)
    s3.upload_fileobj(bytesio, bucket, file_key)
    logging.info("[store_file_from_bytes] upload finish: '%s/%s'", bucket, file_key)

def store_file_from_path(file_path: str, file_key: str) -> None:
    logging.info("[store_file_from_path] upload start: '%s/%s'", bucket, file_key)
    with open(file_path, 'rb') as file_data:
        s3.upload_fileobj(file_data, bucket, file_key)
    logging.info("[store_file_from_path] upload finish: '%s/%s'", bucket, file_key)

# --- getters
def get_stored_file_url(file_key: str) -> str:
    return f"https://s3.amazonaws.com/{bucket}/{file_key}"

def get_stored_file_bytes(file_key: str) -> bytes:
    byte_array = io.BytesIO()
    logging.info("[get_store_file] downloading '%s/%s'...", bucket, file_key)
    s3.download_fileobj(Bucket=bucket, Key=file_key, Fileobj=byte_array)
    logging.info("[get_store_file] downloaded '%s/%s'", bucket, file_key)
    # returns a python File obj, not our model
    return byte_array.getvalue()
