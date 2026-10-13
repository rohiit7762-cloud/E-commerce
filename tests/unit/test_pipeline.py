"""Unit tests for the full ETL pipeline execution."""

import json
from pathlib import Path

from app.etl.pipeline import run_etl

FIXTURE_PATH = "test-data/synthetic_transactions.csv"


def test_pipeline_on_synthetic_fixture(tmp_path: Path):
    clean_out = tmp_path / "clean.csv"
    rejected_out = tmp_path / "rejected.csv"
    reports_out = tmp_path / "reports"

    result = run_etl(
        input_path=FIXTURE_PATH,
        output_clean_path=str(clean_out),
        output_rejected_path=str(rejected_out),
        reports_dir=str(reports_out),
    )

    # 1. Row count assertions
    assert result.raw_count == 13
    assert result.accepted_count == 7
    assert result.rejected_count == 6
    assert result.validation_metrics["duplicate_records"] == 1

    # 2. Financial assertions
    assert result.gross_revenue == 280.00
    assert result.refund_total == -10.00
    assert result.net_revenue == 270.00

    # 3. File existence assertions
    assert clean_out.exists()
    assert rejected_out.exists()
    assert result.report_path is not None
    assert Path(result.report_path).exists()

    # 4. Report payload verification
    with open(result.report_path, "r", encoding="utf-8") as f:
        report_data = json.load(f)

    assert report_data["summary"]["total_raw_records"] == 13
    assert report_data["summary"]["accepted_records"] == 7
    assert report_data["summary"]["rejected_records"] == 6
    assert report_data["financial_reconciliation"]["gross_revenue"] == 280.00
    assert report_data["financial_reconciliation"]["refund_total"] == -10.00
    assert report_data["financial_reconciliation"]["net_revenue"] == 270.00
