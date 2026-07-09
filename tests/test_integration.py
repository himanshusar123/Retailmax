"""
================================================================================
RetailMax Enterprise Data Platform

Module:      tests/test_integration.py
Purpose:     End-to-End Integration tests verifying the full ETL Pipeline.
Author:      Himanshu Sardana
Copyright:   (c) 2026 RetailMax Corp. All rights reserved.
================================================================================
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

from analytics import BusinessAnalyticsEngine
from api_service import APIServiceClient
from data_transformer import DataTransformer
from database import DatabaseHandler
from db_migrator import DatabaseMigrator
from report_generator import ExecutiveReportGenerator


def test_full_pipeline_integration(tmp_path: Path) -> None:
    """Runs the complete synchronous ETL pipeline end-to-end.

    Verifies that files are successfully written, databases are populated,
    and output reports are generated.
    """
    # 1. Prepare temp paths
    temp_csv = tmp_path / "employees.csv"
    temp_db = tmp_path / "retailmax.db"
    temp_charts_dir = tmp_path / "charts"
    temp_reports_dir = tmp_path / "reports"

    # Write a small baseline CSV file
    baseline_content = (
        "EmployeeID,Name,Department,Designation,Salary,JoiningDate,PerformanceScore\n"
        "1001,John Baseline,Engineering,Lead,120000.00,2023-05-15,4\n"
        "1002,Jane Baseline,HR,Manager,90000.00,2024-02-10,5\n"
    )
    with open(temp_csv, "w", encoding="utf-8") as f:
        f.write(baseline_content)

    # 2. Extract & Load baseline to DB
    migrator = DatabaseMigrator(csv_path=temp_csv, db_path=temp_db)
    baseline_count, _ = migrator.migrate()
    assert baseline_count == 2

    # 3. Pull & Transform API Users (mocked)
    mock_api_users = [
        {
            "id": 1,
            "name": "Alice API",
            "username": "aapi",
            "email": "alice@retailmax.com",
            "address": {"city": "Pune"},
            "company": {"bs": "deliver corporate sales"},
        }
    ]

    with patch("requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_api_users
        mock_get.return_value = mock_response

        # Fetch
        client = APIServiceClient()
        raw_users = client.fetch_raw_employees()

        # Transform (Flat and Offset)
        transformer = DataTransformer()
        transformed = transformer.transform_raw_payload(raw_users)
        assert len(transformed) == 1
        assert transformed[0].employee_id == 2001
        assert transformed[0].name == "Alice API"

        # Load API records into SQLite DB
        db = DatabaseHandler(str(temp_db))
        db.insert_employees_batch(transformed)

    # Verify all records merged (2 baseline + 1 API = 3 total)
    all_employees = db.get_all_employees()
    assert len(all_employees) == 3
    assert any(emp.name == "Alice API" for emp in all_employees)

    # 4. Run Pandas analytics on the SQLite DB
    analytics = BusinessAnalyticsEngine(db_path=temp_db, csv_path=temp_csv)
    analytics.charts_dir = temp_charts_dir
    df = analytics.load_cleaned_dataframe()
    assert len(df) == 3

    kpis = analytics.calculate_kpis(df)
    assert kpis["Headcount"] == 3
    assert kpis["TotalSalaryExpense"] == 260000.00  # 120k + 90k + 50k (Alice API ID 1 derived)

    # 5. Draw 16 charts
    charts = analytics.generate_all_charts(df)
    assert len(charts) == 16
    for c in charts:
        assert (temp_charts_dir / c).exists()

    # 6. Generate reports
    dept_summary = db.get_department_summary()
    reporter = ExecutiveReportGenerator(reports_dir=temp_reports_dir)

    md_path = reporter.generate_ceo_markdown_dashboard(kpis, dept_summary)
    xlsx_path = reporter.generate_excel_workbook(all_employees, dept_summary)

    # Assert report files are created
    assert md_path.exists()
    assert xlsx_path.exists()
    assert md_path.stat().st_size > 0
    assert xlsx_path.stat().st_size > 0
