import os
import json
import pika
import time
from dotenv import load_dotenv
from processor import process_file
from utils.rabbitmq_connection import get_rabbitmq_connection

load_dotenv()


def callback(ch, method, properties, body):
    msg = json.loads(body)
    text = msg.get("text")
    filename = msg.get("filename")

    if not text:
        print(f"[ERROR] No text received for file {filename}")
        ch.basic_ack(delivery_tag=method.delivery_tag)
        return

    try:
        # Process the file parses and inserts data
        process_file(filename, text)
        print(f"[INFO] Successfully parsed and inserted: {filename}")
    except Exception as e:
        print(f"[ERROR] Failed to parse or insert {filename}: {e}")

    ch.basic_ack(delivery_tag=method.delivery_tag)


def main():
    connection = None
    for attempt in range(1, 10):
        try:
            print(
                "[INFO] Attempting to connect "
                f"to RabbitMQ (try {attempt}/9)..."
            )
            connection = get_rabbitmq_connection()
            print("[INFO] Connected to RabbitMQ.")
            break
        except pika.exceptions.AMQPConnectionError as e:
            print(f"[WARNING] RabbitMQ connection failed: {e}")
            time.sleep(5)

    if not connection:
        print(
            "[ERROR] Could not connect to RabbitMQ after 5 attempts. Exiting."
        )
        return

    channel = connection.channel()
    queue = os.getenv("RABBITMQ_QUEUE_OCR_RESULTS")
    channel.queue_declare(queue=queue)

    channel.basic_consume(
        queue=queue, on_message_callback=callback, auto_ack=False
    )
    print("[INFO] Parser waiting for messages...")
    channel.start_consuming()


if __name__ == "__main__":
    main()
