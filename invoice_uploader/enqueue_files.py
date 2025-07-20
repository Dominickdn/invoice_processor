import json
import pika
import os
import boto3
from dotenv import load_dotenv
from botocore.exceptions import ClientError

load_dotenv()


def enqueue_files():

    s3 = boto3.client(
        "s3",
        endpoint_url=os.getenv(
            "MINIO_ENDPOINT"
        ),  # e.g., http://localhost:9000
        aws_access_key_id=os.getenv("MINIO_ACCESS_KEY"),
        aws_secret_access_key=os.getenv("MINIO_SECRET_KEY"),
    )

    bucket_name = os.getenv("MINIO_BUCKET")
    prefix = "process/"  # S3 "folder"

    # Check if bucket exists, create if not --- needs to be changed.
    # Breaks flask app if bucket does not exist.
    try:
        s3.head_bucket(Bucket=bucket_name)
        print(f"[INFO] Bucket '{bucket_name}' exists.")
    except ClientError as e:
        error_code = int(e.response["Error"]["Code"])
        if error_code == 404:
            print(f"[INFO] Bucket '{bucket_name}' not found. Creating...")
            s3.create_bucket(Bucket=bucket_name)
            print(f"[SUCCESS] Bucket '{bucket_name}' created.")
        else:
            raise e

    # List files in /process
    response = s3.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
    contents = response.get("Contents", [])

    if not contents:
        print(f"[WARNING] No files found in s3://{bucket_name}/{prefix}")
        return

    credentials = pika.PlainCredentials(
        os.getenv("RABBITMQ_USER"), os.getenv("RABBITMQ_PASS")
    )
    parameters = pika.ConnectionParameters(
        host=os.getenv("RABBITMQ_HOST"),
        port=os.getenv("RABBITMQ_PORT"),
        credentials=credentials,
    )
    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()
    in_queue = os.getenv("RABBITMQ_QUEUE_INVOICES")
    out_queue = os.getenv("RABBITMQ_QUEUE_OCR_RESULTS")

    channel.queue_declare(queue=in_queue)
    channel.queue_declare(queue=out_queue)

    for obj in contents:
        key = obj["Key"]
        if key.endswith("/"):  # skip folder keys
            continue

        message = json.dumps({"filename": key})
        channel.basic_publish(exchange="", routing_key=in_queue, body=message)
        print(f"[ENQUEUED] {key}")

    connection.close()
    print("[INFO] All files enqueued.")


if __name__ == "__main__":
    enqueue_files()
