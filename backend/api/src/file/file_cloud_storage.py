import boto3
import io
from env import env_get_aws_access_key_id, env_get_aws_secret_access_key, env_get_aws_s3_files_bucket

s3 = boto3.client('s3',
    aws_access_key_id=env_get_aws_access_key_id(),
    aws_secret_access_key= env_get_aws_secret_access_key())

# https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3.html#S3.Client.upload_fileobj
def store_file_from_pyfile(pyfile, file_key: str) -> None:
    bucket = env_get_aws_s3_files_bucket()
    print(f"[store_file_from_pyfile] upload start: '{bucket}/{file_key}'")
    s3.upload_fileobj(io.BytesIO(pyfile.body), bucket, file_key)
    print(f"[store_file_from_pyfile] upload finish: '{bucket}/{file_key}'")

def store_file_from_bytes(bytesio: io.BytesIO, file_key: str) -> None:
    bucket = env_get_aws_s3_files_bucket()
    print(f"[store_file_from_bytes] upload start: '{bucket}/{file_key}'")
    s3.upload_fileobj(bytesio, bucket, file_key)
    print(f"[store_file_from_bytes] upload finish: '{bucket}/{file_key}'")

def store_file_from_string(body_string: str, file_key: str) -> None:
    bucket = env_get_aws_s3_files_bucket()
    print(f"[store_file_from_string] upload start: '{bucket}/{file_key}'")
    s3.put_object(Body=body_string, Bucket=bucket, Key=file_key)
    print(f"[store_file_from_string] upload finish: '{bucket}/{file_key}'")

def get_stored_file_url(file_key: str) -> str:
    bucket = env_get_aws_s3_files_bucket()
    return f"https://s3.amazonaws.com/{bucket}/{file_key}"

def get_stored_file_bytes(file_key: str) -> bytes:
    byte_array = io.BytesIO()
    bucket = env_get_aws_s3_files_bucket()
    print(f"[get_store_file] downloading '{bucket}/{file_key}'...")
    s3.download_fileobj(Bucket=bucket, Key=file_key, Fileobj=byte_array)
    print(f"[get_store_file] downloaded '{bucket}/{file_key}'")
    # returns a python File obj, not our model
    return byte_array.getvalue()