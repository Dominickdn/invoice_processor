import boto3
from botocore.exceptions import ClientError
import os
from dotenv import load_dotenv

load_dotenv()


def ensure_bucket_exists(bucket_name):
    """
    Checks if the specified S3 bucket exists. If not, creates it.

    Args:
        bucket_name (str): The name of the bucket to check or create.
    """
    s3 = boto3.client(
        "s3",
        endpoint_url=os.getenv("MINIO_ENDPOINT"),
        aws_access_key_id=os.getenv("MINIO_ACCESS_KEY"),
        aws_secret_access_key=os.getenv("MINIO_SECRET_KEY"),
    )

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
