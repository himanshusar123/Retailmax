"""
================================================================================
RetailMax Enterprise Data Platform

Module:      config.py
Purpose:     Directory Resolutions and System Environments Settings
Author:      Himanshu Sardana
Copyright:   (c) 2026 RetailMax Corp. All rights reserved.
================================================================================
"""

from pathlib import Path

# ==============================================================================
# RESOLVING PROJECT DIRECTORIES (sprint 1: project structure)
# ==============================================================================

# Get absolute path of this config.py file
CONFIG_DIR = Path(__file__).resolve().parent

# Base directory representing the VS Code project root
# If config.py is inside the 'src' subfolder, the root is its parent directory.
BASE_DIR = CONFIG_DIR.parent if CONFIG_DIR.name == "src" else CONFIG_DIR

# Subdirectory configurations
DATA_DIR = BASE_DIR / "data"
DATABASE_DIR = BASE_DIR / "database"
CHARTS_DIR = BASE_DIR / "charts"
REPORTS_DIR = BASE_DIR / "reports"
LOGS_DIR = BASE_DIR

# Files paths
CSV_DATA_PATH = DATA_DIR / "employees.csv"
DB_PATH = DATABASE_DIR / "retailmax.db"
LOG_FILE_PATH = LOGS_DIR / "retailmax.log"


# ==============================================================================
# AUTO-INITIALIZE FOLDERS ON MODULE IMPORT
# ==============================================================================
def initialize_system_folders() -> None:
    """Creates directory nodes if they are missing.

    Prevents FileNotFoundError when write handlers execute.
    """
    for folder in [DATA_DIR, DATABASE_DIR, CHARTS_DIR, REPORTS_DIR]:
        folder.mkdir(parents=True, exist_ok=True)


# Execute setup
initialize_system_folders()


# ==============================================================================
# INTERVIEW NOTES & DESIGN QUESTIONS:
# 1. Why use 'pathlib.Path' over 'os.path'?
#    - Pathlib provides an object-oriented approach to filesystem paths,
#      cross-platform path separators (Windows backslash vs POSIX forward slash),
#      and safer concatenation operator '/'.
# 2. What is the VS Code 'cwd' issue?
#    - When running python files in VS Code, relative paths (e.g. "data/employees.csv")
#      are resolved relative to the folder open in the explorer, NOT the directory
#      the script lives in. Absolute path resolution via __file__.resolve() is the
#      industry-standard fix.
# ==============================================================================
