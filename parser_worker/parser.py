import re
from datetime import datetime


def extract_invoice_data(text):
    try:
        invoice_number = re.search(r"Invoice:\s*(\S+)", text).group(1)
        invoice_date_str = re.search(
            r"Date:\s*(\d{4}-\d{2}-\d{2})", text
        ).group(1)
        invoice_date = datetime.strptime(invoice_date_str, "%Y-%m-%d").date()
        vendor = re.search(r"Vendor:\s*(.+)", text).group(1).strip()

        items_section = re.search(
            r"Item Qty Unit Price Total\n(.+?)Total Amount Due:",
            text,
            re.DOTALL,
        )
        if not items_section:
            raise ValueError("Could not find items section.")

        item_lines = [
            line.strip()
            for line in items_section.group(1).strip().split("\n")
            if line.strip()
        ]
        items = []
        for line in item_lines:
            match = re.match(
                r"(.+?)\s+(\d+)\s+\$?([\d.]+)\s+\$?([\d.]+)", line
            )
            if not match:
                raise ValueError(f"Failed to parse item line: {line}")
            item, qty, unit_price, total = match.groups()
            items.append(
                {
                    "item": item.strip(),
                    "qty": int(qty),
                    "unit_price": float(unit_price),
                    "item_total": float(total),
                }
            )

        total_due_match = re.search(r"Total Amount Due:\s*\$([\d.]+)", text)
        if not total_due_match:
            raise ValueError("Total amount due not found.")
        total_amount_due = float(total_due_match.group(1))

        return {
            "invoice_number": invoice_number,
            "invoice_date": invoice_date,
            "vendor": vendor,
            "items": items,
            "total_amount_due": total_amount_due,
        }

    except Exception as e:
        raise ValueError(f"Invoice parsing failed: {e}")
