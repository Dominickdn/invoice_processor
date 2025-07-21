from botocore.exceptions import ClientError
from dotenv import load_dotenv
from shared.s3_client import s3

load_dotenv()


def ensure_bucket_exists(bucket_name):
    """Creates s3 bucket if it does not exist."""
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
