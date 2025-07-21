import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()


def get_invoices_with_items(limit=20, offset=0):
    conn = psycopg2.connect(
        host=os.getenv("POSTGRES_HOST"),
        port=os.getenv("POSTGRES_PORT"),
        database=os.getenv("POSTGRES_DB"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
    )
    cur = conn.cursor()
    cur.execute(
        """
        SELECT i.id, i.invoice_number, i.invoice_date, i.vendor,
               i.total_amount_due, it.item, it.qty, it.unit_price
        FROM invoices i
        LEFT JOIN invoice_items it ON i.id = it.invoice_id
        ORDER BY i.invoice_date DESC
        LIMIT %s OFFSET %s;
    """,
        (limit, offset),
    )

    rows = cur.fetchall()
    cur.close()
    conn.close()

    # Group items by invoice
    invoices = {}
    for row in rows:
        inv_id, number, date, vendor, total, item, qty, price = row
        if inv_id not in invoices:
            invoices[inv_id] = {
                "invoice_number": number,
                "invoice_date": date,
                "vendor": vendor,
                "total_amount_due": total,
                "items": [],
            }
        if item:
            invoices[inv_id]["items"].append(
                {"item": item, "qty": qty, "unit_price": price}
            )
    return list(invoices.values())
