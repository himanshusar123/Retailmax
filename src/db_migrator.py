"""
================================================================================
RetailMax Enterprise Data Platform

Module:      db_migrator.py
Purpose:     ETL Database Migrator (CSV Flat File -> SQLite Relational DB)
Author:      Himanshu Sardana
Copyright:   (c) 2026 RetailMax Corp. All rights reserved.
================================================================================
"""

import time
from pathlib import Path

from config import CSV_DATA_PATH, DB_PATH
from csv_handler import CSVHandler
from database import DatabaseHandler, initialize_database
from exceptions import CSVHandlerError, DatabaseError, DatabaseMigrationError
from logging_config import get_logger

# Initialize logger
logger = get_logger("db_migrator")


class DatabaseMigrator:
    """Orchestrates the ETL migration pipeline.

    Extracts employee records from CSV, validates and transforms records,
    and loads them into SQLite database within transactional batches.
    """

    def __init__(self, csv_path: Path = CSV_DATA_PATH, db_path: Path = DB_PATH) -> None:
        """Initializes the database migrator.

        Args:
            csv_path: Flat-file source path.
            db_path: Target relational database path.
        """
        self.csv_path = csv_path
        self.db_path = db_path
        self.csv_handler = CSVHandler(self.csv_path)
        self.db_handler = DatabaseHandler(str(self.db_path))
        logger.debug(f"DatabaseMigrator initialized: CSV={csv_path} -> SQLite={db_path}")

    def migrate(self) -> tuple[int, float]:
        """Executes the ETL migration pipeline.

        - Extract: Read from CSV handler.
        - Load: Batch insert into SQLite.

        Returns:
            Tuple[int, float]: (number of successfully migrated records, time elapsed).

        Raises:
            DatabaseMigrationError: If migration fails.
        """
        logger.info("=== Starting Database Migration ETL Process ===")
        start_time = time.perf_counter()

        # Step 1: Initialize DB schema rules
        try:
            initialize_database(str(self.db_path))
        except Exception as e:
            raise DatabaseMigrationError(f"Migration aborted. Schema setup failed: {e}")

        # Step 2: Extract data from CSV
        try:
            logger.info(f"Extracting records from CSV source: {self.csv_path}")
            csv_records = self.csv_handler.read_all()
            if not csv_records:
                logger.warning("No records extracted from CSV source. Ending migration.")
                return 0, 0.0
        except CSVHandlerError as che:
            raise DatabaseMigrationError(f"Migration aborted during extraction phase: {che}")

        # Step 3: Load records into SQLite using transaction batch
        logger.info(f"Loading {len(csv_records)} records into SQLite database...")
        try:
            # Clear existing table to avoid unique constraint violations on re-run
            # This makes migration repeatable (Idempotent)
            # Re-fetch connection manager block to clear table
            from database import SQLiteConnectionManager

            with SQLiteConnectionManager(str(self.db_path)) as conn:
                conn.execute("DELETE FROM employees;")
                conn.commit()
                logger.info("Cleaned target database table 'employees' for clean migration.")

            # Load batch
            inserted_count = self.db_handler.insert_employees_batch(csv_records)

            elapsed = time.perf_counter() - start_time
            logger.info(
                f"=== Migration Successful! Migrated {inserted_count} employees in {elapsed:.4f} seconds ==="
            )
            return inserted_count, elapsed

        except DatabaseError as de:
            raise DatabaseMigrationError(f"Migration failed during database load phase: {de}")
        except Exception as e:
            raise DatabaseMigrationError(f"Migration aborted due to unexpected failure: {e}")


if __name__ == "__main__":
    # Test script run
    import sys

    try:
        migrator = DatabaseMigrator()
        count, duration = migrator.migrate()
        print(f"Migration complete: {count} records loaded in {duration:.4f}s.")
    except Exception as err:
        print(f"Migration failed: {err}", file=sys.stderr)
        sys.exit(1)


# ==============================================================================
# INTERVIEW NOTES & DESIGN PATTERNS:
#
# Q1: What is ETL?
#     ETL stands for Extract, Transform, Load:
#     - Extract: Gathering raw data from source systems (flat CSV files, web scraping).
#     - Transform: Normalizing structures, checking types, filtering bad records,
#       enriching fields.
#     - Load: Persisting clean data in target storage systems (relational databases,
#       data lakes).
#
# Q2: Why is batch insertion in a transaction faster than inserting row-by-row?
#     In standard SQLite, executing DML triggers disk write synchronization on every
#     commit. If you insert 100 records row-by-row, SQLite will open/close and flush
#     data to physical disk 100 times ($O(N)$ write cycles).
#     By running a single transaction batch ('BEGIN' and 'COMMIT'), all insert statements
#     are written to database buffers in memory first, and flushed to disk exactly once
#     ($O(1)$ write cycles), reducing execution time by 10x-100x.
#
# Q3: What is Idempotence in pipeline design?
#     An idempotent operation is one that can be executed multiple times without
#     changing the result beyond the initial application. In our migrator, we run
#     'DELETE FROM employees' before inserting, guaranteeing that running the migrator
#     multiple times won't corrupt the database or create duplicates.
# ==============================================================================
