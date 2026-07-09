"""
================================================================================
RetailMax Enterprise Data Platform

Module:      constants.py
Purpose:     Central Business Rules and Constant Bindings
Author:      Himanshu Sardana
Copyright:   (c) 2026 RetailMax Corp. All rights reserved.
================================================================================
"""

from typing import Final

# ==============================================================================
# BUSINESS DATA CONTRACT RULES
# ==============================================================================

# List of corporate-approved departments (sprint 5: data contracts verification)
APPROVED_DEPARTMENTS: Final[list[str]] = ["HR", "Engineering", "Finance", "Sales", "Marketing"]

# Salary constraints in INR / local currency monthly payout limits
MIN_MONTHLY_SALARY: Final[float] = 15000.00
MAX_MONTHLY_SALARY: Final[float] = 300000.00

# Performance score bounds (1 = Unsatisfactory, 5 = Outstanding)
MIN_PERFORMANCE_SCORE: Final[int] = 1
MAX_PERFORMANCE_SCORE: Final[int] = 5

# Default designation for newly onboarded personnel
DEFAULT_DESIGNATION: Final[str] = "Associate"

# Standard email domain check
CORPORATE_EMAIL_SUFFIX: Final[str] = "@retailmax.com"

# Standard DateTime format used for corporate database migration
DATE_FORMAT: Final[str] = "%Y-%m-%d"


# ==============================================================================
# FINANCIAL REVENUE AND TAX CALCULATION RULES
# ==============================================================================

# Financial multipliers (Sprint 2 & 11)
ANNUAL_MONTHS: Final[int] = 12
BONUS_MULTIPLIER: Final[float] = 0.10  # 10% annual bonus
TAX_MULTIPLIER: Final[float] = 0.08  # 8% income tax


# ==============================================================================
# INGESTION API DETAILS
# ==============================================================================

# REST API endpoint for corporate simulations (Sprint 3 & Phase 4)
EMPLOYEE_API_URL: Final[str] = "https://jsonplaceholder.typicode.com/users"

# Async Auxiliary endpoint mocks
MOCK_WEATHER_URL: Final[str] = (
    "https://api.open-meteo.com/v1/forecast?latitude=12.9716&longitude=77.5946&current_weather=true"
)
MOCK_HOLIDAY_URL: Final[str] = "https://date.nager.at/api/v3/PublicHolidays/2026/IN"
MOCK_TIME_URL: Final[str] = "https://worldtimeapi.org/api/timezone/Asia/Kolkata"

# Network configuration limits
HTTP_TIMEOUT_SECONDS: Final[int] = 10


# ==============================================================================
# CHARTS & DESIGN AESTHETICS (Phase 3)
# ==============================================================================

# Palette mapping for dashboard charts
CHART_COLOR_PALETTE: Final[list[str]] = [
    "#1f77b4",  # Muted Blue
    "#ff7f0e",  # Safety Orange
    "#2ca02c",  # Cooked Green
    "#d62728",  # Brick Red
    "#9467bd",  # Royalty Purple
]

CHART_DPI: Final[int] = 100
CHART_FIGSIZE_WIDTH: Final[int] = 8
CHART_FIGSIZE_HEIGHT: Final[int] = 5
