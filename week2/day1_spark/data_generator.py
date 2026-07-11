#!/usr/bin/env python3
"""
RetailMax Employee Data Generator
Generates realistic, synthetic employee data at scale (up to millions of records)
for Week 2 - Day 1 Cloud Data Engineering PySpark training.

No external dependencies required (uses only standard library modules).
"""

import argparse
import csv
import datetime
import os
import random
import sys


# Pre-defined mock data pools for realistic generation
FIRST_NAMES = [
    "James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael", "Linda",
    "William", "Elizabeth", "David", "Barbara", "Richard", "Susan", "Joseph", "Jessica",
    "Thomas", "Sarah", "Charles", "Karen", "Christopher", "Nancy", "Daniel", "Lisa",
    "Matthew", "Betty", "Anthony", "Margaret", "Mark", "Sandra", "Donald", "Ashley",
    "Steven", "Kimberly", "Paul", "Emily", "Andrew", "Donna", "Joshua", "Michelle",
    "Kenneth", "Carol", "Kevin", "Amanda", "Brian", "Melissa", "George", "Deborah",
    "Timothy", "Stephanie", "Ronald", "Rebecca", "Edward", "Sharon", "Jason", "Laura",
    "Jeffrey", "Cynthia", "Ryan", "Kathleen", "Jacob", "Amy", "Gary", "Shirley",
    "Nicholas", "Angela", "Eric", "Helen", "Jonathan", "Anna", "Stephen", "Brenda",
    "Larry", "Pamela", "Justin", "Nicole", "Raymond", "Emma", "Gregory", "Samantha",
    "Joshua", "Katherine", "Jerry", "Christine", "Dennis", "Debra", "Walter", "Rachel",
    "Patrick", "Carolyn", "Peter", "Janet", "Harold", "Maria", "Douglas", "Heather"
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
    "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson",
    "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson",
    "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson", "Walker",
    "Young", "Allen", "King", "Wright", "Scott", "Torres", "Nguyen", "Hill",
    "Flores", "Green", "Adams", "Nelson", "Baker", "Hall", "Rivera", "Campbell",
    "Mitchell", "Carter", "Roberts", "Gomez", "Phillips", "Evans", "Turner", "Diaz",
    "Parker", "Cruz", "Edwards", "Collins", "Reyes", "Stewart", "Morris", "Morales",
    "Murphy", "Cook", "Rogers", "Gutierrez", "Ortiz", "Morgan", "Cooper", "Peterson",
    "Bailey", "Reed", "Kelly", "Howard", "Ramos", "Kim", "Cox", "Ward", "Richardson",
    "Watson", "Brooks", "Chavez", "Wood", "James", "Bennett", "Gray", "Mendoza"
]

DEPARTMENTS = [
    "Sales", "Engineering", "Marketing", "HR", "Finance", 
    "Operations", "Support", "Procurement", "Legal"
]

# Salary ranges by department to make data realistic
SALARY_RANGES = {
    "Sales": (45000, 95000),
    "Engineering": (85000, 160000),
    "Marketing": (50000, 105000),
    "HR": (48000, 90000),
    "Finance": (60000, 130000),
    "Operations": (55000, 110000),
    "Support": (40000, 75000),
    "Procurement": (50000, 95000),
    "Legal": (90000, 195000)
}

GENDERS = ["Male", "Female", "Non-binary"]

COUNTRIES = [
    "United States", "United Kingdom", "Canada", "Germany", "France", 
    "Japan", "Australia", "India", "Brazil", "Mexico", "Singapore", 
    "South Africa", "Spain", "Italy", "Netherlands", "Sweden", 
    "New Zealand", "Ireland", "Switzerland", "United Arab Emirates",
    "Saudi Arabia", "South Korea", "Denmark", "Norway", "Finland"
]


def generate_employee_row(emp_id):
    """Generates a single dictionary representing an employee record."""
    first_name = random.choice(FIRST_NAMES)
    last_name = random.choice(LAST_NAMES)
    name = f"{first_name} {last_name}"
    
    dept = random.choice(DEPARTMENTS)
    min_sal, max_sal = SALARY_RANGES[dept]
    # Standard deviation modeling for salary distribution
    salary = round(random.uniform(min_sal, max_sal), 2)
    
    age = random.randint(21, 65)
    gender = random.choice(GENDERS)
    country = random.choice(COUNTRIES)
    
    # Store ID modeling global RetailMax network (1 to 2000 stores)
    store_id = random.randint(1, 2000)
    
    # Hire date within the last 10 years
    start_date = datetime.date(2016, 1, 1)
    end_date = datetime.date(2026, 7, 1)
    time_between_dates = end_date - start_date
    days_between_dates = time_between_dates.days
    random_number_of_days = random.randrange(days_between_dates)
    hire_date = start_date + datetime.timedelta(days=random_number_of_days)
    
    # Active status
    is_active = "Yes" if random.random() < 0.92 else "No"
    
    return {
        "EmployeeID": emp_id,
        "Name": name,
        "Department": dept,
        "Salary": salary,
        "Age": age,
        "Gender": gender,
        "Country": country,
        "StoreID": store_id,
        "HireDate": hire_date.isoformat(),
        "IsActive": is_active
    }


def generate_dataset(output_path, num_records):
    """Generates the CSV file writing records in chunks for memory safety."""
    # Ensure directory exists
    dir_name = os.path.dirname(output_path)
    if dir_name and not os.path.exists(dir_name):
        os.makedirs(dir_name)

    headers = [
        "EmployeeID", "Name", "Department", "Salary", "Age", 
        "Gender", "Country", "StoreID", "HireDate", "IsActive"
    ]

    print(f"Generating {num_records:,} records...")
    print(f"Target file: {output_path}")

    # Chunk size for memory-friendly execution when writing millions of rows
    chunk_size = 100000
    records_written = 0

    with open(output_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()

        for chunk_start in range(1, num_records + 1, chunk_size):
            chunk_end = min(chunk_start + chunk_size, num_records + 1)
            chunk_rows = [generate_employee_row(i) for i in range(chunk_start, chunk_end)]
            writer.writerows(chunk_rows)
            records_written += len(chunk_rows)
            
            # Print progress indicators
            progress = (records_written / num_records) * 100
            sys.stdout.write(f"\rProgress: {progress:.1f}% ({records_written:,}/{num_records:,})")
            sys.stdout.flush()

    print("\nGeneration complete!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="RetailMax Synthetic Employee Data Generator.")
    parser.add_argument(
        "--output", "-o", 
        default="data/employees_large.csv", 
        help="Path where the CSV file should be saved"
    )
    parser.add_argument(
        "--records", "-n", 
        type=int, 
        default=10000, 
        help="Number of records to generate (default: 10,000)"
    )

    args = parser.parse_args()
    
    # Resolve absolute path relative to current script directory if path is relative
    out_path = args.output
    if not os.path.isabs(out_path):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        out_path = os.path.normpath(os.path.join(script_dir, out_path))

    generate_dataset(out_path, args.records)
