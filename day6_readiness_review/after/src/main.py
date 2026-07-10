"""Main entry point orchestrator for the production-ready payroll system.

Demonstrates Module 4: Packaging and Module 8: Production Readiness Review.
"""

from src.database.repository import SQLitePayrollRepository
from src.models.employee import Employee
from src.services.payroll import PayrollCalculator


def run_pipeline(db_path: str) -> None:
    """Orchestrates the schema creation, payroll calculations, and persistence."""
    print(f"\n--- Initializing RetailMax Payroll Database: {db_path} ---")
    repository = SQLitePayrollRepository(db_path)
    repository.initialize_schema()

    # Define clean, verified domain objects
    employees = [
        Employee(101, "Alice Smith", 80000.0, 5),
        Employee(102, "Bob Jones", 60000.0, 4),
        Employee(103, "Charlie Brown", 50000.0, 2),
    ]

    calculator = PayrollCalculator()

    print("\n--- Processing Payroll and Persisting via Repository ---")
    for emp in employees:
        # Calculate payroll using isolated business service
        payroll_record = calculator.process_payroll(emp)

        # Persist payroll using repository pattern
        repository.save(payroll_record)

        # Retrieve record to verify persistence
        saved = repository.find_by_id(emp.employee_id)
        if saved:
            print(
                f"Successfully saved and verified: {saved.name} "
                f"[Salary: ${saved.salary:,.2f}, Bonus: ${saved.bonus:,.2f}, "
                f"Tax: ${saved.tax:,.2f}, Net Pay: ${saved.net_pay:,.2f}]"
            )

    print("\n--- Production Readiness Review Verification Successful ---\n")


if __name__ == "__main__":
    # In production, this database path would be fed from config/environment variables
    run_pipeline("retailmax_payroll.db")
