# E-Commerce KPI Definitions & Mathematical Formulas

This document defines the exact business formulas and aggregation rules implemented in SQL and verified in Python.

---

## 1. Gross Revenue
- **Business Definition:** Total monetary value of completed sales orders before factoring in refunds, discounts, or cancellations.
- **SQL Formula:**
  $$\text{Gross Revenue} = \sum (\text{Quantity} \times \text{UnitPrice}) \quad \text{where } \text{is\_cancellation} = \text{FALSE}$$
- **Verification Rule:** Line totals for cancellations (`is_cancellation = TRUE` or `Quantity < 0`) are excluded from Gross Revenue.

---

## 2. Total Refund Value
- **Business Definition:** Total monetary value credited or refunded to customers due to product returns or cancelled orders.
- **SQL Formula:**
  $$\text{Total Refunds} = \sum (\text{Quantity} \times \text{UnitPrice}) \quad \text{where } \text{is\_cancellation} = \text{TRUE}$$
- **Verification Rule:** Expressed as a negative number or absolute credit depending on financial context. In this platform, refund totals are negative values.

---

## 3. Net Revenue
- **Business Definition:** True net earnings from sales after deducting all refunds and cancellations.
- **SQL Formula:**
  $$\text{Net Revenue} = \text{Gross Revenue} + \text{Total Refunds} \equiv \sum \text{line\_total}$$
- **Verification Rule:** Must equal the algebraic sum of all accepted records' `line_total` values.

---

## 4. Completed Orders (Sales Invoices)
- **Business Definition:** Count of distinct purchase transactions completed by customers.
- **SQL Formula:**
  $$\text{Completed Orders} = \text{COUNT}(\text{DISTINCT } \text{InvoiceNo}) \quad \text{where } \text{is\_cancellation} = \text{FALSE}$$
- **Anti-Pattern Prevention:** Multiple line items with the same `InvoiceNo` are deduplicated using `DISTINCT` to prevent transaction overcounting.

---

## 5. Average Order Value (AOV)
- **Business Definition:** Average monetary gross spent per completed sales invoice.
- **SQL Formula:**
  $$\text{AOV} = \frac{\text{Gross Revenue}}{\text{Completed Orders}}$$
- **Edge Case Handling:** If `Completed Orders == 0`, AOV evaluates safely to `0.00` (prevents division by zero).

---

## 6. Net Units Sold
- **Business Definition:** Net physical units delivered to customers (gross units sold minus returned units).
- **SQL Formula:**
  $$\text{Net Units Sold} = \sum \text{Quantity}$$

---

## 7. Customer Purchase Frequency & Monetary Value
- **Business Definition:** Number of distinct purchase transactions executed per customer ID.
- **SQL Formula:**
  $$\text{Frequency} = \text{COUNT}(\text{DISTINCT } \text{InvoiceNo}) \quad \text{GROUP BY } \text{CustomerID}$$
- **Guest Checkout Handling:** Transactions where `customer_id IS NULL` are grouped into a dedicated `'GUEST'` bucket to avoid distorting registered customer retention metrics.
