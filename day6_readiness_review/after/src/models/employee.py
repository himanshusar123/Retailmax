"""Domain models representing Employee and Payroll structures.

Demonstrates Module 2: Type Hints and Module 1: Clean Code validation.
"""

from dataclasses import dataclass


@dataclass
class Employee:
    """Represents an employee profile in the RetailMax platform.

    Validates inputs on creation.
    """

    employee_id: int
    name: str
    salary: float
    performance_score: int

    def __post_init__(self) -> None:
        """Runs post-initialization domain rules."""
        if self.employee_id <= 0:
            raise ValueError(f"Employee ID must be a positive integer, got {self.employee_id}.")
        if self.salary <= 0:
            raise ValueError(f"Salary must be positive, got {self.salary}.")
        if not (1 <= self.performance_score <= 5):
            raise ValueError(
                f"Performance score must be in range 1-5, got {self.performance_score}."
            )


@dataclass
class PayrollRecord:
    """Represents a computed and finalized payroll record."""

    employee_id: int
    name: str
    salary: float
    bonus: float
    tax: float
    net_pay: float
