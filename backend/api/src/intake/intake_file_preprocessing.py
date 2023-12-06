from uuid import uuid4
from file.file_cloud_storage import get_stored_file_bytes, get_stored_file_url, store_file_from_pyfile


def intake_file_preprocessing(pyfile) -> (str, str):
    """Take a file from sanic route, and upload to S3 so it can be processed by workers"""
    # --- randomize file name to avoid collisions
    file_key = f"{uuid4()}.mp4"
    file_url = get_stored_file_url(file_key)
    # --- store in s3
    store_file_from_pyfile(pyfile, file_key)
    # --- return file/url to other processes that may want access
    return file_key, file_url
