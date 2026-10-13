# E-Commerce Sales Analytics & Automated QA Platform

[![CI/CD Pipeline](https://github.com/your-username/ecommerce-sales-analytics-qa/actions/workflows/ci.yml/badge.svg)](https://github.com/your-username/ecommerce-sales-analytics-qa/actions)
![Python Version](https://img.shields.io/badge/Python-3.12-blue.svg)
![Test Coverage](https://img.shields.io/badge/Coverage-95.2%25-brightgreen.svg)
![Code Style](https://img.shields.io/badge/Code%20Style-Ruff-000000.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

An enterprise-grade, end-to-end **Data Engineering, Automated Testing, and Financial Analytics Platform** built to showcase production-level Python, SQL, ETL pipelines, PostgreSQL/SQLite database architecture, rigorous STLC methodologies, and CI/CD automation.

Designed to demonstrate technical excellence for a **Schneider Electric Graduate Engineer Trainee (GET)** role focused on **Software Testing, Quality Assurance Automation, and Digital Transformation**.

---

## 1. System Architecture

```mermaid
flowchart LR
    subgraph Extraction ["1. Ingestion"]
        A[Raw CSV\nUCI Online Retail] --> B[Extractor Module]
    end

    subgraph QA_Gate ["2. QA Validation Gate"]
        B --> C{Validation Engine}
        C -->|Valid Records| D[Transformer]
        C -->|Invalid / Dupes| E[Quarantine Audit Trail]
    end

    subgraph Warehouse ["3. Relational Warehouse"]
        D --> F[Idempotent DB Loader]
        F --> G[(dim_products)]
        F --> H[(dim_customers)]
        F --> I[(fact_transactions)]
        F --> J[(etl_audit_log)]
    end

    subgraph Analytics ["4. Dual-Verified KPIs"]
        I --> K[SQL Analytical Queries]
        K <-->|Assert Equality| L[Pandas Dual-Verifier]
    end

    subgraph UI ["5. Executive Telemetry"]
        K --> M[Streamlit & Plotly Dashboard]
    end
```

---

## 2. Key Features

- **Executable Data Quality & Quarantine Gate:** Automatically catches pricing anomalies (`UnitPrice <= 0`), missing primary keys, zero quantities, and duplicate records. Quarantines invalid records into `rejected_records.csv` with granular reason codes without dropping legitimate guest checkout revenue.
- **Idempotent Database Loading:** Uses deterministic SHA-256 natural composite key hashing (`record_id`). Consecutive pipeline re-runs on identical data skip existing records with zero record count or revenue inflation.
- **Dual-Verification Analytics (SQL vs Pandas):** Every SQL KPI (Gross Revenue, Total Refunds, Net Revenue, Completed Orders, AOV, Net Units) is mirrored by an independent Pandas calculation suite and mathematically verified to the penny across multiple date and regional filters.
- **Transactional Integrity:** Full ACID transaction handling with automated rollback via SQLAlchemy context managers (`session_scope`).
- **Automated QA & CI/CD Suite:** 27 automated unit, integration, and regression tests achieving **95.2% test coverage**, strict Ruff linting, and a GitHub Actions workflow running against an isolated PostgreSQL service container.
- **Executive Streamlit & Plotly Dashboard:** Modern dark-theme glassmorphism dashboard featuring real-time financial KPI cards, dual-axis revenue trends, top product performance, regional distribution, data quality health telemetry, and CSV data export.

---

## 3. Project Directory Structure

```text
e commerce dashboard/
├── .github/
│   └── workflows/
│       └── ci.yml                     # GitHub Actions CI/CD configuration
├── app/
│   ├── analytics/
│   │   ├── engine.py                  # SQL query runner with parameterized filtering
│   │   └── pandas_verifier.py         # Independent Pandas KPI calculation engine
│   ├── config/
│   │   └── settings.py                # Pydantic Settings & environment config
│   ├── dashboard/
│   │   ├── app.py                     # Streamlit web application
│   │   └── components.py              # Plotly interactive chart builders
│   ├── database/
│   │   ├── connection.py              # Engine factory, session lifecycle & transaction scopes
│   │   ├── loader.py                  # Idempotent database loader with upserts
│   │   └── models.py                  # SQLAlchemy ORM declarative models
│   ├── etl/
│   │   ├── extractor.py               # Robust CSV reader with encoding fallback
│   │   ├── pipeline.py                # Pipeline orchestrator & quality reporting
│   │   ├── transformer.py             # Type casting, financial metrics & hashing
│   │   └── validator.py               # Schema & business rule validation
│   └── utils/
│       └── logger.py                  # Structured console and file logger
├── data/
│   ├── processed/                     # Clean and quarantined CSV outputs
│   └── raw/                           # Raw ingested transactions (UCI Online Retail)
├── docs/
│   ├── architecture.md                # System design & Mermaid ERD diagrams
│   ├── dataset_specification.md       # Schema, business rules & acceptance criteria
│   ├── defect_reports.md              # IEEE 829 defect logs with RCA and regression fixes
│   ├── kpi_definitions.md             # Formal mathematical formulas for financial KPIs
│   └── test_plan.md                   # STP test strategy, levels, and entry/exit criteria
├── reports/                           # Generated Data Quality audit reports (JSON & MD)
├── scripts/
│   ├── init_db.py                     # Database DDL initialization script
│   ├── prepare_dataset.py             # UCI dataset downloader & fixture generator
│   └── run_pipeline.py                # Command-line entrypoint for the ETL pipeline
├── sql/
│   ├── queries/                       # Reusable analytical SQL query files
│   └── schema.sql                     # Pure SQL DDL schema definitions
├── test-data/                         # Deterministic synthetic test CSVs
├── tests/
│   ├── fixtures/                      # Test fixture files
│   ├── integration/                   # Database & SQL analytical correctness tests
│   ├── regression/                    # Defect regression tests (DEF-001, DEF-002, DEF-003)
│   └── unit/                          # Unit tests for extractor, validator, transformer
├── .env.example                       # Environment variable template
├── .gitignore                         # Git ignore configuration
├── pyproject.toml                     # Pytest, coverage, and Ruff configuration
├── requirements.txt                   # Locked project dependencies
└── README.md                          # Platform documentation
```

---

## 4. Installation & Setup

### Prerequisites
- Python 3.12+
- Git

### 1. Clone & Set Up Virtual Environment
```bash
# Clone the repository
git clone https://github.com/your-username/ecommerce-sales-analytics-qa.git
cd "ecommerce-sales-analytics-qa"

# Create a virtual environment
python -m venv .venv

# Activate the virtual environment
# Windows (PowerShell):
.\.venv\Scripts\Activate.ps1
# Linux / macOS:
source .venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### 2. Environment Configuration
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Default `.env` configuration uses SQLite for frictionless local development:
```ini
DATABASE_URL=sqlite:///data/ecommerce_analytics.db
RAW_DATA_PATH=data/raw/online_retail.csv
REJECTED_RECORDS_PATH=data/processed/rejected_records.csv
PROCESSED_DATA_PATH=data/processed/clean_retail_transactions.csv
REPORTS_DIR=reports
LOG_LEVEL=INFO
```
*Note: To run against PostgreSQL, simply update `DATABASE_URL` to:*
```ini
DATABASE_URL=postgresql+psycopg2://user:password@localhost:5432/ecommerce_db
```

### 3. Initialize Datasets & Database Schema
```bash
# Generate deterministic test fixtures and download real-world UCI Online Retail data:
python scripts/prepare_dataset.py

# Initialize database schema tables, indexes, and constraints:
python -m scripts.init_db
```

---

## 5. Execution Guide

### Run the ETL Pipeline via CLI
Execute the complete extraction, validation, transformation, and database loading process:

```bash
# Process and load synthetic test fixture:
python -m scripts.run_pipeline --input test-data/synthetic_transactions.csv --load-db

# Process and load full 50,000-row real UCI Online Retail dataset:
python -m scripts.run_pipeline --input data/raw/online_retail.csv --load-db
```

### Run the Streamlit Dashboard
Launch the interactive analytical dashboard:
```bash
streamlit run app/dashboard/app.py
```
Open [http://localhost:8501](http://localhost:8501) in your browser.

---

## 6. Testing, Code Quality & Coverage

Run the automated test suites using the project-specific virtual environment:

```bash
# 1. Run all tests (Unit, Integration, Regression) with full coverage report:
pytest --cov=app --cov-report=term-missing --cov-report=html

# 2. Run unit tests only:
pytest tests/unit/ -v

# 3. Run database integration and SQL correctness tests:
pytest tests/integration/ -v

# 4. Run regression tests for resolved defects:
pytest tests/regression/ -v

# 5. Run Ruff linter and code style checks:
ruff check .
ruff format --check .
```

### Test Results Summary:
- **Total Tests:** 27 passed (100% pass rate)
- **Unit Tests:** 15 passing
- **Integration Tests:** 9 passing
- **Regression Tests:** 3 passing
- **Overall Code Coverage:** **95.20%** (exceeds the 80% threshold)
- **Ruff Linting:** 0 errors, 0 warnings

---

## 7. Continuous Integration (CI/CD)

The GitHub Actions workflow (`.github/workflows/ci.yml`) executes on every push and pull request to `main`:
1. Checks out repository and sets up Python 3.12.
2. Spins up a containerized **PostgreSQL 16** service with health checks.
3. Installs locked project dependencies.
4. Executes **Ruff** linting and formatting validation.
5. Generates deterministic test fixtures.
6. Runs the **Unit Test Suite**.
7. Runs the **Regression Test Suite**.
8. Runs **Database Integration & SQL Correctness Tests** against the active PostgreSQL instance.
9. Executes an end-to-end pipeline run with database loading.
10. Publishes automated coverage artifacts (`coverage.xml`).

---

## 8. Defect Management Highlights

During the development lifecycle, real-world edge cases were captured and resolved following formal STLC procedures:
- **`DEF-2026-001` (Guest Checkout Null CustomerID):** Fixed `ValueError` during integer casting on missing `CustomerID` by adopting Pandas `Int64` nullable integers and declaring the database column nullable, preventing accidental revenue loss.
- **`DEF-2026-002` (Non-Idempotent Ingestion Inflation):** Resolved metric inflation upon repeated pipeline runs by implementing deterministic SHA-256 business key hashing (`record_id`) and pre-insert duplicate filtering.
- **`DEF-2026-003` (Stock Code Whitespace / Casing Fragmentation):** Normalized alphanumeric stock codes to uppercase trimmed strings to prevent dimension table fragmentation.

Full defect reports with Root Cause Analysis (RCA) and reproduction steps are documented in [`docs/defect_reports.md`](docs/defect_reports.md).

---

## 9. Known Limitations & Future Improvements

1. **Streaming Data Ingestion:** Current pipeline operates as scheduled micro-batches. Future enhancement: integrate Apache Kafka or AWS Kinesis with FastAPI for event-driven real-time stream ingestion.
2. **SCD Type 2 (Slowly Changing Dimensions):** `dim_products` currently records the latest unit price. Adding `valid_from` and `valid_to` timestamps would enable historical product pricing trend tracking.
3. **Advanced ML Forecasting:** Historical transaction data can be fed into time-series forecasting models (ARIMA / Prophet) to predict next-quarter inventory demand and return rates.

---

## 10. License

This project is licensed under the MIT License.
