import psycopg2
import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()


def init_db():
    try:
        conn = psycopg2.connect(
            host=os.getenv("POSTGRES_HOST"),
            port=os.getenv("POSTGRES_PORT"),
            database=os.getenv("POSTGRES_DB"),
            user=os.getenv("POSTGRES_USER"),
            password=os.getenv("POSTGRES_PASSWORD"),
        )
        cur = conn.cursor()

        schema_path = Path(__file__).parent / "schema.sql"
        with schema_path.open("r") as f:
            cur.execute(f.read())

        conn.commit()
        print("[INFO] Database schema initialized.")
    except Exception as e:
        print(f"[ERROR] Failed to initialize DB: {e}")
    finally:
        if conn:
            cur.close()
            conn.close()


if __name__ == "__main__":
    init_db()
