import os
import shutil
import subprocess
import tempfile

# TMP
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
def get_media_duration(file_path):
    print("[get_video_duration] file_path:", file_path)
    command = [
        'ffprobe', '-v', 'error', '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1', file_path
    ]
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    duration = float(result.stdout)
    print(f"[get_video_duration] duration = {duration}, for file_path:", file_path)
    return duration
