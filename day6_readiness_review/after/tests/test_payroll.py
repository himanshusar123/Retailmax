"""Unit and integration tests for the refactored payroll application.

Demonstrates Module 5: Unit Testing (pytest).
"""

from pathlib import Path

import pytest

from src.database.repository import SQLitePayrollRepository
from src.models.employee import Employee, PayrollRecord
from src.services.payroll import PayrollCalculator

# ==============================================================================
# Domain Model Tests
# ==============================================================================


def test_employee_valid_initialization() -> None:
    """Verifies that an Employee object initializes correctly with valid data."""
    emp = Employee(1, "Alice", 50000.0, 5)
    assert emp.employee_id == 1
    assert emp.name == "Alice"
    assert emp.salary == 50000.0
    assert emp.performance_score == 5


def test_employee_invalid_id_raises_value_error() -> None:
    """Verifies that an invalid employee ID throws a ValueError."""
    with pytest.raises(ValueError) as exc:
        Employee(-10, "Alice", 50000.0, 5)
    assert "Employee ID must be a positive integer" in str(exc.value)


def test_employee_invalid_salary_raises_value_error() -> None:
    """Verifies that a non-positive salary throws a ValueError."""
    with pytest.raises(ValueError) as exc:
        Employee(1, "Alice", -500.0, 5)
    assert "Salary must be positive" in str(exc.value)


def test_employee_invalid_performance_score_raises_value_error() -> None:
    """Verifies that a performance score outside 1-5 throws a ValueError."""
    with pytest.raises(ValueError) as exc:
        Employee(1, "Alice", 50000.0, 6)
    assert "Performance score must be in range 1-5" in str(exc.value)


# ==============================================================================
# Business Service Tests
# ==============================================================================


@pytest.fixture
def calculator() -> PayrollCalculator:
    """Pytest fixture to supply a fresh PayrollCalculator instance."""
    return PayrollCalculator()


@pytest.mark.parametrize(
    "performance_score,expected_bonus_rate",
    [
        (5, 0.20),
        (4, 0.10),
        (3, 0.05),
        (2, 0.00),
        (1, 0.00),
    ],
)
def test_payroll_calculator_bonus_rates(
    calculator: PayrollCalculator, performance_score: int, expected_bonus_rate: float
) -> None:
    """Verifies that each performance score maps to the correct bonus rate."""
    salary = 10000.0
    bonus = calculator.calculate_bonus(salary, performance_score)
    assert bonus == salary * expected_bonus_rate


def test_payroll_processing(calculator: PayrollCalculator) -> None:
    """Verifies end-to-end calculations inside the PayrollRecord."""
    emp = Employee(10, "Test User", 100000.0, 5)
    record = calculator.process_payroll(emp)

    assert record.employee_id == 10
    assert record.name == "Test User"
    assert record.salary == 100000.0
    assert record.bonus == 20000.0  # 20% of 100000
    assert record.tax == 18000.0  # 15% of (100000 + 20000)
    assert record.net_pay == 102000.0  # 120000 - 18000


# ==============================================================================
# Database Persistence / Repository Tests
# ==============================================================================


@pytest.fixture
def temp_db(tmp_path: Path) -> str:
    """Pytest fixture to provide an isolated temporary SQLite database path."""
    db_file = tmp_path / "test_payroll.db"
    return str(db_file)


def test_repository_save_and_retrieve(temp_db: str) -> None:
    """Verifies that the Repository correctly saves and finds records."""
    repository = SQLitePayrollRepository(temp_db)
    repository.initialize_schema()

    record = PayrollRecord(
        employee_id=200, name="Jane Doe", salary=90000.0, bonus=9000.0, tax=14850.0, net_pay=84150.0
    )

    # Save to SQLite
    repository.save(record)

    # Retrieve from SQLite
    saved_record = repository.find_by_id(200)

    assert saved_record is not None
    assert saved_record.employee_id == 200
    assert saved_record.name == "Jane Doe"
    assert saved_record.salary == 90000.0
    assert saved_record.bonus == 9000.0
    assert saved_record.tax == 14850.0
    assert saved_record.net_pay == 84150.0


def test_repository_find_by_id_missing_returns_none(temp_db: str) -> None:
    """Verifies that retrieving a non-existent ID returns None."""
    repository = SQLitePayrollRepository(temp_db)
    repository.initialize_schema()

    saved_record = repository.find_by_id(999)
    assert saved_record is None
