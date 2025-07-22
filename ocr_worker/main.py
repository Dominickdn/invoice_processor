import os
import json
import time
import pika
from dotenv import load_dotenv
from processor import process_file
from utils.rabbitmq_connection import get_rabbitmq_connection

load_dotenv()


def callback(ch, method, properties, body):
    msg = json.loads(body)
    filename = msg.get("filename")
    if not filename:
        print("[WARNING] No filename in message.")
        ch.basic_ack(delivery_tag=method.delivery_tag)
        return

    success, text = process_file(filename)

    result_msg = {
        "filename": filename,
        "status": "processed ocr-worker" if success else "failed ocr-worker",
        "text": text if success else None,
    }

    ch.basic_publish(
        exchange="",
        routing_key=os.getenv("RABBITMQ_QUEUE_OCR_RESULTS"),
        body=json.dumps(result_msg),
    )

    ch.basic_ack(delivery_tag=method.delivery_tag)
    print(f"[INFO] {filename} -> {result_msg['status']}")


def main():
    # Retry connection loop
    connection = None
    for attempt in range(1, 6):
        try:
            print(
                "[INFO] Attempting to connect "
                f"to RabbitMQ (try {attempt}/5)..."
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
    in_queue = os.getenv("RABBITMQ_QUEUE_INVOICES")
    channel.queue_declare(queue=in_queue)

    print("[INFO] Awaiting invoice messages...")

    channel.basic_consume(
        queue=in_queue, on_message_callback=callback, auto_ack=False
    )
    channel.start_consuming()


if __name__ == "__main__":
    main()
