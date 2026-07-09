"""
================================================================================
RetailMax Enterprise Data Platform

Module:      employee.py
Purpose:     Defines the core Employee domain entity and OOP validation layers.
Author:      Himanshu Sardana
Copyright:   (c) 2026 RetailMax Corp. All rights reserved.
================================================================================
"""

from datetime import datetime
from typing import Any

from constants import (
    ANNUAL_MONTHS,
    APPROVED_DEPARTMENTS,
    BONUS_MULTIPLIER,
    DATE_FORMAT,
    MAX_MONTHLY_SALARY,
    MAX_PERFORMANCE_SCORE,
    MIN_MONTHLY_SALARY,
    MIN_PERFORMANCE_SCORE,
    TAX_MULTIPLIER,
)
from exceptions import EmployeeValidationError
from logging_config import get_logger

# Initialize logger
logger = get_logger("employee")


class Employee:
    """Represents a standard corporate Employee within RetailMax.

    This class enforces strict data contracts using properties and throws custom
    exceptions on field failures. It encapsulates employee metadata, financial
    aggregations, and serialization behaviors.

    Attributes:
        employee_id (int): Unique identifier.
        name (str): Full name of the employee.
        department (str): Corporate division.
        designation (str): Role description.
        salary (float): Monthly salary.
        joining_date (str): ISO formatted joining date (YYYY-MM-DD).
        performance_score (int): Rating between 1 and 5.
    """

    def __init__(
        self,
        employee_id: int,
        name: str,
        department: str,
        designation: str,
        salary: float,
        joining_date: str,
        performance_score: int,
    ) -> None:
        """Initializes a validated Employee instance.

        Args:
            employee_id: Unique integer ID.
            name: Full name string.
            department: Whitelisted corporate department.
            designation: Role string.
            salary: Positive monthly salary amount.
            joining_date: ISO date string.
            performance_score: Rating from 1 to 5.

        Raises:
            EmployeeValidationError: If any of the inputs fail validation.
        """
        # Validate and set attributes through property setters
        self.employee_id = employee_id
        self.name = name
        self.department = department
        self.designation = designation
        self.salary = salary
        self.joining_date = joining_date
        self.performance_score = performance_score

        logger.debug(f"Employee instance successfully initialized: ID={self._employee_id}")

    # ==============================================================================
    # GETTERS AND SETTERS (ENCAPSULATION & DATA VALIDATION)
    # ==============================================================================

    @property
    def employee_id(self) -> int:
        """Gets the employee's unique ID."""
        return self._employee_id

    @employee_id.setter
    def employee_id(self, val: int) -> None:
        """Sets the employee's ID. Enforces positive integer check."""
        if not isinstance(val, int) or val <= 0:
            raise EmployeeValidationError(
                "Employee ID must be a positive integer.", "employee_id", val
            )
        self._employee_id = val

    @property
    def name(self) -> str:
        """Gets the employee's full name."""
        return self._name

    @name.setter
    def name(self, val: str) -> None:
        """Sets the employee's name. Enforces non-empty string check."""
        if not isinstance(val, str) or not val.strip():
            raise EmployeeValidationError("Employee Name cannot be empty.", "name", val)
        self._name = val.strip()

    @property
    def department(self) -> str:
        """Gets the employee's department."""
        return self._department

    @department.setter
    def department(self, val: str) -> None:
        """Sets the employee's department. Enforces department whitelist check."""
        if not isinstance(val, str) or val.strip() not in APPROVED_DEPARTMENTS:
            raise EmployeeValidationError(
                f"Department must be one of: {APPROVED_DEPARTMENTS}.", "department", val
            )
        self._department = val.strip()

    @property
    def designation(self) -> str:
        """Gets the employee's designation."""
        return self._designation

    @designation.setter
    def designation(self, val: str) -> None:
        """Sets the employee's designation. Enforces non-empty string check."""
        if not isinstance(val, str) or not val.strip():
            raise EmployeeValidationError("Designation cannot be empty.", "designation", val)
        self._designation = val.strip()

    @property
    def salary(self) -> float:
        """Gets the monthly salary."""
        return self._salary

    @salary.setter
    def salary(self, val: float) -> None:
        """Sets the monthly salary. Enforces corporate minimum and maximum bounds."""
        try:
            numeric_val = float(val)
        except (ValueError, TypeError):
            raise EmployeeValidationError("Salary must be a numeric value.", "salary", val)

        if numeric_val < MIN_MONTHLY_SALARY or numeric_val > MAX_MONTHLY_SALARY:
            raise EmployeeValidationError(
                f"Salary must be between {MIN_MONTHLY_SALARY} and {MAX_MONTHLY_SALARY}.",
                "salary",
                val,
            )
        self._salary = numeric_val

    @property
    def joining_date(self) -> str:
        """Gets the joining date."""
        return self._joining_date

    @joining_date.setter
    def joining_date(self, val: str) -> None:
        """Sets the joining date. Enforces date format check."""
        if not isinstance(val, str) or not val.strip():
            raise EmployeeValidationError("Joining date cannot be empty.", "joining_date", val)
        try:
            datetime.strptime(val.strip(), DATE_FORMAT)
        except ValueError:
            raise EmployeeValidationError(
                f"Joining date must match format {DATE_FORMAT} (e.g. 2024-05-15).",
                "joining_date",
                val,
            )
        self._joining_date = val.strip()

    @property
    def performance_score(self) -> int:
        """Gets the performance score."""
        return self._performance_score

    @performance_score.setter
    def performance_score(self, val: int) -> None:
        """Sets the performance score. Enforces range check [1, 5]."""
        try:
            int_val = int(val)
        except (ValueError, TypeError):
            raise EmployeeValidationError(
                "Performance score must be an integer.", "performance_score", val
            )

        if int_val < MIN_PERFORMANCE_SCORE or int_val > MAX_PERFORMANCE_SCORE:
            raise EmployeeValidationError(
                f"Performance score must be between {MIN_PERFORMANCE_SCORE} and {MAX_PERFORMANCE_SCORE}.",
                "performance_score",
                val,
            )
        self._performance_score = int_val

    # ==============================================================================
    # BUSINESS LOGIC METHOD LAYERS
    # ==============================================================================

    def annual_salary(self) -> float:
        """Calculates the annual base salary.

        Returns:
            Annual base salary amount.
        """
        return self._salary * ANNUAL_MONTHS

    def calculate_bonus(self) -> float:
        """Computes the employee's annual bonus (10% of annual salary).

        Returns:
            Computed bonus amount.
        """
        return self.annual_salary() * BONUS_MULTIPLIER

    def calculate_tax(self) -> float:
        """Computes the employee's income tax liabilities (8% of annual salary).

        Returns:
            Tax deduction amount.
        """
        return self.annual_salary() * TAX_MULTIPLIER

    def net_salary(self) -> float:
        """Calculates net annual earnings after applying bonuses and taxes.

        Returns:
            Total annual net payout.
        """
        return self.annual_salary() + self.calculate_bonus() - self.calculate_tax()

    # ==============================================================================
    # SERIALIZATION AND UTILITIES
    # ==============================================================================

    def to_dict(self) -> dict[str, Any]:
        """Serializes the employee object into a standard dictionary.

        Returns:
            Dictionary payload representing the employee.
        """
        return {
            "EmployeeID": self.employee_id,
            "Name": self.name,
            "Department": self.department,
            "Designation": self.designation,
            "Salary": self.salary,
            "JoiningDate": self.joining_date,
            "PerformanceScore": self.performance_score,
            "AnnualSalary": self.annual_salary(),
            "AnnualBonus": self.calculate_bonus(),
            "AnnualTax": self.calculate_tax(),
            "NetSalary": self.net_salary(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Employee":
        """Factory method to construct an Employee instance from a dictionary payload.

        Args:
            data: Raw dictionary loaded from CSV/JSON.

        Returns:
            A validated Employee instance.

        Raises:
            EmployeeValidationError: If dictionary contains invalid types or values.
        """
        try:
            return cls(
                employee_id=int(data["EmployeeID"]),
                name=str(data["Name"]),
                department=str(data["Department"]),
                designation=str(data["Designation"]),
                salary=float(data["Salary"]),
                joining_date=str(data["JoiningDate"]),
                performance_score=int(data["PerformanceScore"]),
            )
        except KeyError as ke:
            raise EmployeeValidationError(
                f"Missing required key in data dictionary: {ke}", str(ke), "N/A"
            )
        except (ValueError, TypeError) as e:
            raise EmployeeValidationError(
                f"Failed to cast data types: {e}", "dictionary_data", str(data)
            )

    def to_csv_row(self) -> list[str]:
        """Converts the employee record back to flat CSV string list format.

        Returns:
            List of values matching CSV headers.
        """
        return [
            str(self.employee_id),
            self.name,
            self.department,
            self.designation,
            f"{self.salary:.2f}",
            self.joining_date,
            str(self.performance_score),
        ]

    # ==============================================================================
    # DUNDER REPRESENTATIONS
    # ==============================================================================

    def __str__(self) -> str:
        """Returns a user-friendly string representation of the Employee.

        Shows basic ID, Name, and Department.
        """
        return f"Employee: {self.name} (ID: {self.employee_id}, Dept: {self.department})"

    def __repr__(self) -> str:
        """Returns a detailed, unambiguous programmer-facing representation.

        Shows constructor invocation signature for debugging.
        """
        return (
            f"Employee(employee_id={self.employee_id!r}, name={self.name!r}, "
            f"department={self.department!r}, designation={self.designation!r}, "
            f"salary={self.salary!r}, joining_date={self.joining_date!r}, "
            f"performance_score={self.performance_score!r})"
        )


# ==============================================================================
# INTERVIEW NOTES, ARCHITECTURAL CONCEPTS & PITFALLS:
#
# Q1: What is Encapsulation and how does Python support it?
#     Encapsulation is the bundling of data and methods operating on that data,
#     restricting direct access to some of the object's components. Python uses
#     underscores to signal access control:
#     - Single underscore (_field) indicates it is internal (protected).
#     - Double underscore (__field) triggers name mangling to prevent accidental
#       subclass overrides (private).
#     We use properties (@property) to wrap private attributes with validation logic,
#     ensuring instance integrity.
#
# Q2: What is the difference between '__str__' and '__repr__'?
#     - '__str__' is for end-users. It should be readable, clean, and informative.
#     - '__repr__' is for developers and debugging. It must be unambiguous and,
#       if possible, resemble valid Python code that can reconstruct the object.
#     - Rule of Thumb: 'repr(x)' is called if '__str__' is missing.
#
# Q3: Why do we use custom exception classes like 'EmployeeValidationError'?
#     In enterprise codebases, catching generic built-in exceptions like 'ValueError'
#     can mask other underlying issues (e.g., failed parsing elsewhere). Creating
#     specific custom exception classes allows callers to selectively catch and handle
#     validation failures differently from system failures.
# ==============================================================================
