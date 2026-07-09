"""
================================================================================
RetailMax Enterprise Data Platform

Module:      tests/test_analytics.py
Purpose:     Unit tests for Pandas KPI calculations & Matplotlib visualizations.
Author:      Himanshu Sardana
Copyright:   (c) 2026 RetailMax Corp. All rights reserved.
================================================================================
"""

from pathlib import Path

import pandas as pd
import pytest

from analytics import BusinessAnalyticsEngine


@pytest.fixture
def clean_test_df() -> pd.DataFrame:
    """Fixture providing a standard clean Pandas DataFrame for test cases."""
    data = {
        "EmployeeID": [1001, 1002, 1003, 1004],
        "Name": ["John Doe", "Jane Smith", "Bob Jones", "Alice Patel"],
        "Department": ["HR", "Engineering", "Engineering", "Marketing"],
        "Designation": ["Manager", "Lead", "Developer", "Associate"],
        "Salary": [60000.00, 150000.00, 80000.00, 50000.00],
        "JoiningDate": ["2023-01-01", "2024-06-15", "2025-03-01", "2024-11-20"],
        "PerformanceScore": [4, 5, 3, 4],
    }
    df = pd.DataFrame(data)
    df["JoiningDate"] = pd.to_datetime(df["JoiningDate"])
    # Add simulated TenureYears relative to current date (July 9, 2026)
    current_date = pd.Timestamp("2026-07-09")
    df["TenureYears"] = (current_date - df["JoiningDate"]).dt.days / 365.25
    return df


def test_kpi_calculations(clean_test_df: pd.DataFrame) -> None:
    """Verifies descriptive statistics computed by the business intelligence engine."""
    engine = BusinessAnalyticsEngine()
    kpis = engine.calculate_kpis(clean_test_df)

    assert kpis["Headcount"] == 4
    # Total Salary: 60k + 150k + 80k + 50k = 340k
    assert kpis["TotalSalaryExpense"] == 340000.00
    # Average Salary: 340k / 4 = 85k
    assert kpis["AverageSalary"] == 85000.00
    assert kpis["MaxSalary"] == 150000.00
    assert kpis["MinSalary"] == 50000.00

    # Average performance: (4+5+3+4)/4 = 4.0
    assert kpis["AveragePerformanceScore"] == 4.0
    # High performers count (rating >= 4): John(4), Jane(5), Alice(4) = 3
    assert kpis["HighPerformersCount"] == 3
    assert kpis["HighPerformersRatio"] == 75.00


def test_chart_generation_files(tmp_path: Path, clean_test_df: pd.DataFrame) -> None:
    """Verifies that the chart engine successfully saves all 16 chart PNG files."""
    engine = BusinessAnalyticsEngine()
    # Override charts destination directory to temp directory for testing
    engine.charts_dir = tmp_path

    generated_charts = engine.generate_all_charts(clean_test_df)
    assert len(generated_charts) == 16

    # Verify each expected chart exists in the temporary directory
    for chart_name in generated_charts:
        chart_file = tmp_path / chart_name
        assert chart_file.exists()
        # Verify file is not empty
        assert chart_file.stat().st_size > 0
