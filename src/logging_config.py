"""
================================================================================
RetailMax Enterprise Data Platform

Module:      logging_config.py
Purpose:     Rotating Logger Configurations for Auditing & Debugging
Author:      Himanshu Sardana
Copyright:   (c) 2026 RetailMax Corp. All rights reserved.
================================================================================
"""

import logging
import sys
from logging.handlers import RotatingFileHandler

from config import LOG_FILE_PATH


def setup_corporate_logging() -> None:
    """Configures system-wide logging with Console and Rotating File Handlers.

    Logs events to standard output (stream) and persists them in a rotating
    log file structure at the project root directory.
    """
    # Prevent duplicate handler assignment if called multiple times
    root_logger = logging.getLogger()
    if root_logger.hasHandlers():
        return

    # Set root logger level
    root_logger.setLevel(logging.DEBUG)

    # Log format pattern
    log_format = logging.Formatter(
        "[%(asctime)s] [%(levelname)-8s] [%(name)s:%(funcName)s:%(lineno)d] - %(message)s"
    )

    # 1. Console Handler (Standard Output)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(log_format)
    root_logger.addHandler(console_handler)

    # 2. Rotating File Handler (5 MB max file size, 3 backup rotations)
    try:
        file_handler = RotatingFileHandler(
            filename=LOG_FILE_PATH,
            maxBytes=5 * 1024 * 1024,  # 5 Megabytes
            backupCount=3,
            encoding="utf-8",
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(log_format)
        root_logger.addHandler(file_handler)
    except Exception as e:
        # Fallback if log directory is unwritable
        print(f"CRITICAL ERROR: Failed to initialize file logger: {e}", file=sys.stderr)


# Self-execute on import to guarantee availability of root logging configurations
setup_corporate_logging()


def get_logger(name: str) -> logging.Logger:
    """Helper method to return a configured module-level logger instance.

    Args:
        name: Typically __name__ of the calling module.

    Returns:
        logging.Logger: Configured logger.
    """
    return logging.getLogger(name)


# ==============================================================================
# INTERVIEW NOTES & PITFALLS:
# 1. Why is 'print()' bad in production?
#    - No standard timestamps or log levels (INFO vs ERROR vs DEBUG).
#    - No log rotation (will fill up disk space if redirected to text).
#    - Not thread-safe (can result in interleaved, scrambled lines).
# 2. What is log propagation?
#    - Child loggers (e.g. 'retailmax.database') propagate messages upwards to
#      the root logger. If propagation is set to True, handlers on parent loggers
#      will also process the record.
# ==============================================================================
