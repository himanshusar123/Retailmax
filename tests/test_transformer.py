"""
================================================================================
RetailMax Enterprise Data Platform

Module:      tests/test_transformer.py
Purpose:     Unit tests for DataTransformer (JSON flattening & type parsing)
Author:      Himanshu Sardana
Copyright:   (c) 2026 RetailMax Corp. All rights reserved.
================================================================================
"""

from data_transformer import DataTransformer


def test_data_transformer_flattening() -> None:
    """Verifies that nested address/company maps are flattened and cast correctly."""
    transformer = DataTransformer()
    raw_api_users = [
        {
            "id": 1,
            "name": "Alice Cooper",
            "username": "acooper",
            "email": "alice@retailmax.com",
            "address": {"street": "123 Main St", "city": "Mumbai"},
            "company": {
                "name": "RetailMax Engineering Services",
                "bs": "develop software features",
            },
        },
        {
            "id": 2,
            "name": "Bob Marley",
            "username": "bmarley",
            "email": "bob@retailmax.com",
            "address": {"city": "Delhi"},
            "company": {"name": "RetailMax Marketing", "bs": "synergize corporate campaigns"},
        },
    ]

    employees = transformer.transform_raw_payload(raw_api_users)
    assert len(employees) == 2

    # Check first employee parameters
    emp1 = employees[0]
    # Offset ID: 1 + 2000 = 2001
    assert emp1.employee_id == 2001
    assert emp1.name == "Alice Cooper"
    # Department derived dynamically: 1 % 5 = 1 (Engineering)
    assert emp1.department == "Engineering"
    # Designation derived from bs split capital: bs='develop software...' -> Develop
    assert emp1.designation == "Develop"
    # Salary derived: 40,000 + 1 * 10,000 = 50,000.00
    assert emp1.salary == 50000.00
    assert emp1.performance_score == 2  # (1 % 5) + 1 = 2
    assert emp1.joining_date == "2024-02-02"  # Month=1+1=2, Day=1+1=2

    # Check second employee parameters
    emp2 = employees[1]
    assert emp2.employee_id == 2002
    assert emp2.name == "Bob Marley"
    # Department: 2 % 5 = 2 (Finance)
    assert emp2.department == "Finance"
    # Designation: bs='synergize corporate...' -> Synergize
    assert emp2.designation == "Synergize"
    # Salary: 40,000 + 2 * 10,000 = 60,000.00
    assert emp2.salary == 60000.00
    assert emp2.performance_score == 3
    assert emp2.joining_date == "2024-03-03"
