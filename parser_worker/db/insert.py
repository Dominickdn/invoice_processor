import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

def insert_invoice_data(data):
    """
    Inserts an invoice and its items into the PostgreSQL database.
    Expects data to be a dict with keys:
      - invoice_number (str)
      - invoice_date (str or date)
      - vendor (str)
      - total_amount_due (float or decimal)
      - items: list of dicts with keys: item (str), qty (int), unit_price (float)
    """
    print(f"[DEBUG] Inserting invoice data: {data}")
    try:
        conn = psycopg2.connect(
            host=os.getenv("POSTGRES_HOST"),
            port=os.getenv("POSTGRES_PORT"),
            database=os.getenv("POSTGRES_DB"),
            user=os.getenv("POSTGRES_USER"),
            password=os.getenv("POSTGRES_PASSWORD")
        )
        cur = conn.cursor()

        # Insert into invoices table
        cur.execute("""
            INSERT INTO invoices (invoice_number, invoice_date, vendor, total_amount_due)
            VALUES (%s, %s, %s, %s)
            RETURNING id;
        """, (
            data["invoice_number"],
            data["invoice_date"],
            data["vendor"],
            data["total_amount_due"]
        ))
        invoice_id = cur.fetchone()[0]

        # Insert items into invoice_items table
        for item in data.get("items", []):
            cur.execute("""
                INSERT INTO invoice_items (invoice_id, item, qty, unit_price)
                VALUES (%s, %s, %s, %s);
            """, (
                invoice_id,
                item.get("item"),
                item.get("qty"),
                item.get("unit_price")
            ))

        conn.commit()
        print(f"[INFO] Inserted invoice {data['invoice_number']} (ID: {invoice_id}) successfully.")
        return True

    except Exception as e:
        conn.rollback()
        print(f"[ERROR] Failed to insert invoice: {e}")
        return False

    finally:
        if cur: cur.close()
        if conn: conn.close()
