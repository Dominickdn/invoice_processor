from dotenv import load_dotenv
from utils.db_connection import get_db_connection

load_dotenv()


def get_invoices_with_items(limit=20, offset=0):
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT id, invoice_number, invoice_date, vendor, total_amount_due
        FROM invoices
        ORDER BY invoice_date DESC
        LIMIT %s OFFSET %s;
        """,
        (limit, offset),
    )
    invoice_rows = cur.fetchall()

    if not invoice_rows:
        cur.close()
        conn.close()
        return []

    invoice_ids = [row[0] for row in invoice_rows]

    cur.execute(
        """
        SELECT invoice_id, item, qty, unit_price
        FROM invoice_items
        WHERE invoice_id = ANY(%s);
        """,
        (invoice_ids,),
    )
    item_rows = cur.fetchall()

    cur.close()
    conn.close()

    invoice_map = {}
    for row in invoice_rows:
        inv_id, number, date, vendor, total = row
        invoice_map[inv_id] = {
            "invoice_number": number,
            "invoice_date": date,
            "vendor": vendor,
            "total_amount_due": total,
            "items": [],
        }

    for invoice_id, item, qty, price in item_rows:
        if invoice_id in invoice_map:
            invoice_map[invoice_id]["items"].append(
                {"item": item, "qty": qty, "unit_price": price}
            )

    return list(invoice_map.values())
