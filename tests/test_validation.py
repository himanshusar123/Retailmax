"""
================================================================================
RetailMax Enterprise Data Platform

Module:      tests/test_validation.py
Purpose:     Unit tests for validation patterns and DataFrame data contracts.
Author:      Himanshu Sardana
Copyright:   (c) 2026 RetailMax Corp. All rights reserved.
================================================================================
"""

import pandas as pd

from validation import DataContractValidator, is_valid_date, is_valid_email


def test_email_validation_cases() -> None:
    """Tests email regex patterns on valid and invalid strings."""
    assert is_valid_email("info@retailmax.com") is True
    assert is_valid_email("jane.doe-work@company.co.in") is True

    assert is_valid_email("info.retailmax.com") is False  # Missing @
    assert is_valid_email("info@com") is False  # No domain extension
    assert is_valid_email(None) is False  # Non-string input


def test_date_validation_cases() -> None:
    """Tests date formatting regex validations on YYYY-MM-DD structures."""
    assert is_valid_date("2024-05-15") is True
    assert is_valid_date("1999-12-31") is True

    assert is_valid_date("15-05-2024") is False  # DD-MM-YYYY
    assert is_valid_date("2024/05/15") is False  # Slash separators
    assert is_valid_date("invalid-date") is False
    assert is_valid_date(None) is False


def test_dataframe_split_validation() -> None:
    """Verifies that DataContractValidator quarantines invalid/duplicate rows."""
    validator = DataContractValidator()

    # Create dummy DataFrame containing:
    # Row 0: Clean
    # Row 1: Duplicate ID
    # Row 2: Negative Salary (Failed contract)
    # Row 3: Invalid Department (Failed contract)
    # Row 4: Malformed Date (Failed contract)
    # Row 5: Clean 2
    raw_data = {
        "EmployeeID": [1001, 1001, 1002, 1003, 1004, 1005],
        "Name": ["Alice", "Alice Dup", "Bob", "Charlie", "Diana", "Ethan"],
        "Department": ["HR", "HR", "Engineering", "InvalidDept", "Sales", "Marketing"],
        "Designation": ["Specialist", "Specialist", "Developer", "Specialist", "Lead", "Associate"],
        "Salary": [50000.00, 50000.00, -1000.00, 80000.00, 75000.00, 60000.00],
        "JoiningDate": [
            "2024-01-01",
            "2024-01-01",
            "2024-01-02",
            "2024-01-03",
            "12/12/2024",
            "2024-01-05",
        ],
        "PerformanceScore": [4, 4, 3, 4, 3, 5],
    }
    df = pd.DataFrame(raw_data)

    clean_df, quarantined_df = validator.validate_employee_dataframe(df)

    # Expected clean: Row 0 (Alice 1001), Row 5 (Ethan 1005)
    assert len(clean_df) == 2
    assert list(clean_df["EmployeeID"]) == [1001, 1005]

    # Expected quarantined: Row 1 (Dup ID), Row 2 (Neg Salary), Row 3 (InvalidDept), Row 4 (Malformed Date)
    assert len(quarantined_df) == 4
    assert 1 in quarantined_df.index
    assert 2 in quarantined_df.index
    assert 3 in quarantined_df.index
    assert 4 in quarantined_df.index
