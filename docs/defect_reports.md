# Quality Assurance & Defect Management Reports

This document logs real software and data quality defects identified, analyzed, resolved, and safeguarded with automated regression tests during the platform's development life cycle (STLC).

---

## Defect Log 001: Guest Checkout CustomerID Type Coercion Failure

| Attribute | Specification |
| :--- | :--- |
| **Defect ID** | `DEF-2026-001` |
| **Title** | Guest Checkout CustomerID Type Coercion Failure and Accidental Record Dropping |
| **Severity** | **High** (Caused pipeline exception or potential revenue data loss) |
| **Priority** | **P1 (Immediate Fix Required)** |
| **Component** | `app.etl.transformer` & `app.database.models` |
| **Status** | **Closed / Verified by Regression Test** |

### 1. Description & Business Impact
In real-world e-commerce systems (including UCI Online Retail), unregistered guest shoppers complete purchases without creating an account. In raw CSV extracts, `CustomerID` for these transactions is blank (`NaN`).
During initial transformation, casting `df['CustomerID'].astype(int)` immediately raised:
```text
ValueError: Cannot convert non-finite values (NA or inf) to integer
```
Furthermore, filtering out `NaN` rows via `df[df['CustomerID'].notna()]` resulted in the silent loss of thousands of pounds in legitimate sales revenue, directly falsifying corporate financial metrics.

### 2. Steps to Reproduce
1. Ingest an order line where `CustomerID` is empty/null (e.g., `InvoiceNo: 100005, Quantity: 2, UnitPrice: 25.00, CustomerID: None`).
2. Execute the transformation module without nullable integer handling.
3. Observe `ValueError` or the omission of the transaction from the accepted dataset.

### 3. Expected Result
The record must be accepted and preserved in `fact_transactions` with `customer_id = NULL`. Total revenue must include the £50.00 guest sale.

### 4. Actual Result
Pipeline crashed with `ValueError`, or if filtered, £50.00 was dropped.

### 5. Root Cause Analysis (RCA)
Standard NumPy/Pandas `int` type does not support missing values (`NaN`). Converting float columns containing `NaN` to `int` is disallowed in Python. In the relational schema, `customer_id` must explicitly permit `NULL`.

### 6. Remediation & Fix
1. In `app/etl/transformer.py`, converted CustomerID using Pandas' modern nullable integer extension type:
   ```python
   customer_series = pd.to_numeric(df["CustomerID"], errors="coerce")
   df["CustomerID"] = customer_series.astype("Int64")
   ```
2. In `app/database/models.py`, defined `customer_id` as `Column(Integer, ForeignKey("dim_customers.customer_id"), nullable=True)`.
3. In SQL analytics, grouped guest transactions into a dedicated `'GUEST'` bucket to avoid skewing retention metrics.

### 7. Regression Test
- **Test File:** `tests/regression/test_defect_regression.py`
- **Test Case:** `test_defect_001_guest_checkout_null_safety`
- **Outcome:** **PASSED** (asserts guest transactions are preserved with exact line totals).

---

## Defect Log 002: Pipeline Re-execution Record Count & Revenue Inflation

| Attribute | Specification |
| :--- | :--- |
| **Defect ID** | `DEF-2026-002` |
| **Title** | Non-Idempotent Database Loading Leading to Record Duplication on Re-runs |
| **Severity** | **Critical** (Financial KPI distortion through double-counting) |
| **Priority** | **P1 (Immediate Fix Required)** |
| **Component** | `app.database.loader` |
| **Status** | **Closed / Verified by Regression Test** |

### 1. Description & Business Impact
If an automated CI/CD pipeline or scheduled cron job re-triggers an ingestion batch, identical transaction records must not be inserted multiple times. Without an idempotency check, re-running the pipeline on identical source data doubles the fact table rows and doubles reported gross and net revenue.

### 2. Steps to Reproduce
1. Ingest `test-data/synthetic_transactions.csv` into the database (7 accepted rows, Net Revenue: £270.00).
2. Execute `python -m scripts.run_pipeline --input test-data/synthetic_transactions.csv --load-db` a second time.
3. Query `SELECT SUM(line_total) FROM fact_transactions`.

### 3. Expected Result
`fact_transactions` count remains strictly 7. Net Revenue remains strictly £270.00. The loader reports `inserted_count = 0` and `skipped_count = 7`.

### 4. Actual Result
Without idempotency checks, row count doubled to 14, and net revenue inflated to £540.00.

### 5. Root Cause Analysis (RCA)
The table lacked a natural business surrogate key, and the loader relied on blind appending without querying existing records.

### 6. Remediation & Fix
1. Introduced `generate_record_hash(row)` in `app/etl/transformer.py`, which derives a deterministic SHA-256 hash (`record_id`) from immutable composite business attributes:
   `InvoiceNo | StockCode | InvoiceDate | Quantity | UnitPrice | CustomerID`.
2. In `app/database/loader.py`, partitioned incoming batch into existing IDs vs new IDs. Only unrecorded IDs are appended.
3. Logged skipped rows in `etl_audit_log`.

### 7. Regression Test
- **Test File:** `tests/regression/test_defect_regression.py`
- **Test Case:** `test_defect_002_repeated_loading_does_not_inflate_revenue`
- **Outcome:** **PASSED** (asserts run 2 inserts 0 rows, skips duplicate batch, and revenue remains unchanged).

---

## Defect Log 003: Alphanumeric Stock Code Whitespace and Case Fragmentation

| Attribute | Specification |
| :--- | :--- |
| **Defect ID** | `DEF-2026-003` |
| **Title** | Unsanitized Stock Code Casing and Padding Fragmented Product Dimension |
| **Severity** | **Medium** |
| **Priority** | **P2** |
| **Component** | `app.etl.transformer` |
| **Status** | **Closed / Verified by Regression Test** |

### 1. Description & Business Impact
In raw ERP data, product stock codes such as `' 85123A '`, `'85123a'`, and `'85123A'` represent the exact same SKU. Without standardization, the relational database inserted multiple entries into `dim_products`, breaking foreign key lookups and splitting analytics for a single product across multiple rows.

### 2. Remediation & Fix
Normalized all stock codes in `transformer.py`:
```python
df["StockCode"] = df["StockCode"].astype(str).str.strip().str.upper()
```

### 3. Regression Test
- **Test File:** `tests/regression/test_defect_regression.py`
- **Test Case:** `test_defect_003_whitespace_and_casing_normalization`
- **Outcome:** **PASSED**.
