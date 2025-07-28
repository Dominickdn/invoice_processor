CREATE TABLE IF NOT EXISTS invoices (
    id SERIAL PRIMARY KEY,
    invoice_number TEXT NOT NULL UNIQUE,
    invoice_date DATE,
    vendor TEXT,
    total_amount_due NUMERIC,
    insert_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    file_name TEXT
);

CREATE TABLE IF NOT EXISTS invoice_items (
    id SERIAL PRIMARY KEY,
    invoice_id INTEGER REFERENCES invoices(id) ON DELETE CASCADE,
    item TEXT,
    qty INTEGER,
    unit_price NUMERIC
);