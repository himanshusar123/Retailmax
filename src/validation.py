"""
================================================================================
RetailMax Enterprise Data Platform

Module:      validation.py
Purpose:     Data Contract Verification Layer for Pandas DataFrames & Individual Entities
Author:      Himanshu Sardana
Copyright:   (c) 2026 RetailMax Corp. All rights reserved.
================================================================================
"""

import re
from typing import Any

import pandas as pd

from constants import (
    APPROVED_DEPARTMENTS,
    MAX_MONTHLY_SALARY,
    MAX_PERFORMANCE_SCORE,
    MIN_MONTHLY_SALARY,
    MIN_PERFORMANCE_SCORE,
)
from logging_config import get_logger

# Initialize logger
logger = get_logger("validation")

# Corporate Email Regex Check (sprint 5: regex compilation)
EMAIL_PATTERN = re.compile(r"^[\w\.-]+@[\w\.-]+\.\w+$")


def is_valid_email(email: Any) -> bool:
    """Validates an email address against corporate regular expressions.

    Args:
        email: The email string to evaluate.

    Returns:
        True if valid format, False otherwise.
    """
    if not isinstance(email, str):
        return False
    return bool(EMAIL_PATTERN.match(email.strip()))


def is_valid_date(date_str: Any) -> bool:
    """Validates whether a string matches the corporate YYYY-MM-DD format.

    Args:
        date_str: Joining date string.

    Returns:
        True if valid, False otherwise.
    """
    if not isinstance(date_str, str):
        return False
    # Simple regex match to avoid expensive datetime.strptime overhead in first-pass filters
    return bool(re.match(r"^\d{4}-\d{2}-\d{2}$", date_str.strip()))


class DataContractValidator:
    """Enforces tabular data contracts against raw data frames.

    Implements a split-validation pipeline that quarantines corrupted records
    while permitting clean records to pass downstream.
    """

    def validate_employee_dataframe(self, df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
        """Validates all employee records in a Pandas DataFrame.

        Evaluates rows against the following constraints:
        1. EmployeeID: Must be a positive integer and unique.
        2. Department: Must be whitelisted.
        3. Salary: Must fall within [MIN_MONTHLY_SALARY, MAX_MONTHLY_SALARY].
        4. PerformanceScore: Must fall within [MIN_PERFORMANCE_SCORE, MAX_PERFORMANCE_SCORE].
        5. JoiningDate: Must match standard date format.

        Args:
            df: Input raw DataFrame.

        Returns:
            Tuple[pd.DataFrame, pd.DataFrame]: (clean_df, quarantined_df).
        """
        logger.info("Executing row-level contract validation on employee DataFrame...")

        if df.empty:
            logger.warning("Empty DataFrame passed for validation. Returning empty split.")
            return df.copy(), df.copy()

        # Step 1: Detect duplicate EmployeeIDs (Keep first, quarantine others)
        duplicate_mask = df.duplicated(subset=["EmployeeID"], keep="first")

        # Step 2: Establish row validation rules using vectorized pandas filters
        id_valid = df["EmployeeID"].astype(str).str.isdigit() & (df["EmployeeID"].astype(float) > 0)
        dept_valid = df["Department"].isin(APPROVED_DEPARTMENTS)
        salary_valid = (df["Salary"].astype(float) >= MIN_MONTHLY_SALARY) & (
            df["Salary"].astype(float) <= MAX_MONTHLY_SALARY
        )
        score_valid = (df["PerformanceScore"].astype(float) >= MIN_PERFORMANCE_SCORE) & (
            df["PerformanceScore"].astype(float) <= MAX_PERFORMANCE_SCORE
        )
        date_valid = df["JoiningDate"].astype(str).apply(is_valid_date)

        # Composite validation mask (must pass all rules and not be a duplicate ID)
        valid_rows_mask = (
            id_valid & dept_valid & salary_valid & score_valid & date_valid & ~duplicate_mask
        )

        # Split DataFrames
        clean_df = df[valid_rows_mask].copy()
        quarantined_df = df[~valid_rows_mask].copy()

        # Perform type conversions on the clean dataset to standardize
        if not clean_df.empty:
            clean_df["EmployeeID"] = clean_df["EmployeeID"].astype(int)
            clean_df["Salary"] = clean_df["Salary"].astype(float)
            clean_df["PerformanceScore"] = clean_df["PerformanceScore"].astype(int)
            clean_df["Name"] = clean_df["Name"].astype(str).str.strip()
            clean_df["Department"] = clean_df["Department"].astype(str).str.strip()
            clean_df["Designation"] = clean_df["Designation"].astype(str).str.strip()
            clean_df["JoiningDate"] = clean_df["JoiningDate"].astype(str).str.strip()

        # Log summary
        logger.info(
            f"Validation Completed. Valid rows: {len(clean_df)}, Quarantined rows: {len(quarantined_df)}."
        )

        # Log specific quarantine warnings
        if not quarantined_df.empty:
            for idx, row in quarantined_df.iterrows():
                logger.warning(
                    f"Quarantined Row {idx}: EmployeeID={row.get('EmployeeID')}, Name='{row.get('Name')}', "
                    f"Reason=Violated contract constraints or duplicated ID."
                )

        return clean_df, quarantined_df


# ==============================================================================
# INTERVIEW NOTES & VALIDATION THEORIES:
#
# Q1: What is a "Data Contract" and why is it useful?
#     A data contract is an agreement between data producers and consumers about
#     the structure, type, and bounds of data being transmitted. Enforcing data
#     contracts ensures data quality and prevents bad data from breaking downstream
#     pipelines, reports, or models.
#
# Q2: Why compile regular expression patterns using 're.compile()'?
#     When you call 're.match(pattern, text)', Python parses, compiles, and caches
#     the regex string at runtime. If you execute this inside a loop of 10,000 rows,
#     re-compiling wastes CPU cycles. Using 're.compile()' creates a reusable pattern
#     object once, speeding up matches.
#
# Q3: Why split validation pools (Clean vs Quarantine) instead of throwing errors?
#     In batch processing, if a single bad record out of 100,000 causes the program
#     to raise an exception and exit, the entire business pipeline stalls.
#     Split-validation quarantines only the corrupt records for audit while allowing
#     clean data to flow through, maintaining pipeline availability.
# ==============================================================================
