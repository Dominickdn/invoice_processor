import json
import pika
import os
from shared.redis_client import r
from shared.s3_client import s3
from dotenv import load_dotenv

load_dotenv()


def enqueue_files():
    bucket_name = os.getenv("MINIO_BUCKET")
    prefix = "process/"

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
        if key.endswith("/"):
            continue

        r.set(key, "queued")

        message = json.dumps({"filename": key})
        channel.basic_publish(exchange="", routing_key=in_queue, body=message)
        print(f"[ENQUEUED] {key}")

    connection.close()
    print("[INFO] All files enqueued.")


if __name__ == "__main__":
    enqueue_files()
