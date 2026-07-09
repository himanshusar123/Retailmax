"""
================================================================================
RetailMax Enterprise Data Platform

Module:      exceptions.py
Purpose:     Custom Exception Hierarchy for Enterprise Error Handling
Author:      Himanshu Sardana
Copyright:   (c) 2026 RetailMax Corp. All rights reserved.
================================================================================
"""


class RetailMaxError(Exception):
    """Base exception for the RetailMax Enterprise Data Platform.

    All project-specific exceptions inherit from this class, enabling
    blanket catch-all blocks at the orchestrator level while preserving
    context.

    ----------------------------------------------------------------------------
    INTERVIEW NOTES & PITFALLS:
    1. Why inherit from 'Exception' and not 'BaseException'?
       - 'BaseException' covers system-level events like KeyboardInterrupt (Ctrl+C)
         and SystemExit. Catching 'BaseException' can prevent users from stopping
         the program. Always inherit custom application exceptions from 'Exception'.
    2. What is Exception Chaining?
       - Using 'raise CustomError(...) from original_error' links exceptions,
         allowing full stack trace debuggability.
    ----------------------------------------------------------------------------
    """

    def __init__(self, message: str, error_code: str = "ERR_GENERIC") -> None:
        super().__init__(message)
        self.message = message
        self.error_code = error_code

    def __str__(self) -> str:
        return f"[{self.error_code}] {self.message}"


# ==============================================================================
# PHASE 1 & 5: VALIDATION & CORE EXCEPTIONS
# ==============================================================================


class ValidationError(RetailMaxError):
    """Generic validation exception for input data contracts."""

    def __init__(self, message: str, error_code: str = "ERR_VALIDATION") -> None:
        super().__init__(message, error_code)


class EmployeeValidationError(ValidationError):
    """Raised when an Employee record fails data contract checks.

    Attributes:
        field: The name of the field that failed validation.
        value: The invalid value supplied.
    """

    def __init__(self, message: str, field: str, value: str | float | int) -> None:
        full_msg = f"Validation failed for field '{field}' with value '{value}': {message}"
        super().__init__(full_msg, error_code="ERR_EMPLOYEE_VAL")
        self.field = field
        self.value = value


class CSVHandlerError(RetailMaxError):
    """Raised when flat file operations fail (missing files, write locks)."""

    def __init__(self, message: str, path: str) -> None:
        super().__init__(
            f"CSV operation failed on file '{path}': {message}", error_code="ERR_CSV_HANDLER"
        )
        self.path = path


# ==============================================================================
# PHASE 2: DATABASE LAYER EXCEPTIONS
# ==============================================================================


class DatabaseError(RetailMaxError):
    """Base exception for all database persistence operations."""

    def __init__(self, message: str, error_code: str = "ERR_DATABASE") -> None:
        super().__init__(message, error_code)


class DatabaseConnectionError(DatabaseError):
    """Raised when connection to SQLite database fails or is locked."""

    def __init__(self, message: str) -> None:
        super().__init__(message, error_code="ERR_DB_CONNECT")


class DatabaseQueryError(DatabaseError):
    """Raised when SQL query execution or CRUD operation fails.

    Attributes:
        sql: The SQL statement that failed to execute.
    """

    def __init__(self, message: str, sql: str = "") -> None:
        full_msg = f"{message} | SQL: {sql}" if sql else message
        super().__init__(full_msg, error_code="ERR_DB_QUERY")
        self.sql = sql


class DatabaseMigrationError(DatabaseError):
    """Raised when CSV-to-SQLite ETL database migration encounters schema issues."""

    def __init__(self, message: str) -> None:
        super().__init__(message, error_code="ERR_DB_MIGRATION")


# ==============================================================================
# PHASE 3: ANALYTICS LAYER EXCEPTIONS
# ==============================================================================


class AnalyticsError(RetailMaxError):
    """Raised when Pandas calculations or Matplotlib chart generation fails."""

    def __init__(self, message: str) -> None:
        super().__init__(message, error_code="ERR_ANALYTICS")


# ==============================================================================
# PHASE 4: API & INGESTION EXCEPTIONS
# ==============================================================================


class APIError(RetailMaxError):
    """Base exception for external REST API ingestion layer."""

    def __init__(self, message: str, error_code: str = "ERR_API") -> None:
        super().__init__(message, error_code)


class APIConnectionError(APIError):
    """Raised when connection timeouts or HTTP failures occur."""

    def __init__(self, message: str, status_code: int = 0) -> None:
        super().__init__(
            f"HTTP Connection Failed (Status: {status_code}): {message}",
            error_code="ERR_API_CONNECT",
        )
        self.status_code = status_code


class APIPayloadError(APIError):
    """Raised when JSON payload schemas are corrupted or missing keys."""

    def __init__(self, message: str) -> None:
        super().__init__(message, error_code="ERR_API_PAYLOAD")
