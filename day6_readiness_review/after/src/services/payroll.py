"""Business service for processing employee payroll calculations.

Demonstrates Module 1: Single Responsibility Principle and Module 2: Type Hints.
"""

from src.models.employee import Employee, PayrollRecord


class PayrollCalculator:
    """Calculates payroll, bonuses, and taxes for employees."""

    TAX_RATE = 0.15  # 15% flat tax rate

    def calculate_bonus(self, salary: float, performance_score: int) -> float:
        """Determines the performance-based bonus.

        - Score 5: 20%
        - Score 4: 10%
        - Score 3: 5%
        - Score 1-2: 0%
        """
        if performance_score == 5:
            return salary * 0.20
        elif performance_score == 4:
            return salary * 0.10
        elif performance_score == 3:
            return salary * 0.05
        return 0.0

    def calculate_tax(self, gross_pay: float) -> float:
        """Applies flat tax rate to gross earnings."""
        return gross_pay * self.TAX_RATE

    def process_payroll(self, employee: Employee) -> PayrollRecord:
        """Processes calculations and builds a typed PayrollRecord.

        This function represents pure business logic. It takes domain structures
        and returns domain structures, without any awareness of databases or files.
        """
        bonus = self.calculate_bonus(employee.salary, employee.performance_score)
        gross_pay = employee.salary + bonus
        tax = self.calculate_tax(gross_pay)
        net_pay = gross_pay - tax

        return PayrollRecord(
            employee_id=employee.employee_id,
            name=employee.name,
            salary=employee.salary,
            bonus=bonus,
            tax=tax,
            net_pay=net_pay,
        )
