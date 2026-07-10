# Day 6 Lab: Enterprise Software Engineering Best Practices

Welcome to the final phase of the **RetailMax Developer Training Program**! 

## 📖 The Scenario
> **"The RetailMax application is complete. Before it can be deployed to production, the CTO has asked the Engineering Team to perform a Production Readiness Review."**

To demonstrate the importance of software engineering standards, you have been handed a legacy, monolithic payroll calculation script (`before/legacy_payroll.py`). It works, but it suffers from severe design flaws:
1. **No Modularization**: Database logic, calculation logic, and validation are all mixed in a single flat file (violating the Single Responsibility Principle).
2. **No Type Hints**: It relies on loose dynamic typing, leaving the system vulnerable to runtime crashes.
3. **No Repository Pattern**: Raw SQL queries are hardcoded directly inside business logic functions.
4. **No Automated Testing**: There are no unit or integration tests to verify calculations.
5. **No Code Quality Standards**: The formatting is messy, imports are unorganized, and there are static analysis issues.

Your mission in this lab is to refactor this script into an enterprise-grade, production-ready package (as shown in the `after/` folder) and run the full suite of code quality checks.

---

## 📅 Day 6 Curriculum Modules

| Module | Topic | Duration | Key Action / Command |
| :--- | :--- | :--- | :--- |
| **1** | **Project Refactoring** | 45 min | Modularize the single script into distinct architectural layers. |
| **2** | **Type Hints** | 45 min | Add strict type annotations to classes, variables, and functions. |
| **3** | **Design Patterns (Repository Pattern)** | 45 min | Extract SQLite database operations out of business logic. |
| **4** | **Packaging & Modular Architecture** | 60 min | Organize the files into standard `src/` and `tests/` directories. |
| **5** | **Unit Testing (pytest)** | 45 min | Write isolated pytest assertions to test payroll logic. Run `pytest`. |
| **6** | **Code Quality** | 45 min | Run `black .`, `ruff check .`, and `mypy .` to enforce clean standards. |
| **7** | **CI/CD Awareness** | 30 min | Review a GitHub Actions pipeline that automates QA on code push. |
| **8** | **Final Production Readiness Review** | 45 min | Verify the clean pipeline run and sign off for deployment! |

---

## 🛠️ The Production Readiness Checklist & Commands

Run these tools inside the `after/` directory to verify the codebase's compliance with modern standards:

### 1. Code Formatting (Black)
Enforce a uniform code style across the team.
```bash
# Check formatting compliance
black --check .

# Auto-format the entire project
black .
```

### 2. Fast Code Linting (Ruff)
Catch bugs, code smells, and unorganized imports instantly.
```bash
# Run the linter
ruff check .

# Automatically fix safe violations
ruff check . --fix
```

### 3. Static Type Verification (Mypy)
Verify type safety before running the code.
```bash
# Run static type checker
mypy .
```

### 4. Unit Testing (Pytest)
Run assertions to verify calculation correctness and edge cases.
```bash
# Execute unit test suite
pytest -v
### 5. Running the Application
Execute the refactored end-to-end pipeline. Because the package uses absolute imports starting from `src`, it must be run as a module from the `after/` directory:
```bash
# Run the application orchestrator
python -m src.main
```

---


## 📦 Architecture: Before vs. After

### Before (Monolithic & Fragile)
```
day6_readiness_review/
└── before/
    └── legacy_payroll.py  # Mixed DB, logic, formatting errors, no types
```

### After (Enterprise-Grade & Robust)
```
day6_readiness_review/
└── after/
    ├── src/
    │   ├── database/
    │   │   ├── connection.py  # SQLite Connection Context Manager
    │   │   └── repository.py  # Repository Pattern (isolating DB access)
    │   ├── models/
    │   │   └── employee.py    # Domain Data Model (with type hints)
    │   ├── services/
    │   │   └── payroll.py     # Core business logic (SRP)
    │   └── main.py            # Orchestrator
    ├── tests/
    │   └── test_payroll.py    # Unit tests with pytest fixtures
    ├── pyproject.toml         # Standard configurations for black, ruff, mypy, pytest
    ├── requirements.txt       # Lab dependencies
    └── README.md              # Instructions
```
