import boto3
import io
from env import env_aws_access_key_id, env_aws_secret_access_key, env_aws_s3_files_bucket


# CLOUD-LEVEL
# --- setup
s3 = boto3.client('s3',
    aws_access_key_id=env_aws_access_key_id(),
    aws_secret_access_key= env_aws_secret_access_key())
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
    print(f"[store_file_from_path] upload start: '{file_path}' > '{bucket}/{file_key}'")
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
