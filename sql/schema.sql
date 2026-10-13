-- =============================================================================
-- E-commerce Sales Analytics & Automated QA Platform
-- Relational Schema Definition (PostgreSQL & SQLite Compatible)
-- =============================================================================

-- 1. Product Dimension Table
CREATE TABLE IF NOT EXISTS dim_products (
    stock_code VARCHAR(50) PRIMARY KEY,
    description VARCHAR(255) NOT NULL,
    latest_unit_price NUMERIC(10, 2) NOT NULL,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 2. Customer Dimension Table
CREATE TABLE IF NOT EXISTS dim_customers (
    customer_id INTEGER PRIMARY KEY,
    country VARCHAR(100) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 3. Transaction Fact Table
CREATE TABLE IF NOT EXISTS fact_transactions (
    record_id VARCHAR(64) PRIMARY KEY,
    invoice_no VARCHAR(20) NOT NULL,
    stock_code VARCHAR(50) NOT NULL,
    customer_id INTEGER NULL,
    quantity INTEGER NOT NULL,
    unit_price NUMERIC(10, 2) NOT NULL,
    line_total NUMERIC(10, 2) NOT NULL,
    invoice_date TIMESTAMP NOT NULL,
    country VARCHAR(100) NOT NULL,
    is_cancellation BOOLEAN NOT NULL DEFAULT FALSE,
    year_month VARCHAR(7) NOT NULL,
    loaded_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_transaction_product FOREIGN KEY (stock_code) REFERENCES dim_products (stock_code),
    CONSTRAINT fk_transaction_customer FOREIGN KEY (customer_id) REFERENCES dim_customers (customer_id)
);

-- Indexes for analytical query acceleration
CREATE INDEX IF NOT EXISTS idx_fact_invoice_no ON fact_transactions(invoice_no);
CREATE INDEX IF NOT EXISTS idx_fact_invoice_date ON fact_transactions(invoice_date);
CREATE INDEX IF NOT EXISTS idx_fact_year_month ON fact_transactions(year_month);
CREATE INDEX IF NOT EXISTS idx_fact_customer_id ON fact_transactions(customer_id);
CREATE INDEX IF NOT EXISTS idx_fact_stock_code ON fact_transactions(stock_code);
CREATE INDEX IF NOT EXISTS idx_fact_country ON fact_transactions(country);

-- 4. ETL & Data Quality Audit Log Table
CREATE TABLE IF NOT EXISTS etl_audit_log (
    run_id VARCHAR(64) PRIMARY KEY,
    source_file VARCHAR(255) NOT NULL,
    raw_count INTEGER NOT NULL,
    accepted_count INTEGER NOT NULL,
    rejected_count INTEGER NOT NULL,
    inserted_count INTEGER NOT NULL,
    skipped_count INTEGER NOT NULL,
    gross_revenue NUMERIC(12, 2) NOT NULL,
    net_revenue NUMERIC(12, 2) NOT NULL,
    status VARCHAR(20) NOT NULL,
    executed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
