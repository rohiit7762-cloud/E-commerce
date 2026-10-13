"""ETL Pipeline Orchestrator.

Coordinates extraction, validation, transformation, rejected records quarantine,
and data quality reporting.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

import pandas as pd

from app.etl.extractor import extract_csv
from app.etl.transformer import transform_records
from app.etl.validator import validate_records
from app.utils.logger import setup_logger

logger = setup_logger("pipeline")


class ETLResult:
    """Encapsulates the output of an ETL run."""

    def __init__(
        self,
        raw_count: int,
        accepted_df: pd.DataFrame,
        rejected_df: pd.DataFrame,
        validation_metrics: Dict[str, Any],
        report_path: Optional[str] = None,
    ):
        self.raw_count = raw_count
        self.accepted_df = accepted_df
        self.rejected_df = rejected_df
        self.validation_metrics = validation_metrics
        self.report_path = report_path

    @property
    def accepted_count(self) -> int:
        return len(self.accepted_df)

    @property
    def rejected_count(self) -> int:
        return len(self.rejected_df)

    @property
    def gross_revenue(self) -> float:
        if self.accepted_df.empty:
            return 0.0
        sales = self.accepted_df[~self.accepted_df["is_cancellation"]]
        return float(round(sales["line_total"].sum(), 2))

    @property
    def refund_total(self) -> float:
        if self.accepted_df.empty:
            return 0.0
        refunds = self.accepted_df[self.accepted_df["is_cancellation"]]
        return float(round(refunds["line_total"].sum(), 2))

    @property
    def net_revenue(self) -> float:
        return float(round(self.gross_revenue + self.refund_total, 2))


def generate_quality_report(
    result: ETLResult,
    output_dir: str = "reports",
    run_id: Optional[str] = None,
) -> str:
    """Generate and persist a detailed JSON and Markdown validation report."""
    reports_path = Path(output_dir)
    reports_path.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    report_tag = run_id or timestamp
    json_path = reports_path / f"dq_report_{report_tag}.json"
    md_path = reports_path / f"dq_report_{report_tag}.md"

    report_payload = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "run_id": report_tag,
        "summary": {
            "total_raw_records": result.raw_count,
            "accepted_records": result.accepted_count,
            "rejected_records": result.rejected_count,
            "acceptance_rate_pct": round(
                (result.accepted_count / result.raw_count * 100) if result.raw_count > 0 else 0.0, 2
            ),
        },
        "financial_reconciliation": {
            "gross_revenue": result.gross_revenue,
            "refund_total": result.refund_total,
            "net_revenue": result.net_revenue,
        },
        "rejection_breakdown": result.validation_metrics.get("reasons", {}),
    }

    with open(json_path, "w", encoding="utf-8") as jf:
        json.dump(report_payload, jf, indent=2)

    # Markdown representation
    md_content = f"""# Data Quality & Validation Audit Report
**Run ID:** `{report_tag}`
**Generated At:** {report_payload["timestamp_utc"]}

## 1. Executive Summary
- **Total Ingested Records:** {result.raw_count:,}
- **Accepted Clean Records:** {result.accepted_count:,} ({report_payload["summary"]["acceptance_rate_pct"]}%)
- **Quarantined Records:** {result.rejected_count:,}

## 2. Financial Metrics Reconciliation
| Metric | Amount |
| :--- | :--- |
| **Gross Revenue (Completed Sales)** | £{result.gross_revenue:,.2f} |
| **Total Refunds / Returns** | £{result.refund_total:,.2f} |
| **Net Revenue** | **£{result.net_revenue:,.2f}** |

## 3. Quarantine Reason Breakdown
| Rejection Reason | Record Count |
| :--- | :--- |
"""
    for reason, count in report_payload["rejection_breakdown"].items():
        md_content += f"| `{reason}` | {count:,} |\n"

    if not report_payload["rejection_breakdown"]:
        md_content += "| *None (100% clean)* | 0 |\n"

    with open(md_path, "w", encoding="utf-8") as mf:
        mf.write(md_content)

    logger.info(f"Quality report persisted to {json_path} and {md_path}")
    return str(json_path)


def run_etl(
    input_path: str,
    output_clean_path: Optional[str] = None,
    output_rejected_path: Optional[str] = None,
    reports_dir: str = "reports",
    nrows: Optional[int] = None,
) -> ETLResult:
    """
    Execute full ETL cycle from raw CSV to validated & transformed outputs.

    Args:
        input_path: Path to source CSV.
        output_clean_path: Optional path to save cleaned CSV.
        output_rejected_path: Optional path to save quarantined CSV.
        reports_dir: Directory to save audit reports.
        nrows: Optional row limit for sampling.

    Returns:
        ETLResult: Result containing accepted DataFrame, rejected DataFrame, and audit metrics.
    """
    logger.info(f"=== Starting ETL Pipeline Execution (Source: {input_path}) ===")

    # 1. Extraction
    raw_df = extract_csv(input_path, nrows=nrows)
    raw_count = len(raw_df)

    # 2. Validation & Quarantine
    accepted_raw_df, rejected_df, validation_metrics = validate_records(raw_df)

    # 3. Transformation
    transformed_df = transform_records(accepted_raw_df)

    # 4. Optional CSV persistence for downstream consumers
    if output_clean_path:
        out_clean = Path(output_clean_path)
        out_clean.parent.mkdir(parents=True, exist_ok=True)
        transformed_df.to_csv(out_clean, index=False)
        logger.info(f"Saved cleaned records to {out_clean}")

    if output_rejected_path and not rejected_df.empty:
        out_rejected = Path(output_rejected_path)
        out_rejected.parent.mkdir(parents=True, exist_ok=True)
        rejected_df.to_csv(out_rejected, index=False)
        logger.info(f"Saved {len(rejected_df)} quarantined records to {out_rejected}")

    # 5. Result compilation & Quality Report
    result = ETLResult(
        raw_count=raw_count,
        accepted_df=transformed_df,
        rejected_df=rejected_df,
        validation_metrics=validation_metrics,
    )

    report_path = generate_quality_report(result, output_dir=reports_dir)
    result.report_path = report_path

    logger.info(
        f"=== ETL Pipeline Complete. Clean: {result.accepted_count}, "
        f"Rejected: {result.rejected_count}, Net Revenue: £{result.net_revenue:,.2f} ==="
    )
    return result
