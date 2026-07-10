"""Repository layer to isolate SQLite persistence logic.

Demonstrates Module 3: Software Design Patterns (Repository Pattern).
"""

from src.database.connection import SQLiteConnectionManager
from src.models.employee import PayrollRecord


class PayrollRepository:
    """Abstract interface defining payroll persistence actions."""

    def initialize_schema(self) -> None:
        """Sets up database tables."""
        raise NotImplementedError

    def save(self, record: PayrollRecord) -> None:
        """Persists a payroll record."""
        raise NotImplementedError

    def find_by_id(self, employee_id: int) -> PayrollRecord | None:
        """Retrieves a payroll record by ID."""
        raise NotImplementedError


class SQLitePayrollRepository(PayrollRepository):
    """Concrete SQLite implementation of the PayrollRepository."""

    def __init__(self, db_path: str) -> None:
        """Initializes with target database path."""
        self.db_path = db_path

    def initialize_schema(self) -> None:
        """Creates the SQLite database schema if not exists."""
        with SQLiteConnectionManager(self.db_path) as conn:
            conn.execute("""
            CREATE TABLE IF NOT EXISTS employee_payroll (
                employee_id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                salary REAL NOT NULL,
                bonus REAL NOT NULL,
                tax REAL NOT NULL,
                net_pay REAL NOT NULL
            )
            """)

    def save(self, record: PayrollRecord) -> None:
        """Inserts or replaces a payroll record in SQLite."""
        with SQLiteConnectionManager(self.db_path) as conn:
            conn.execute(
                """
            INSERT OR REPLACE INTO employee_payroll (employee_id, name, salary, bonus, tax, net_pay)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    record.employee_id,
                    record.name,
                    record.salary,
                    record.bonus,
                    record.tax,
                    record.net_pay,
                ),
            )

    def find_by_id(self, employee_id: int) -> PayrollRecord | None:
        """Fetches a payroll record by employee_id from SQLite."""
        with SQLiteConnectionManager(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT employee_id, name, salary, bonus, tax, net_pay FROM employee_payroll WHERE employee_id = ?",
                (employee_id,),
            )
            row = cursor.fetchone()
            if row is None:
                return None
            return PayrollRecord(
                employee_id=row["employee_id"],
                name=row["name"],
                salary=row["salary"],
                bonus=row["bonus"],
                tax=row["tax"],
                net_pay=row["net_pay"],
            )
