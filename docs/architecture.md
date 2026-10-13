# System Architecture & Technical Design

## 1. High-Level Architecture Overview

The **E-commerce Sales Analytics & Automated QA Platform** is an enterprise data engineering and quality assurance solution that extracts, validates, transforms, loads, and visualizes retail transactions with dual-verified financial reconciliation.

```mermaid
flowchart TD
    subgraph Ingestion ["1. Ingestion & Extraction"]
        RawCSV["Raw Transactions CSV\n(UCI Online Retail / Fixtures)"] --> Extractor["Extractor Module\n(app/etl/extractor.py)"]
    end

    subgraph QualityGate ["2. Automated Quality Assurance Gate"]
        Extractor --> Validator["Data Quality Validator\n(app/etl/validator.py)"]
        Validator -->|Failed Rules & Duplicates| Quarantine["Quarantine CSV &\nReason Tagging"]
        Validator -->|Accepted Clean Data| Transformer["Transformation Engine\n(app/etl/transformer.py)"]
        Validator --> DQReport["Data Quality Audit Report\n(JSON & Markdown)"]
    end

    subgraph Transformation ["3. Transformation & Hashing"]
        Transformer --> LineTotal["Line Total Calculation"]
        Transformer --> Cancellation["Cancellation & Return Flagging"]
        Transformer --> HashGen["Deterministic SHA-256 Key Hashing"]
    end

    subgraph Persistence ["4. Relational Data Warehouse"]
        HashGen --> Loader["Idempotent DB Loader\n(app/database/loader.py)"]
        Loader --> DimProd[("dim_products\n(Dimension)")]
        Loader --> DimCust[("dim_customers\n(Dimension)")]
        Loader --> FactTrans[("fact_transactions\n(Fact Table)")]
        Loader --> AuditLog[("etl_audit_log\n(Execution Audit)")]
    end

    subgraph Analytics ["5. Dual-Verified Analytics"]
        FactTrans --> SQLQueries["Production SQL Queries\n(sql/queries/*.sql)"]
        SQLQueries --> AnalyticsEngine["Analytics Engine\n(app/analytics/engine.py)"]
        AnalyticsEngine <-->|Dual Verification| PandasVerifier["Independent Pandas\nKPI Verifier"]
    end

    subgraph Presentation ["6. Presentation Layer"]
        AnalyticsEngine --> Streamlit["Streamlit Dashboard\n(Plotly Visuals)"]
    end
```

---

## 2. Relational Entity-Relationship Diagram (ERD)

```mermaid
erDiagram
    dim_products ||--o{ fact_transactions : "contains"
    dim_customers ||--o{ fact_transactions : "purchases"

    dim_products {
        varchar(50) stock_code PK
        varchar(255) description
        numeric latest_unit_price
        timestamp updated_at
    }

    dim_customers {
        int customer_id PK
        varchar(100) country
        timestamp created_at
    }

    fact_transactions {
        varchar(64) record_id PK
        varchar(20) invoice_no
        varchar(50) stock_code FK
        int customer_id FK "Nullable for Guest Checkouts"
        int quantity
        numeric unit_price
        numeric line_total
        timestamp invoice_date
        varchar(100) country
        boolean is_cancellation
        varchar(7) year_month
        timestamp loaded_at
    }

    etl_audit_log {
        varchar(64) run_id PK
        varchar(255) source_file
        int raw_count
        int accepted_count
        int rejected_count
        int inserted_count
        int skipped_count
        numeric gross_revenue
        numeric net_revenue
        varchar(20) status
        timestamp executed_at
    }
```

---

## 3. Idempotent Ingestion Design
To guarantee that pipelines can be triggered on an automated cron schedule or CI/CD re-run without inflating metrics:
1. Every record receives a surrogate business key generated via SHA-256 over:
   $$\text{Hash} = \text{SHA256}(\text{InvoiceNo} \parallel \text{StockCode} \parallel \text{InvoiceDate} \parallel \text{Quantity} \parallel \text{UnitPrice} \parallel \text{CustomerID})$$
2. Prior to database insertion, existing `record_id`s in the warehouse are queried in indexed batches.
3. Only genuinely unrecorded entries are inserted. Existing entries are incremented in the `skipped_count` audit metric.
4. Total fact table rows remain strictly constant on consecutive runs.
