"""
================================================================================
RetailMax Enterprise Data Platform

Module:      csv_handler.py
Purpose:     Handles transactional CRUD operations against the local CSV flat-file.
Author:      Himanshu Sardana
Copyright:   (c) 2026 RetailMax Corp. All rights reserved.
================================================================================
"""

import csv
import os
from pathlib import Path

from employee import Employee
from exceptions import CSVHandlerError, ValidationError
from logging_config import get_logger

# Initialize logger
logger = get_logger("csv_handler")


class CSVHandler:
    """Manages flat-file operations for Employee records.

    Provides transactional-like operations on CSV files. To prevent file corruption,
    writes are executed using an atomic temp-file write-and-replace strategy.
    """

    def __init__(self, file_path: Path) -> None:
        """Initializes the CSV Handler.

        Args:
            file_path: Absolute path to the CSV data file.
        """
        self.file_path = file_path
        self._headers = [
            "EmployeeID",
            "Name",
            "Department",
            "Designation",
            "Salary",
            "JoiningDate",
            "PerformanceScore",
        ]
        logger.debug(f"CSVHandler initialized pointing to: {self.file_path}")

    def _ensure_file_exists(self) -> None:
        """Creates the data directory and CSV file with headers if missing."""
        try:
            if not self.file_path.exists():
                self.file_path.parent.mkdir(parents=True, exist_ok=True)
                with open(self.file_path, mode="w", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)
                    writer.writerow(self._headers)
                logger.info(f"Initialized new CSV file with headers at: {self.file_path}")
        except Exception as e:
            raise CSVHandlerError(
                f"Failed to initialize CSV storage file: {e}", str(self.file_path)
            )

    def read_all(self) -> list[Employee]:
        """Reads and deserializes all employee records from the CSV file.

        Returns:
            A list of validated Employee instances.

        Raises:
            CSVHandlerError: If the file is unreadable or contains invalid format.
        """
        self._ensure_file_exists()
        employees: list[Employee] = []

        try:
            with open(self.file_path, newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row_num, row in enumerate(reader, start=2):
                    try:
                        # Map keys to Employee fields
                        emp = Employee.from_dict(row)
                        employees.append(emp)
                    except ValidationError as ve:
                        logger.warning(
                            f"Skipping corrupted CSV row {row_num} in {self.file_path}: {ve}"
                        )
                        continue
            logger.info(f"Read {len(employees)} valid employees from CSV.")
            return employees
        except PermissionError as pe:
            raise CSVHandlerError(f"Permission denied: {pe}", str(self.file_path))
        except Exception as e:
            raise CSVHandlerError(f"Failed to read CSV database: {e}", str(self.file_path))

    def get_by_id(self, employee_id: int) -> Employee | None:
        """Retrieves a single employee record by ID.

        Args:
            employee_id: Unique identifier to search.

        Returns:
            Employee instance if found, otherwise None.
        """
        employees = self.read_all()
        for emp in employees:
            if emp.employee_id == employee_id:
                return emp
        return None

    def insert(self, employee: Employee) -> None:
        """Appends a new employee record to the CSV file.

        Ensures the EmployeeID is unique before writing.

        Args:
            employee: The validated Employee instance to add.

        Raises:
            CSVHandlerError: If a duplicate key is found or write fails.
        """
        self._ensure_file_exists()

        # Read first to verify uniqueness
        existing_employees = self.read_all()
        if any(emp.employee_id == employee.employee_id for emp in existing_employees):
            raise CSVHandlerError(
                f"Insert failed: Employee with ID {employee.employee_id} already exists.",
                str(self.file_path),
            )

        try:
            with open(self.file_path, mode="a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(employee.to_csv_row())
            logger.info(f"Successfully appended Employee ID {employee.employee_id} to CSV.")
        except Exception as e:
            raise CSVHandlerError(f"Failed to append employee to CSV: {e}", str(self.file_path))

    def update(self, employee: Employee) -> None:
        """Updates an existing employee's details in the CSV database.

        Uses an atomic temporary-file replacement process to avoid data loss.

        Args:
            employee: Employee instance with updated fields.

        Raises:
            CSVHandlerError: If the employee ID is not found or file writing fails.
        """
        self._ensure_file_exists()
        employees = self.read_all()

        found = False
        for idx, emp in enumerate(employees):
            if emp.employee_id == employee.employee_id:
                employees[idx] = employee
                found = True
                break

        if not found:
            raise CSVHandlerError(
                f"Update failed: Employee ID {employee.employee_id} not found.", str(self.file_path)
            )

        self._atomic_write(employees)
        logger.info(f"Successfully updated Employee ID {employee.employee_id} in CSV.")

    def delete(self, employee_id: int) -> None:
        """Removes an employee record from the CSV file by ID.

        Uses an atomic temporary-file replacement process to avoid data loss.

        Args:
            employee_id: ID of the employee to remove.

        Raises:
            CSVHandlerError: If the employee ID is not found or file writing fails.
        """
        self._ensure_file_exists()
        employees = self.read_all()

        initial_len = len(employees)
        employees = [emp for emp in employees if emp.employee_id != employee_id]

        if len(employees) == initial_len:
            raise CSVHandlerError(
                f"Delete failed: Employee ID {employee_id} not found.", str(self.file_path)
            )

        self._atomic_write(employees)
        logger.info(f"Successfully deleted Employee ID {employee_id} from CSV.")

    def _atomic_write(self, employees: list[Employee]) -> None:
        """Writes the list of employees to a temporary file, then overwrites the database.

        This prevents file corruption if a write is interrupted by a system crash or power cut.

        Args:
            employees: The list of all Employee records to persist.

        Raises:
            CSVHandlerError: If file writing or system replacement operations fail.
        """
        temp_file_path = self.file_path.with_suffix(".tmp")
        try:
            with open(temp_file_path, mode="w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(self._headers)
                for emp in employees:
                    writer.writerow(emp.to_csv_row())

            # Atomic swap of the temp file over the target database file
            # On Windows, os.replace() overwrites destination files atomically
            os.replace(temp_file_path, self.file_path)
        except Exception as e:
            temp_file_path.unlink(missing_ok=True)
            raise CSVHandlerError(f"Atomic transaction write failed: {e}", str(self.file_path))


# ==============================================================================
# INTERVIEW NOTES, FILE HANDLING MECHANICS & PITFALLS:
#
# Q1: Why do we use the 'with' statement when opening files?
#     The 'with' statement acts as a Context Manager. It guarantees that the file
#     descriptor is closed immediately when the block exits, even if exceptions are
#     raised within the block. This prevents resource leaks (locked file descriptors).
#
# Q2: Why is the 'Atomic Write' design pattern crucial for corporate backend code?
#     If a program writes directly to the primary file (e.g., 'open(file, "w")')
#     and the application crashed, the OS runs out of disk, or the power goes out
#     halfway through writing, the file becomes corrupted (cut in half).
#     By writing to a temporary file and executing 'os.replace()' (which is atomic
#     at the OS level), we guarantee the operation either completely succeeds or
#     fails, leaving the original data intact.
#
# Q3: What is the difference between 'newline=""' behavior in python 3 csv files?
#     If 'newline=""' is not specified when opening files for writing on Windows,
#     the CSV writer will output carriage returns '\r\r\n' (double newlines), causing
#     blank rows between entries. Specifying 'newline=""' directs the writer to let
#     the CSV module handle system-level line endings properly.
# ==============================================================================
