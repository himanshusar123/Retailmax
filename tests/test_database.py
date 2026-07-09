"""
================================================================================
RetailMax Enterprise Data Platform

Module:      tests/test_database.py
Purpose:     Unit tests for database handlers, connection context, & CRUD operations.
Author:      Himanshu Sardana
Copyright:   (c) 2026 RetailMax Corp. All rights reserved.
================================================================================
"""

from pathlib import Path

import pytest

from database import DatabaseHandler, initialize_database
from employee import Employee
from exceptions import DatabaseQueryError


@pytest.fixture
def temp_db(tmp_path: Path) -> str:
    """Fixture providing a clean initialized temporary SQLite database path."""
    db_file = tmp_path / "test_retailmax.db"
    db_path_str = str(db_file)
    initialize_database(db_path_str)
    return db_path_str


def test_database_initialization(temp_db: str) -> None:
    """Verifies tables are created and indexes exist on schema startup."""
    import sqlite3

    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()
    # Check if table employees exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='employees';")
    assert cursor.fetchone() is not None

    # Check if indexes exist
    cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='employees';")
    indexes = [row[0] for row in cursor.fetchall()]
    assert "idx_emp_dept" in indexes
    assert "idx_emp_salary" in indexes
    conn.close()


def test_crud_lifecycle(temp_db: str) -> None:
    """Executes the full Create, Read, Update, Delete lifecycle on a single employee."""
    db = DatabaseHandler(temp_db)
    emp = Employee(1001, "Jane Doe", "HR", "Manager", 80000.00, "2024-03-12", 4)

    # 1. Create (Insert)
    db.insert_employee(emp)

    # 2. Read (Get)
    fetched = db.get_employee(1001)
    assert fetched is not None
    assert fetched.name == "Jane Doe"
    assert fetched.salary == 80000.00

    # 3. Update
    fetched.name = "Jane Smith"
    fetched.salary = 95000.00
    db.update_employee(fetched)

    updated = db.get_employee(1001)
    assert updated is not None
    assert updated.name == "Jane Smith"
    assert updated.salary == 95000.00

    # 4. Delete
    db.delete_employee(1001)
    assert db.get_employee(1001) is None


def test_duplicate_insert_fails(temp_db: str) -> None:
    """Verifies inserting a duplicate primary key raises DatabaseQueryError."""
    db = DatabaseHandler(temp_db)
    emp1 = Employee(1001, "Jane Doe", "HR", "Manager", 80000.00, "2024-03-12", 4)
    emp2 = Employee(1001, "John Smith", "Sales", "Associate", 40000.00, "2025-01-10", 3)

    db.insert_employee(emp1)
    with pytest.raises(DatabaseQueryError):
        db.insert_employee(emp2)


def test_batch_transaction_inserts(temp_db: str) -> None:
    """Verifies transactional batch insertions load all items or rollback on failures."""
    db = DatabaseHandler(temp_db)
    employees = [
        Employee(1001, "A", "HR", "Associate", 30000.00, "2024-01-01", 3),
        Employee(1002, "B", "Engineering", "Lead", 150000.00, "2024-01-02", 5),
        Employee(1003, "C", "Finance", "Manager", 90000.00, "2024-01-03", 4),
    ]

    inserted = db.insert_employees_batch(employees)
    assert inserted == 3
    assert len(db.get_all_employees()) == 3


def test_batch_transaction_rollback_protects_integrity(temp_db: str) -> None:
    """Checks that a duplicate primary key inside a batch rolls back all insertions."""
    db = DatabaseHandler(temp_db)
    # Load first record
    db.insert_employee(Employee(1001, "A", "HR", "Associate", 30000.00, "2024-01-01", 3))

    # Compile batch where one record (1001) causes a unique key collision
    batch = [
        Employee(1002, "B", "Engineering", "Lead", 150000.00, "2024-01-02", 5),
        Employee(
            1001, "C (Duplicate)", "Finance", "Manager", 90000.00, "2024-01-03", 4
        ),  # Conflict
    ]

    with pytest.raises(DatabaseQueryError):
        db.insert_employees_batch(batch)

    # Verify ID 1002 was NOT inserted because the transaction rolled back atomically
    assert db.get_employee(1002) is None
    assert len(db.get_all_employees()) == 1  # Only original 1001 remains


def test_search_employees(temp_db: str) -> None:
    """Verifies dynamic SQL search filters."""
    db = DatabaseHandler(temp_db)
    db.insert_employee(
        Employee(1001, "Alice Sharma", "Engineering", "Developer", 75000.00, "2024-01-01", 4)
    )
    db.insert_employee(
        Employee(1002, "Bob Patel", "Engineering", "Lead", 160000.00, "2024-01-02", 5)
    )
    db.insert_employee(Employee(1003, "Charlie Das", "HR", "Specialist", 45000.00, "2024-01-03", 3))

    # Name search
    name_results = db.search_employees(query="Sharma")
    assert len(name_results) == 1
    assert name_results[0].employee_id == 1001

    # Department filter
    dept_results = db.search_employees(department="Engineering")
    assert len(dept_results) == 2

    # Salary range filter
    salary_results = db.search_employees(min_salary=50000.00, max_salary=100000.00)
    assert len(salary_results) == 1
    assert salary_results[0].name == "Alice Sharma"


def test_get_department_summary(temp_db: str) -> None:
    """Checks SQL department aggregation computations."""
    db = DatabaseHandler(temp_db)
    db.insert_employee(
        Employee(1001, "Alice", "Engineering", "Developer", 100000.00, "2024-01-01", 4)
    )
    db.insert_employee(Employee(1002, "Bob", "Engineering", "Lead", 200000.00, "2024-01-02", 5))
    db.insert_employee(Employee(1003, "Charlie", "HR", "Specialist", 60000.00, "2024-01-03", 3))

    summary = db.get_department_summary()
    # Engineering and HR
    assert len(summary) == 2

    # Check Engineering aggregates (headcount=2, sum=300000, avg=150000, max=200000)
    eng_summary = [d for d in summary if d["Department"] == "Engineering"][0]
    assert eng_summary["Headcount"] == 2
    assert eng_summary["TotalSalary"] == 300000.00
    assert eng_summary["AverageSalary"] == 150000.00
    assert eng_summary["MaxSalary"] == 200000.00
