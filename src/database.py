"""
================================================================================
RetailMax Enterprise Data Platform

Module:      database.py
Purpose:     Relational storage layer using SQLite. Supports Transactions, CRUD,
             complex aggregation, and reports.
Author:      Himanshu Sardana
Copyright:   (c) 2026 RetailMax Corp. All rights reserved.
================================================================================
"""

import sqlite3
from typing import Any

from config import DB_PATH
from employee import Employee
from exceptions import (
    DatabaseConnectionError,
    DatabaseError,
    DatabaseQueryError,
)
from logging_config import get_logger

# Initialize logger
logger = get_logger("database")


class SQLiteConnectionManager:
    """Context manager for managing SQLite connections safely.

    Ensures connections are closed and transactions are committed or rolled
    back automatically depending on execution success.

    ----------------------------------------------------------------------------
    INTERVIEW NOTES & PITFALLS:
    1. What is SQLite transaction isolation?
       By default, python sqlite3 starts a transaction implicitly when executing
       DML (Data Manipulation Language) statements like INSERT/UPDATE/DELETE.
       We must commit/rollback or use context managers.
    2. Why use a context manager for connections?
       To guarantee that connection objects are closed under all circumstances,
       avoiding dangling file locks on the database file.
    ----------------------------------------------------------------------------
    """

    def __init__(self, db_path: str = str(DB_PATH)) -> None:
        """Initializes the Connection Manager with database path.

        Args:
            db_path: Path to sqlite database file.
        """
        self.db_path = db_path
        self.connection: sqlite3.Connection | None = None

    def __enter__(self) -> sqlite3.Connection:
        """Establishes connection and turns on foreign keys.

        Returns:
            sqlite3.Connection: Opened connection.

        Raises:
            DatabaseConnectionError: If connection fails.
        """
        try:
            # Connect with isolation_level=None to let us handle transaction boundaries manually
            self.connection = sqlite3.connect(
                self.db_path, timeout=10.0, detect_types=sqlite3.PARSE_DECLTYPES
            )
            # Enable row factory to access columns by name like dict rows
            self.connection.row_factory = sqlite3.Row
            # Enable foreign keys
            self.connection.execute("PRAGMA foreign_keys = ON;")
            # Enable Write-Ahead Log (WAL) mode for concurrency optimization
            self.connection.execute("PRAGMA journal_mode = WAL;")

            logger.debug(f"SQLite connected successfully to {self.db_path}")
            return self.connection
        except sqlite3.Error as e:
            raise DatabaseConnectionError(f"Failed to connect to SQLite: {e}")

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Closes the connection, rolling back if an exception occurred."""
        if self.connection:
            try:
                if exc_type is not None:
                    # Roll back changes on active transaction if error occurred
                    logger.warning("Transaction rollback triggered due to exception.")
                    self.connection.rollback()
                self.connection.close()
                logger.debug("SQLite connection closed.")
            except sqlite3.Error as e:
                logger.error(f"Error closing SQLite connection: {e}")


# ==============================================================================
# SCHEMAS INITIALIZATION
# ==============================================================================


def initialize_database(db_path: str = str(DB_PATH)) -> None:
    """Initializes the database schema and sets up tables and indexes.

    Creates 'employees' table and sets up indexes on department and salary.
    """
    logger.info("Initializing SQLite Database and schema...")

    sql_create_table = """
    CREATE TABLE IF NOT EXISTS employees (
        employee_id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        department TEXT NOT NULL,
        designation TEXT NOT NULL,
        salary REAL NOT NULL CHECK(salary >= 0),
        joining_date TEXT NOT NULL,
        performance_score INTEGER NOT NULL CHECK(performance_score BETWEEN 1 AND 5)
    );
    """

    sql_create_idx_dept = "CREATE INDEX IF NOT EXISTS idx_emp_dept ON employees(department);"
    sql_create_idx_salary = "CREATE INDEX IF NOT EXISTS idx_emp_salary ON employees(salary);"

    try:
        with SQLiteConnectionManager(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(sql_create_table)
            cursor.execute(sql_create_idx_dept)
            cursor.execute(sql_create_idx_salary)
            conn.commit()
            logger.info("Database schema initialized and indexes created successfully.")
    except DatabaseError as de:
        logger.error(f"Database schema initialization failed: {de}")
        raise
    except sqlite3.Error as e:
        raise DatabaseConnectionError(f"Failed to initialize database: {e}")


# ==============================================================================
# DATABASE OPERATIONAL CRUD INTERFACE
# ==============================================================================


class DatabaseHandler:
    """Wrapper class implementing the CRUD and search operations for SQLite.

    Each operation manages its own connection context to remain thread-safe.
    """

    def __init__(self, db_path: str = str(DB_PATH)) -> None:
        self.db_path = db_path

    def insert_employee(self, employee: Employee) -> None:
        """Inserts an employee record into the database.

        Args:
            employee: Employee instance to persist.

        Raises:
            DatabaseQueryError: If INSERT fails (e.g. Unique constraints violation).
        """
        sql = """
        INSERT INTO employees (
            employee_id, name, department, designation, salary, joining_date, performance_score
        ) VALUES (?, ?, ?, ?, ?, ?, ?);
        """
        params = (
            employee.employee_id,
            employee.name,
            employee.department,
            employee.designation,
            employee.salary,
            employee.joining_date,
            employee.performance_score,
        )

        try:
            with SQLiteConnectionManager(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(sql, params)
                conn.commit()
                logger.info(
                    f"Successfully inserted employee ID {employee.employee_id} to database."
                )
        except sqlite3.IntegrityError as ie:
            raise DatabaseQueryError(
                f"Integrity check failed: ID {employee.employee_id} already exists or values violate check constraints. details: {ie}",
                sql,
            )
        except sqlite3.Error as e:
            raise DatabaseQueryError(f"Database insert query failed: {e}", sql)

    def insert_employees_batch(self, employees: list[Employee]) -> int:
        """Inserts multiple employees inside a single ACID-compliant transaction.

        If any insertion fails, the entire batch is rolled back to protect consistency.

        Args:
            employees: List of Employee objects.

        Returns:
            int: Number of records inserted.
        """
        if not employees:
            return 0

        sql = """
        INSERT INTO employees (
            employee_id, name, department, designation, salary, joining_date, performance_score
        ) VALUES (?, ?, ?, ?, ?, ?, ?);
        """

        inserted_count = 0
        try:
            with SQLiteConnectionManager(self.db_path) as conn:
                cursor = conn.cursor()
                # Start transaction explicitly
                cursor.execute("BEGIN TRANSACTION;")
                for emp in employees:
                    params = (
                        emp.employee_id,
                        emp.name,
                        emp.department,
                        emp.designation,
                        emp.salary,
                        emp.joining_date,
                        emp.performance_score,
                    )
                    cursor.execute(sql, params)
                    inserted_count += 1
                conn.commit()
                logger.info(f"Successfully batch inserted {inserted_count} employees to database.")
                return inserted_count
        except sqlite3.Error as e:
            # Under SQLiteConnectionManager context, raising an exception triggers rollback
            logger.error(f"Batch transaction failed, rolling back. Error: {e}")
            raise DatabaseQueryError(f"Batch transaction failed: {e}", sql)

    def get_employee(self, employee_id: int) -> Employee | None:
        """Retrieves an employee record from the database by ID.

        Args:
            employee_id: Unique primary key.

        Returns:
            Employee instance if found, else None.
        """
        sql = "SELECT * FROM employees WHERE employee_id = ?;"

        try:
            with SQLiteConnectionManager(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(sql, (employee_id,))
                row = cursor.fetchone()
                if row:
                    return Employee(
                        employee_id=row["employee_id"],
                        name=row["name"],
                        department=row["department"],
                        designation=row["designation"],
                        salary=row["salary"],
                        joining_date=row["joining_date"],
                        performance_score=row["performance_score"],
                    )
                return None
        except sqlite3.Error as e:
            raise DatabaseQueryError(f"Failed to retrieve employee: {e}", sql)

    def get_all_employees(self) -> list[Employee]:
        """Retrieves all employee records from the database.

        Returns:
            List of all Employee records.
        """
        sql = "SELECT * FROM employees ORDER BY employee_id ASC;"
        employees: list[Employee] = []

        try:
            with SQLiteConnectionManager(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(sql)
                rows = cursor.fetchall()
                for row in rows:
                    employees.append(
                        Employee(
                            employee_id=row["employee_id"],
                            name=row["name"],
                            department=row["department"],
                            designation=row["designation"],
                            salary=row["salary"],
                            joining_date=row["joining_date"],
                            performance_score=row["performance_score"],
                        )
                    )
            return employees
        except sqlite3.Error as e:
            raise DatabaseQueryError(f"Failed to retrieve all employees: {e}", sql)

    def update_employee(self, employee: Employee) -> None:
        """Updates an employee record in the database.

        Args:
            employee: Employee instance with modified values.

        Raises:
            DatabaseQueryError: If ID doesn't exist or query fails.
        """
        sql = """
        UPDATE employees
        SET name = ?, department = ?, designation = ?, salary = ?, joining_date = ?, performance_score = ?
        WHERE employee_id = ?;
        """
        params = (
            employee.name,
            employee.department,
            employee.designation,
            employee.salary,
            employee.joining_date,
            employee.performance_score,
            employee.employee_id,
        )

        try:
            with SQLiteConnectionManager(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(sql, params)
                conn.commit()
                if cursor.rowcount == 0:
                    raise DatabaseQueryError(
                        f"Update failed: Employee ID {employee.employee_id} not found in database.",
                        sql,
                    )
                logger.info(f"Successfully updated employee ID {employee.employee_id} in database.")
        except sqlite3.Error as e:
            raise DatabaseQueryError(f"Database update query failed: {e}", sql)

    def delete_employee(self, employee_id: int) -> None:
        """Deletes an employee record from the database by ID.

        Args:
            employee_id: Primary key of employee to delete.

        Raises:
            DatabaseQueryError: If ID doesn't exist or query fails.
        """
        sql = "DELETE FROM employees WHERE employee_id = ?;"

        try:
            with SQLiteConnectionManager(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(sql, (employee_id,))
                conn.commit()
                if cursor.rowcount == 0:
                    raise DatabaseQueryError(
                        f"Delete failed: Employee ID {employee_id} not found in database.", sql
                    )
                logger.info(f"Successfully deleted employee ID {employee_id} from database.")
        except sqlite3.Error as e:
            raise DatabaseQueryError(f"Database delete query failed: {e}", sql)

    # ==============================================================================
    # SEARCH AND COMPLEX QUERIES
    # ==============================================================================

    def search_employees(
        self,
        query: str | None = None,
        department: str | None = None,
        min_salary: float | None = None,
        max_salary: float | None = None,
    ) -> list[Employee]:
        """Dynamic parameterized filter queries against employee database.

        Prevents SQL injection by constructing dynamically binded statements.

        Args:
            query: Matches characters inside employee names.
            department: Filter by specific department.
            min_salary: Bottom salary threshold.
            max_salary: Top salary threshold.

        Returns:
            Filtered list of Employee objects.
        """
        base_sql = "SELECT * FROM employees WHERE 1=1"
        params: list[Any] = []

        if query:
            base_sql += " AND name LIKE ?"
            params.append(f"%{query}%")

        if department:
            base_sql += " AND department = ?"
            params.append(department)

        if min_salary is not None:
            base_sql += " AND salary >= ?"
            params.append(min_salary)

        if max_salary is not None:
            base_sql += " AND salary <= ?"
            params.append(max_salary)

        base_sql += " ORDER BY employee_id ASC;"
        employees: list[Employee] = []

        try:
            with SQLiteConnectionManager(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(base_sql, tuple(params))
                rows = cursor.fetchall()
                for row in rows:
                    employees.append(
                        Employee(
                            employee_id=row["employee_id"],
                            name=row["name"],
                            department=row["department"],
                            designation=row["designation"],
                            salary=row["salary"],
                            joining_date=row["joining_date"],
                            performance_score=row["performance_score"],
                        )
                    )
            return employees
        except sqlite3.Error as e:
            raise DatabaseQueryError(f"Search query failed: {e}", base_sql)

    # ==============================================================================
    # BUSINESS METRIC AGGREGATION QUERIES
    # ==============================================================================

    def get_department_summary(self) -> list[dict[str, Any]]:
        """Calculates key financial and headcount aggregations grouped by Department.

        Demonstrates complex SQL aggregation functions.

        Returns:
            List of dictionaries representing summary metrics per department:
            - Department name
            - Headcount (Count)
            - TotalSalary (Sum)
            - AverageSalary (Avg)
            - MaxSalary (Max)
        """
        sql = """
        SELECT 
            department,
            COUNT(*) as headcount,
            SUM(salary) as total_salary,
            AVG(salary) as average_salary,
            MAX(salary) as max_salary
        FROM employees
        GROUP BY department
        ORDER BY headcount DESC;
        """

        summary = []
        try:
            with SQLiteConnectionManager(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(sql)
                rows = cursor.fetchall()
                for row in rows:
                    summary.append(
                        {
                            "Department": row["department"],
                            "Headcount": row["headcount"],
                            "TotalSalary": round(row["total_salary"], 2),
                            "AverageSalary": round(row["average_salary"], 2),
                            "MaxSalary": round(row["max_salary"], 2),
                        }
                    )
            return summary
        except sqlite3.Error as e:
            raise DatabaseQueryError(f"Department aggregate summary failed: {e}", sql)


# ==============================================================================
# INTERVIEW NOTES, ACID PROPERTIES & SQL INJECTION:
#
# Q1: What is SQL Injection and how do Parameterized Queries prevent it?
#     SQL Injection occurs when untrusted user input is directly concatenated
#     into SQL strings, allowing users to inject malicious commands:
#     - Bad: execute("SELECT * FROM employees WHERE name = '" + user_input + "';")
#     If user_input is: "admin' OR '1'='1", they bypass logic.
#     Parameterized queries use placeholders ('?') to inform the database engine
#     to treat the input strictly as literal values, never executable SQL code.
#
# Q2: What are the ACID properties in database transaction management?
#     - Atomicity: Guarantees that all DML statements in a transaction succeed
#       or all fail (rolled back). (Implemented via 'BEGIN TRANSACTION' and 'ROLLBACK').
#     - Consistency: Prevents invalid states. Schema rules like 'CHECK(salary >= 0)'
#       are validated.
#     - Isolation: Concurrency control. Transactions cannot see incomplete changes
#       made by others (SQLite uses locking).
#     - Durability: Once committed, changes survive crashes (saved on disk in WAL).
#
# Q3: What is SQLite WAL (Write-Ahead Log) mode?
#     WAL mode allows readers to read from the database without blocking writers,
#     and writers can write without blocking readers, significantly improving
#     concurrent application read/write throughput over standard rollback journals.
# ==============================================================================
