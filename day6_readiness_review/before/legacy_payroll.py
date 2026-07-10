# ==============================================================================
# RetailMax Legacy Payroll Processor (Monolithic Script)
#
# Flaws in this script:
# 1. No modularization: DB schema creation, connection, calculation, and
#    reporting are all crammed together.
# 2. No type hints: Hard to understand what types functions expect or return.
# 3. Direct SQLite queries in business logic: No isolation of SQL code.
# 4. PEP-8 Violations: Bad spacing, inconsistent indentation, unused imports.
# ==============================================================================

import sqlite3
import sys # Unused import (Ruff will flag)
import os  # Unused import (Ruff will flag)

def calculate_payroll_and_persist(emp_id,name,salary,perf_score):
    # PEP-8: bad spacing around commas and operators
    # Mypy: no type hints
    
    # Validation
    if salary <= 0:
        raise ValueError("Salary must be positive")
        
    # Calculation logic (Business logic)
    bonus_multiplier = 0.0
    if perf_score == 5:
        bonus_multiplier = 0.20
    elif perf_score == 4:
         bonus_multiplier = 0.10 # Bad indentation (Black/Ruff will flag)
    elif perf_score == 3:
        bonus_multiplier = 0.05
    else:
        bonus_multiplier = 0.00
        
    bonus = salary * bonus_multiplier
    tax = (salary + bonus) * 0.15 # 15% flat tax rate
    net_pay = salary + bonus - tax
    
    # DB persistence directly inline (Violates Repository Pattern and SRP)
    connection = sqlite3.connect("legacy_retailmax.db")
    cursor = connection.cursor()
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS employee_payroll (
        employee_id INTEGER PRIMARY KEY,
        name TEXT,
        salary REAL,
        bonus REAL,
        tax REAL,
        net_pay REAL
    )
    """)
    
    cursor.execute("""
    INSERT OR REPLACE INTO employee_payroll (employee_id, name, salary, bonus, tax, net_pay)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (emp_id, name, salary, bonus, tax, net_pay))
    
    connection.commit()
    connection.close()
    
    # Return dictionary with raw untyped data
    return {
        "emp_id": emp_id,
        "name": name,
        "net_pay": net_pay
    }

if __name__ == "__main__":
    # Main orchestration mixed directly at module level
    print("Running Legacy Payroll...")
    
    # Dummy list of employee data
    employees = [
        (101, "Alice Smith", 80000.0, 5),
        (102, "Bob Jones", 60000.0, 4),
        (103, "Charlie Brown", 50000.0, 2)
    ]
    
    for emp in employees:
        result = calculate_payroll_and_persist(emp[0], emp[1], emp[2], emp[3])
        print(f"Processed: {result['name']} -> Net Pay: ${result['net_pay']:.2f}")
