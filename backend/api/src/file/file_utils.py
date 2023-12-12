import io
import os
import subprocess
import tempfile
from typing import List

# TMP
def tmp_file_path(prefix=""):
    with tempfile.NamedTemporaryFile(delete=False, prefix=prefix, suffix='.mp4', mode='wb') as tmp_file:
        return tmp_file.name

def tmp_file_set(file_bytes):
    # Write the video bytes to a temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4', mode='wb') as tmp_file:
        tmp_file.write(file_bytes)
        tmp_file_path = tmp_file.name
    print(f'[tmp_file_set] path: {tmp_file_path}')
    return tmp_file_path

def tmp_file_rmv(file_path):
    print(f'[tmp_file_rmv] path: {file_path}')
    os.remove(file_path)


# MEDIA
def get_media_file_duration(file_path):
    print("[get_video_duration] file_path:", file_path)
    command = [
        'ffprobe', '-v', 'error', '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1', file_path
    ]
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    duration = float(result.stdout)
    print(f"[get_video_duration] duration = {duration}, for file_path:", file_path)
    return duration

def merge_media_files(file_paths: List[str], output_file_path: str):
    print("[merge_media_files] file_paths:", file_paths)
    # --- form file txt
    file_list_content = "".join(f"file '{path}'\n" for path in file_paths)
    file_list_bytes = io.BytesIO(file_list_content.encode())
    file_list_path = tmp_file_set(file_list_bytes.read())
    # --- FFmpeg command (feed in tmp file)
    command = [
        "ffmpeg",
        "-y", # -y overwrites the file. i'mo overwriting bc the temp file command creates a file
        "-protocol_whitelist", "file,https,tcp,tls",
        "-f", "concat", # specifies concating file. w/o this I think I'm just over-writing
        "-safe", "0", # "The -safe 0 is not required if the paths are relative" (https://trac.ffmpeg.org/wiki/Concatenate#Instructions)
        "-i", file_list_path,
        "-c", "copy", output_file_path,
    ]
    # --- execute
    print("[merge_media_files] command:", command)
    subprocess.run(command, check=True)
    # --- rmv tmp txt file
    tmp_file_rmv(file_list_path)
