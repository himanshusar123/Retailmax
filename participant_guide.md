# RetailMax Enterprise Data Platform - Participant Study Guide

Welcome to the **RetailMax Developer Training Program**. This guide is your companion as you progress from a beginner scriptwriter to an enterprise-grade backend developer. 

Through this course, you will build and evolve the **RetailMax Enterprise Data Platform**. You will learn the mechanics of clean code, Object-Oriented Programming (OOP), file manipulation, relational databases, data pipelines, business intelligence visualizations, concurrent programming, and automated unit testing.

---

## 📅 Curriculum Roadmap Overview

```
 ───────────────         ───────────────         ───────────────         ───────────────         ───────────────
│    Day 1      │  ───► │    Day 2      │  ───► │    Day 3      │  ───► │    Day 4      │  ───► │    Day 5      │
│  Core & OOP   │       │ File Handling │       │ Database & SQL│       │ Pandas & BI   │       │  Production   │
 ───────────────         ───────────────         ───────────────         ───────────────         ───────────────
```

* **Day 1 – Core Application & OOP:** Basic variables, calculations, functions, Object-Oriented Programming (classes/instances/methods), lists, error handling, and terminal menu-driven portals.
* **Day 2 – File Handling:** `os` and `pathlib` navigation, reading/writing CSV flat-files, search filters, and transactional file replacements.
* **Day 3 – Relational Databases:** SQLite, SQL tables, primary keys, indexes, DML commands, parameterized queries, and ACID batch transactions.
* **Day 4 – Data Analytics & BI:** Pandas Series/DataFrames, vectorized operations, data cleaning (nulls, duplicates), KPIs, and Matplotlib data visualization.
* **Day 5 – Enterprise Packaging & APIs:** Consuming REST APIs (requests), Asynchronous concurrency (`asyncio`/`httpx`), code isolation, custom exceptions, rotating logs, Pytest unit tests, and static linting (`black`/`ruff`/`mypy`).

---

## 📘 Day 1: Core Programming & Object-Oriented Python

### 🎯 Key Concepts
1. **Scoping and Lifetimes:**
   Variables defined inside functions live only during execution (local scope). Global variables live at the module level.
2. **Encapsulation:**
   Bundling data and operations inside classes. Private attributes are prefixed with single or double underscores to hide them from direct external modifications.
3. **Properties (@property):**
   A pythonic way to implement getters and setters. They allow intercepting field reads and writes to enforce validation rules.
4. **Dunder Methods:**
   Double-underscore methods like `__init__`, `__str__` (for users), and `__repr__` (for developer debugging).

### 📝 Day 1 Coding Challenge
Create an `Employee` class that enforces:
- `employee_id` must be a positive integer.
- `salary` must be positive.
- Calculate annual salary, bonus (10%), and net payout (8% tax).

#### Solution Template:
```python
class Employee:
    def __init__(self, emp_id: int, name: str, salary: float):
        if emp_id <= 0:
            raise ValueError("ID must be positive.")
        if salary <= 0:
            raise ValueError("Salary must be positive.")
        self.emp_id = emp_id
        self.name = name
        self.salary = salary

    def annual_salary(self) -> float:
        return self.salary * 12

    def calculate_bonus(self) -> float:
        return self.annual_salary() * 0.10

    def calculate_tax(self) -> float:
        return self.annual_salary() * 0.08

    def net_salary(self) -> float:
        return self.annual_salary() + self.calculate_bonus() - self.calculate_tax()
```

---

## 📗 Day 2: File Ingestion & Flat File Storage

### 🎯 Key Concepts
1. **Context Managers (`with` statement):**
   Guarantees that files are closed automatically when execution leaves the block, even if errors are raised, preventing memory leaks and file descriptor exhaustion.
2. **CSV Dialects:**
   CSV files use specific character delimiters (commas, tabs) and line endings (`\r\n` or `\n`). We use `newline=""` in Python's `open()` on Windows to prevent extra blank lines.
3. **Atomic Writes:**
   Writing directly to a target file risks corrupting it if the program crashes mid-write. Creating a temporary file and swapping it using `os.replace()` is the industry standard for atomic updates.

### 📝 Day 2 Coding Challenge
Write a function that reads a CSV file of employees and returns the headcount.

#### Solution Template:
```python
import csv

def get_csv_headcount(filepath: str) -> int:
    try:
        with open(filepath, mode="r", newline="", encoding="utf-8") as f:
            reader = csv.reader(f)
            rows = list(reader)
            # Exclude header row if file is not empty
            return max(0, len(rows) - 1)
    except FileNotFoundError:
        return 0
```

---

## 📙 Day 3: Relational Persistence with SQLite

### 🎯 Key Concepts
1. **Relational Constraints:**
   Primary keys ensure row uniqueness. Foreign keys enforce relationships. `CHECK` constraints validate bounds (e.g. `CHECK(salary >= 0)`).
