-- =============================================================================
-- AgroFactura Cloud - Database Initialization Script
-- Executed on container startup by postgres:16-alpine entrypoint
-- =============================================================================

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    cif_nif VARCHAR(20) NOT NULL,
    address VARCHAR(255),
    regime VARCHAR(50) DEFAULT 'REAGP' NOT NULL,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS customers (
    id SERIAL PRIMARY KEY,
    farmer_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    company_name VARCHAR(255) NOT NULL,
    cif_nif VARCHAR(20) NOT NULL,
    email VARCHAR(255) NOT NULL,
    address VARCHAR(255) NOT NULL,
    status VARCHAR(50) DEFAULT 'active' NOT NULL,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_customers_cif ON customers(cif_nif);

CREATE TABLE IF NOT EXISTS invoice_sequences (
    year INTEGER PRIMARY KEY,
    last_sequence INTEGER DEFAULT 0 NOT NULL
);

CREATE TABLE IF NOT EXISTS invoices (
    id SERIAL PRIMARY KEY,
    farmer_id INTEGER NOT NULL REFERENCES users(id),
    customer_id INTEGER NOT NULL REFERENCES customers(id),
    invoice_number VARCHAR(50) UNIQUE NOT NULL,
    issue_date VARCHAR(20) NOT NULL,
    tax_regime VARCHAR(50) DEFAULT 'REAGP' NOT NULL,
    taxable_base DOUBLE PRECISION NOT NULL,
    agricultural_compensation_pct DOUBLE PRECISION DEFAULT 12.0 NOT NULL,
    agricultural_compensation_amount DOUBLE PRECISION DEFAULT 0.0 NOT NULL,
    withholding_tax_pct DOUBLE PRECISION DEFAULT 2.0 NOT NULL,
    withholding_tax_amount DOUBLE PRECISION DEFAULT 0.0 NOT NULL,
    total_amount DOUBLE PRECISION NOT NULL,
    status VARCHAR(50) DEFAULT 'issued' NOT NULL,
    drive_url VARCHAR(500),
    emailed_to VARCHAR(255),
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_invoices_number ON invoices(invoice_number);

CREATE TABLE IF NOT EXISTS invoice_items (
    id SERIAL PRIMARY KEY,
    invoice_id INTEGER NOT NULL REFERENCES invoices(id) ON DELETE CASCADE,
    description VARCHAR(255) NOT NULL,
    quantity DOUBLE PRECISION NOT NULL,
    unit_price DOUBLE PRECISION NOT NULL,
    subtotal DOUBLE PRECISION NOT NULL
);
