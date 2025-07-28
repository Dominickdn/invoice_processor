import os
import boto3
from dotenv import load_dotenv
from io import BytesIO
from botocore.exceptions import ClientError

load_dotenv()

BUCKET = os.getenv("MINIO_BUCKET")

s3 = boto3.client(
    "s3",
    endpoint_url=os.getenv("MINIO_ENDPOINT"),
    aws_access_key_id=os.getenv("MINIO_ACCESS_KEY"),
    aws_secret_access_key=os.getenv("MINIO_SECRET_KEY"),
)


def download_from_s3(prefixed_key):
    obj = s3.get_object(Bucket=BUCKET, Key=prefixed_key)
    return BytesIO(obj["Body"].read())


def upload_to_s3(buffer, prefix, filename):
    s3.upload_fileobj(buffer, BUCKET, f"{prefix}{filename}")


def delete_from_s3(prefixed_key):
    s3.delete_object(Bucket=BUCKET, Key=prefixed_key)


def list_files_in_folder(prefix):
    response = s3.list_objects_v2(Bucket=BUCKET, Prefix=prefix)
    contents = response.get("Contents", [])
    files = [
        obj["Key"].replace(prefix, "")
        for obj in contents
        if not obj["Key"].endswith("/")
    ]
    return files


def ensure_bucket_exists(bucket_name):
    try:
        s3.head_bucket(Bucket=bucket_name)
        print(f"[INFO] Bucket '{bucket_name}' already exists.")
    except ClientError as e:
        error_code = int(e.response["Error"]["Code"])
        if error_code == 404:
            print(f"[INFO] Bucket '{bucket_name}' not found. Creating...")
            s3.create_bucket(Bucket=bucket_name)
            print(f"[SUCCESS] Bucket '{bucket_name}' created.")
        else:
            print(f"[ERROR] Failed to check or create bucket: {e}")
            raise
