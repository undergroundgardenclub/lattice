import os
import shutil
import tempfile

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

