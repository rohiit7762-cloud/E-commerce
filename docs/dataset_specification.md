# E-commerce Dataset Specification & Data Quality Rules

## 1. Overview
This platform ingests transnational e-commerce sales data based on the **UCI Machine Learning Repository Online Retail Dataset** (and matching synthetic enterprise fixtures). The dataset captures all transactions occurring between an online UK-based retailer and international customers.

## 2. Dataset Schema

| Field Name | Raw Type | Target Type | Nullable? | Description & Business Meaning |
| :--- | :--- | :--- | :--- | :--- |
| `InvoiceNo` | String / Int | `VARCHAR(20)` | **No** | 6-digit integer uniquely assigned to each transaction. If the code begins with `'C'`, it indicates a cancellation / credit memo. |
| `StockCode` | String | `VARCHAR(20)` | **No** | 5-digit or alphanumeric unique identifier for each distinct product/item. |
| `Description`| String | `VARCHAR(255)`| Yes | Product name / description. If missing, imputed with `'UNKNOWN PRODUCT'`. |
| `Quantity` | Integer | `INTEGER` | **No** | The quantity of the item per transaction. Positive for sales; negative for cancellations and returns. Must not be zero. |
| `InvoiceDate`| Datetime/Str | `TIMESTAMP` | **No** | Date and time when the transaction was generated. Format: `YYYY-MM-DD HH:MM:SS`. |
| `UnitPrice` | Float / Num | `NUMERIC(10, 2)`| **No** | Unit price of the product. Must be strictly positive (`> 0.00`). |
| `CustomerID` | Float / Int | `INTEGER` | Yes | 5-digit integral number uniquely identifying the customer. Unregistered guest checkouts have NULL CustomerID. |
| `Country` | String | `VARCHAR(100)`| **No** | Name of the country where each customer resides. Defaults to `'Unknown'` if missing. |

## 3. Derived Analytical Fields
The ETL pipeline computes the following derived fields for every accepted record:
- `line_total`: `Quantity * UnitPrice` (signed: positive for sales, negative for refunds/cancellations).
- `is_cancellation`: Boolean flag (`TRUE` if `InvoiceNo` starts with `'C'` or `Quantity < 0`).
- `year_month`: String format `YYYY-MM` extracted from `InvoiceDate` for time-series aggregation.
- `processed_at`: Ingestion timestamp for data auditability.

## 4. Data Quality & Cleaning Rules

### Acceptance Criteria (Clean Records):
1. **Mandatory Keys**: `InvoiceNo` and `StockCode` must be present and non-empty.
2. **Valid Quantities**: `Quantity != 0`. (A transaction with quantity 0 has no financial substance and is rejected).
3. **Valid Pricing**: `UnitPrice > 0.00`. Negative prices represent bad debt adjustments or system errors; zero prices represent pricing glitches or unbilled samples. Both are quarantined.
4. **Valid Dates**: `InvoiceDate` must parse into a valid timestamp.

### Quality Handling Rules:
1. **Missing CustomerID**: Retained! In e-commerce, guest checkouts contribute genuine revenue. Discarding them would artificially depress revenue and violate business reporting integrity. For customer-frequency KPIs, guest checkouts are evaluated separately from identified customer accounts.
2. **Missing Description**: Retained and imputed with `'UNKNOWN PRODUCT'` to protect financial reconciliation.
3. **Exact Duplicates**: Identified and deduplicated. Only the first occurrence is kept; duplicate instances are logged to the quarantine audit trail.
4. **Cancellations / Returns**: Preserved with `is_cancellation = TRUE` and negative quantity/revenue. Net revenue is defined as `Gross Revenue + Refund Total` (where Refund Total is negative).
5. **Rejected Records Quarantine**: All records failing validation are written to `data/processed/rejected_records.csv` alongside a detailed rejection reason code (e.g., `MISSING_INVOICE_NO`, `INVALID_UNIT_PRICE`, `ZERO_QUANTITY`, `DUPLICATE_ROW`).

## 5. Audit & Validation Metrics
Every pipeline execution generates a summary report:
- Total Raw Rows Ingested
- Valid Records Accepted
- Duplicate Rows Removed
- Rejected Records by Reason Category
- Gross Revenue, Cancellation Value, and Net Revenue Reconciliation
