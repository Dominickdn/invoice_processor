import os
import boto3
from botocore.exceptions import ClientError
from io import BytesIO
from parser import extract_invoice_data
from dotenv import load_dotenv

load_dotenv()

# S3 client
s3 = boto3.client(
    's3',
    endpoint_url=os.getenv("MINIO_ENDPOINT"),
    aws_access_key_id=os.getenv("MINIO_ACCESS_KEY"),
    aws_secret_access_key=os.getenv("MINIO_SECRET_KEY"),
)
BUCKET = os.getenv("MINIO_BUCKET")

def download_from_s3(prefixed_key):
    obj = s3.get_object(Bucket=BUCKET, Key=prefixed_key)
    return BytesIO(obj['Body'].read())

def upload_to_s3(buffer, prefix, filename):
    s3.upload_fileobj(buffer, BUCKET, f"{prefix}{filename}")

def delete_from_s3(prefixed_key):
    s3.delete_object(Bucket=BUCKET, Key=prefixed_key)

def process_file(filename):
    key = f"{filename}"
    try:
        body = download_from_s3(key)
    except ClientError as e:
        print(f"[ERROR] Cannot download {key}: {e}")
        return False

    try:
        print(f"Moving to Processed {filename}")

        upload_to_s3(body, "processed/", filename)
        delete_from_s3(key)
        return True

    except Exception as e:
        print(f"[ERROR] Processing failed for {filename}: {e}")
        body.seek(0)
        upload_to_s3(body, "failed/", filename)
        delete_from_s3(key)
        return False
