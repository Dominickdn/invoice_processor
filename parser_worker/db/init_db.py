from dotenv import load_dotenv
from pathlib import Path
from utils.db_connection import get_db_connection

load_dotenv()


def init_db():
    try:
        conn = get_db_connection()
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
