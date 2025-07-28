import os
from botocore.exceptions import ClientError
from parser import extract_invoice_data
from db.insert import insert_invoice_data
from utils.redis_client import r
from utils.s3_client import upload_to_s3, download_from_s3, delete_from_s3


def get_clean_filename(filepath):
    """Extract just the filename, stripping any prefixes like 'process/'."""
    return os.path.basename(filepath)


def move_file_to(bucket_prefix, buffer, filename):
    """Move file to given prefix (e.g., 'failed/', 'processed/')."""
    buffer.seek(0)
    upload_to_s3(buffer, bucket_prefix, filename)


def process_file(filename, text):
    key = filename  # Full S3 key, like 'process/invoice.pdf'
    try:
        body = download_from_s3(key)
    except ClientError as e:
        print(f"[ERROR] Cannot download {key}: {e}")
        return False

    # Extract filename only (e.g. 'invoice.pdf')
    clean_filename = get_clean_filename(filename)
    processed_filename = f"processed/{clean_filename}"

    try:
        data = extract_invoice_data(text)
    except Exception as e:
        print(f"[ERROR] Failed to parse invoice from {filename}: {e}")
        r.set(key, "failed")
        move_file_to("failed/", body, clean_filename)
        delete_from_s3(key)
        return False

    try:
        success = insert_invoice_data(data, processed_filename)
        if not success:
            raise Exception("Insert failed")
    except Exception as e:
        print(f"[ERROR] DB insert failed for {filename}: {e}")
        r.set(key, "failed")
        move_file_to("failed/", body, clean_filename)
        delete_from_s3(key)
        return False

    # Everything succeeded: move to processed
    print(f"[INFO] Successfully inserted and moving {filename} to processed/")
    r.set(key, "completed")
    move_file_to("processed/", body, clean_filename)
    delete_from_s3(key)
    return True