2. **SQL Injection:**
   Never concatenate variables directly into SQL queries. Hackers can input values like `' OR 1=1;` to drop tables. Parameterized queries use placeholders (`?`) to treat inputs as raw data values.
3. **ACID Transactions:**
   - **Atomicity:** All statements in a transaction commit together or roll back.
   - **Consistency:** Database transitions from one valid state to another.
   - **Isolation:** Concurrent transactions don't interfere with each other.
   - **Durability:** Data survives power losses or system crashes.
4. **Indexes:**
   B-Tree structures that speed up search filters (e.g. `idx_emp_dept`) from slow $O(N)$ table scans to fast $O(\log N)$ index lookups.

### 📝 Day 3 Coding Challenge
Implement a transaction block that inserts three employees, rolling back the entire operation if one fails.

#### Solution:
```python
import sqlite3

def insert_employees_transaction(db_path: str, employees: list) -> None:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("BEGIN TRANSACTION;")
        for emp in employees:
            cursor.execute(
                "INSERT INTO employees VALUES (?, ?, ?, ?);",
                (emp.id, emp.name, emp.dept, emp.salary)
            )
        conn.commit()
    except sqlite3.Error as e:
        conn.rollback()
        raise RuntimeError(f"Transaction rolled back: {e}")
    finally:
        conn.close()
```

---

## 📊 Day 4: Data Engineering & Analytics with Pandas

### 🎯 Key Concepts
1. **Loops vs Vectorization:**
   Looping through 10,000 rows in Python is slow. Pandas uses vectorized operations compiled in C to execute operations on whole arrays instantly.
2. **Data Cleaning:**
   - `drop_duplicates()`: Removes duplicate rows.
   - `fillna()`: Imputes missing values (e.g., substituting median salaries for nulls).
   - `pd.to_datetime()`: Standardizes malformed strings to datetime objects.
3. **Matplotlib Visualizations:**
   Using non-interactive backends like `matplotlib.use('Agg')` is required in server environments where no graphical display exists.

### 📝 Day 4 Assessment (Multiple-Choice Questions)

**1. Why are vectorized operations in Pandas preferred over standard Python loops for large datasets?**
* [ ] A) They use less disk storage.
* [x] B) They execute operations in optimized C under the hood, running operations in parallel across arrays rather than element-by-element in Python.
* [ ] C) They automatically write data to a database.
* [ ] D) They do not support missing data.

**2. Which command would you use to find the count of non-null values and data types of all columns in a DataFrame?**
* [ ] A) `df.describe()`
* [ ] B) `df.shape`
* [x] C) `df.info()`
* [ ] D) `df.columns`

**3. What does the `df.drop_duplicates(subset=["EmployeeID"], keep="first")` operation do?**
* [ ] A) It deletes the entire dataset except the first row.
* [ ] B) It deletes the EmployeeID column.
* [x] C) It removes rows with duplicate EmployeeIDs, retaining only the first occurrence in the dataset.
* [ ] D) It throws an error if duplicates are found.

---

## 🚀 Day 5: Production Ready Architectures & APIs

### 🎯 Key Concepts
1. **Asynchronous Non-blocking I/O (`asyncio` / `httpx`):**
   Standard requests block the CPU while waiting for a response. Asynchronous calls allow other coroutines to execute while waiting for network I/O.
2. **Mypy Static Typing:**
   Enforces type safety at compile time, catching bugs before runtime.
3. **Rotating Log Handlers:**
   Prevents log files from consuming infinite disk space by rotating files at fixed sizes (e.g., 5MB) and retaining a limited number of backups.
4. **Pytest Unit Testing:**
   Using assertion blocks and isolated fixtures (`tmp_path`) to verify code correctness under clean conditions.

### 📝 Day 5 Coding Challenge
Write a pytest fixture that initializes a dummy database and returns the path.

#### Solution:
```python
import pytest
from pathlib import Path
from database import initialize_database

@pytest.fixture
def test_db(tmp_path: Path) -> str:
    db_file = tmp_path / "test.db"
    initialize_database(str(db_file))
    return str(db_file)
```

---

## 💡 Interview Preparation Q&A

### Q: Why is `print()` discouraged in corporate production systems?
* **A:** Printing lacks timestamp headers, severity levels (DEBUG, INFO, WARNING, ERROR), and thread-safety. In production, logs must be routed to rotating files, external aggregate databases, or standard error streams using a structured logging framework.

### Q: What is the benefit of custom exception classes?
* **A:** Catching generic exceptions (like `ValueError` or `Exception`) can mask other errors. Custom exceptions (like `EmployeeValidationError`) let callers selectively handle expected domain-level issues without catching and masking system faults.

### Q: Explain the difference between Concurrency and Parallelism.
* **A:** Concurrency is about *structure*—handling multiple tasks in overlapping intervals by interleaving them on a single core (e.g., async I/O). Parallelism is about *execution*—running multiple operations simultaneously across multiple physical CPU cores.
