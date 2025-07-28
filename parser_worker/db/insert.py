from dotenv import load_dotenv
from utils.db_connection import get_db_connection

load_dotenv()


def insert_invoice_data(data, file_name):
    """
    Inserts an invoice and its items into the PostgreSQL database.
    Expects data to be a dict with keys:
      - invoice_number (str)
      - invoice_date (str or date)
      - vendor (str)
      - total_amount_due (float or decimal)
      - items: list of dicts with keys:
          item (str), qty (int), unit_price (float)
    """
    print(f"[DEBUG] Inserting invoice data: {data}")
    print(f"[DEBUG] file: {file_name}")
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Insert into invoices table
        cur.execute(
            """
            INSERT INTO invoices (
                invoice_number,
                invoice_date,
                vendor,
                total_amount_due,
                file_name
            )
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id;
        """,
            (
                data["invoice_number"],
                data["invoice_date"],
                data["vendor"],
                data["total_amount_due"],
                f"{file_name}",
            ),
        )
        invoice_id = cur.fetchone()[0]

        # Insert items into invoice_items table
        for item in data.get("items", []):
            cur.execute(
                """
                INSERT INTO invoice_items (invoice_id, item, qty, unit_price)
                VALUES (%s, %s, %s, %s);
            """,
                (
                    invoice_id,
                    item.get("item"),
                    item.get("qty"),
                    item.get("unit_price"),
                ),
            )

        conn.commit()
        print(
            f"[INFO] Inserted invoice {data['invoice_number']}"
            f"(ID: {invoice_id}) successfully."
        )
        return True

    except Exception as e:
        conn.rollback()
        print(f"[ERROR] Failed to insert invoice: {e}")
        return False

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()
