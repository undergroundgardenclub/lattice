from file.file_cloud_storage import get_stored_file_bytes
from file.file_utils import get_media_file_duration, tmp_file_rmv, tmp_file_set


def get_recording_file_duration(file: dict):
    # setup file
    media_file_bytes = get_stored_file_bytes(file.get("file_key")) # TODO: request.files.get('file') but writing offline atm
    tmp_file_path = tmp_file_set(media_file_bytes, "mp4") # need file path for OpenCV processing
    # calc
    try:
        media_duration_sec = get_media_file_duration(tmp_file_path)
    finally:
        tmp_file_rmv(tmp_file_path)
    # return sec
    return media_duration_sec