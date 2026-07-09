"""
================================================================================
RetailMax Enterprise Data Platform

Module:      data_transformer.py
Purpose:     ETL Data Transformation (JSON Payload flattening & Type casting)
Author:      Himanshu Sardana
Copyright:   (c) 2026 RetailMax Corp. All rights reserved.
================================================================================
"""

from typing import Any

from employee import Employee
from exceptions import ValidationError
from logging_config import get_logger

# Initialize logger
logger = get_logger("data_transformer")


class DataTransformer:
    """Transforms raw API user dictionary payloads into structured Employee objects.

    Flattens nested keys, maps columns, and performs deterministic derivations.
    """

    def transform_raw_payload(self, raw_users: list[dict[str, Any]]) -> list[Employee]:
        """Flattens and transforms a raw list of user dictionaries.

        Args:
            raw_users: A list of dictionary payloads from the remote REST API.

        Returns:
            List[Employee]: A list of validated, constructed Employee objects.

        Raises:
            APIPayloadError: If crucial fields are missing or corrupted.
        """
        logger.info(f"Starting transformation of {len(raw_users)} raw user payloads.")
        transformed_employees: list[Employee] = []

        for user in raw_users:
            try:
                # Extract and unpack nested company sub-dictionary
                company = user.get("company", {})

                # Determine basic values with safe defaults
                user_id = int(user["id"])
                name = str(user["name"])

                # Default department based on ID (deterministic cycle)
                departments = ["HR", "Engineering", "Finance", "Sales", "Marketing"]
                department = departments[user_id % len(departments)]

                # Derive designation from company business role or use default
                bs = company.get("bs", "Associate")
                designation = bs.split(" ")[0].capitalize() if bs else "Associate"
                if len(designation) < 3:
                    designation = "Associate"

                # Deterministic monthly salary based on employee ID: $40,000 + ID * $10,000
                salary = float(40000.00 + (user_id * 10000.00))

                # Joining Date simulation (2024-01-01 + ID days)
                joining_day = (user_id % 28) + 1
                joining_month = (user_id % 12) + 1
                joining_date = f"2024-{joining_month:02d}-{joining_day:02d}"

                # Performance score (id mod 5 + 1)
                performance_score = (user_id % 5) + 1

                # Construct Employee instance (which self-validates on init)
                emp = Employee(
                    employee_id=user_id + 2000,  # Offset to avoid conflict with initial CSV IDs
                    name=name,
                    department=department,
                    designation=designation,
                    salary=salary,
                    joining_date=joining_date,
                    performance_score=performance_score,
                )

                transformed_employees.append(emp)
                logger.debug(
                    f"Transformed raw user ID {user_id} into Employee ID {emp.employee_id}"
                )

            except (KeyError, ValueError, TypeError) as e:
                logger.warning(f"Skipping corrupted raw user record: {user}. Error: {e}")
                continue
            except ValidationError as ve:
                logger.warning(f"Record validation failed for raw user ID {user.get('id')}: {ve}")
                continue

        logger.info(
            f"DataFrame Transformation complete: Generated {len(transformed_employees)} Employee instances."
        )
        return transformed_employees


# ==============================================================================
# INTERVIEW NOTES & DATA NORMALIZATION MECHANICS:
#
# Q1: What is JSON Flattening and why is it necessary?
#     JSON is a hierarchical data format supporting nested objects (dicts inside dicts).
#     Relational databases (SQL) and tabular formats (CSV, DataFrames) are two-dimensional
#     grids (rows and columns). Flattening is the process of extracting nested fields
#     (e.g., user['address']['city']) and placing them on the root level (e.g., 'City' column)
#     so they can be mapped to database schemas.
#
# Q2: What is the difference between Deterministic and Stochastic transformations?
#     - Deterministic: An operation that always produces the exact same output given
#       the same inputs (e.g. mapping department based on user_id % 5). This is
#       crucial for reproducible unit testing.
#     - Stochastic: An operation that involves randomness or probability (e.g.
#       assigning random salaries). This is harder to test.
#
# Q3: Why is schema validation done during the transformation stage?
#     Validating schemas early in the pipeline (the "Fail-Fast" principle) prevents
#     corrupted, dirty, or incomplete records from reaching downstream storage
#     layers (SQL database or CSV files), which could cause integrity constraint
#     violations, application crashes, or dirty business analytics dashboards.
# ==============================================================================
