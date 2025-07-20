import os
import json
import pika
import time
from dotenv import load_dotenv
from parser import extract_invoice_data
from db.insert import insert_invoice_data
from processor import process_file

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
        data = extract_invoice_data(text)
        insert_invoice_data(data)
        process_file(
            filename
        )  # Process the file after parsing just moves to different folder
        print(f"[INFO] Successfully parsed and inserted: {filename}")
    except Exception as e:
        print(f"[ERROR] Failed to parse or insert {filename}: {e}")

    ch.basic_ack(delivery_tag=method.delivery_tag)


def main():
    credentials = pika.PlainCredentials(
        os.getenv("RABBITMQ_USER"), os.getenv("RABBITMQ_PASS")
    )
    params = pika.ConnectionParameters(
        host=os.getenv("RABBITMQ_HOST"),
        port=int(os.getenv("RABBITMQ_PORT")),
        credentials=credentials,
    )
    connection = None
    for attempt in range(1, 10):
        try:
            print(
                "[INFO] Attempting to connect "
                f"to RabbitMQ (try {attempt}/9)..."
            )
            connection = pika.BlockingConnection(params)
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

    conn = pika.BlockingConnection(params)
    channel = conn.channel()
    queue = os.getenv("RABBITMQ_QUEUE_OCR_RESULTS")
    channel.queue_declare(queue=queue)

    channel.basic_consume(
        queue=queue, on_message_callback=callback, auto_ack=False
    )
    print("[INFO] Parser waiting for messages...")
    channel.start_consuming()


if __name__ == "__main__":
    main()
