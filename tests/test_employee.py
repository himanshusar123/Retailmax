"""
================================================================================
RetailMax Enterprise Data Platform

Module:      tests/test_employee.py
Purpose:     Unit tests for Employee domain object validation and logic.
Author:      Himanshu Sardana
Copyright:   (c) 2026 RetailMax Corp. All rights reserved.
================================================================================
"""

import pytest

from employee import Employee
from exceptions import EmployeeValidationError


def test_valid_employee_creation() -> None:
    """Verifies that a correct set of arguments instantiates an Employee."""
    emp = Employee(
        employee_id=1001,
        name="John Doe",
        department="Engineering",
        designation="Software Developer",
        salary=75000.00,
        joining_date="2025-06-15",
        performance_score=4,
    )
    assert emp.employee_id == 1001
    assert emp.name == "John Doe"
    assert emp.department == "Engineering"
    assert emp.designation == "Software Developer"
    assert emp.salary == 75000.00
    assert emp.joining_date == "2025-06-15"
    assert emp.performance_score == 4


def test_invalid_id_raises_exception() -> None:
    """Checks that invalid Employee ID structures raise validations exceptions."""
    with pytest.raises(EmployeeValidationError) as exc:
        Employee(
            employee_id=-5,
            name="John Doe",
            department="Engineering",
            designation="Developer",
            salary=50000.00,
            joining_date="2025-06-15",
            performance_score=3,
        )
    assert "employee_id" in str(exc.value)


def test_empty_name_raises_exception() -> None:
    """Checks that empty names raise validation exceptions."""
    with pytest.raises(EmployeeValidationError) as exc:
        Employee(
            employee_id=1001,
            name="  ",
            department="Engineering",
            designation="Developer",
            salary=50000.00,
            joining_date="2025-06-15",
            performance_score=3,
        )
    assert "name" in str(exc.value)


def test_invalid_department_raises_exception() -> None:
    """Checks that departments outside the whitelist raise exceptions."""
    with pytest.raises(EmployeeValidationError) as exc:
        Employee(
            employee_id=1001,
            name="John Doe",
            department="R&D",  # Invalid department
            designation="Developer",
            salary=50000.00,
            joining_date="2025-06-15",
            performance_score=3,
        )
    assert "department" in str(exc.value)


def test_salary_bounds_validation() -> None:
    """Verifies that monthly salaries outside [15000, 300000] raise exceptions."""
    # Under boundary
    with pytest.raises(EmployeeValidationError) as exc1:
        Employee(
            employee_id=1001,
            name="John Doe",
            department="Engineering",
            designation="Developer",
            salary=12000.00,
            joining_date="2025-06-15",
            performance_score=3,
        )
    assert "salary" in str(exc1.value)

    # Over boundary
    with pytest.raises(EmployeeValidationError) as exc2:
        Employee(
            employee_id=1001,
            name="John Doe",
            department="Engineering",
            designation="Developer",
            salary=350000.00,
            joining_date="2025-06-15",
            performance_score=3,
        )
    assert "salary" in str(exc2.value)


def test_performance_score_bounds_validation() -> None:
    """Verifies that performance ratings outside [1, 5] raise exceptions."""
    with pytest.raises(EmployeeValidationError) as exc:
        Employee(
            employee_id=1001,
            name="John Doe",
            department="Engineering",
            designation="Developer",
            salary=50000.00,
            joining_date="2025-06-15",
            performance_score=6,  # Invalid
        )
    assert "performance_score" in str(exc.value)


def test_joining_date_format_validation() -> None:
    """Verifies that incorrect date formatting raises exceptions."""
    with pytest.raises(EmployeeValidationError) as exc:
        Employee(
            employee_id=1001,
            name="John Doe",
            department="Engineering",
            designation="Developer",
            salary=50000.00,
            joining_date="15/06/2025",  # Invalid format (expected YYYY-MM-DD)
            performance_score=3,
        )
    assert "joining_date" in str(exc.value)


def test_financial_calculations() -> None:
    """Verifies financial formula outputs (bonus, tax, net base)."""
    emp = Employee(
        employee_id=1001,
        name="John Doe",
        department="Engineering",
        designation="Developer",
        salary=100000.00,  # 100k per month
        joining_date="2025-06-15",
        performance_score=3,
    )
    # Annual: 100,000 * 12 = 1,200,000
    assert emp.annual_salary() == 1200000.00
    # Bonus: 10% of 1,200,000 = 120,000
    assert emp.calculate_bonus() == 120000.00
    # Tax: 8% of 1,200,000 = 96,000
    assert emp.calculate_tax() == 96000.00
    # Net: 1,200,000 + 120,000 - 96,000 = 1,224,000
    assert emp.net_salary() == 1224000.00


def test_serialization_roundtrip() -> None:
    """Verifies that object-to-dictionary-to-object returns equal parameters."""
    emp = Employee(
        employee_id=1001,
        name="John Doe",
        department="Engineering",
        designation="Developer",
        salary=75000.00,
        joining_date="2025-06-15",
        performance_score=4,
    )
    serialized_dict = emp.to_dict()
    assert serialized_dict["EmployeeID"] == 1001
    assert serialized_dict["AnnualSalary"] == 900000.00

    # Reconstruct
    reconstructed_emp = Employee.from_dict(serialized_dict)
    assert reconstructed_emp.employee_id == emp.employee_id
    assert reconstructed_emp.name == emp.name
    assert reconstructed_emp.salary == emp.salary
    assert reconstructed_emp.joining_date == emp.joining_date
    assert reconstructed_emp.performance_score == emp.performance_score
