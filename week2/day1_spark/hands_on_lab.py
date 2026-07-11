#!/usr/bin/env python3
"""
RetailMax Cloud Data Engineering
Week 2 - Day 1: Hands-on Lab - RetailMax Global Expansion Department Analytics

This script solves the Day 1 Hands-on Lab requirements. It runs analytical metrics on
employee data using PySpark and exports the results into structured formats (CSV and Markdown).

Deliverables:
1. Total Headcount
2. Company-wide Average Salary
3. Company-wide Highest Salary
4. Headcount per Department
5. Top 10 Highest-earning Employees

Usage:
    python hands_on_lab.py
"""

import os
import sys

try:
    from pyspark.sql import SparkSession
    from pyspark.sql.functions import avg, max as spark_max, desc
except ImportError:
    print("Error: PySpark is not installed. Run: pip install pyspark")
    sys.exit(1)


def run_department_analytics(data_path, reports_dir):
    """Executes the Spark analytics and generates reports."""
    # Ensure reports directory exists
    os.makedirs(reports_dir, exist_ok=True)
    
    # 1. Initialize Spark Session
    spark = SparkSession.builder \
        .appName("RetailMax-Department-Analytics") \
        .master("local[*]") \
        .getOrCreate()
        
    print(f"Analyzing dataset: {data_path}")
    
    # 2. Ingest Data
    df = spark.read.csv(data_path, header=True, inferSchema=True)
    
    # 3. Calculate Deliverables
    # 3.1 Total Employees
    total_employees = df.count()
    
    # 3.2 & 3.3 Average and Highest Salary
    stats = df.agg(
        avg("Salary").alias("avg_salary"),
        spark_max("Salary").alias("max_salary")
    ).collect()[0]
    
    avg_salary = round(stats["avg_salary"], 2)
    max_salary = round(stats["max_salary"], 2)
    
    # 3.4 Department Count (headcount grouped by department)
    dept_counts = df.groupBy("Department").count().orderBy(desc("count"))
    dept_counts_list = dept_counts.collect()
    
    # 3.5 Top 10 Salaries
    top_10_salaries = df.select("EmployeeID", "Name", "Department", "Salary", "Country") \
                        .orderBy(desc("Salary")) \
                        .limit(10)
    top_10_list = top_10_salaries.collect()
    
    # ---------------------------------------------------------
    # 4. EXPORT RESULTS (CSV and Markdown Dashboard)
    # ---------------------------------------------------------
    # Save raw tables to CSV (converting back to pandas or writing directly)
    # Since Spark writes to directories (partition files) by default, we can write
    # to Pandas for small aggregations to output single flat CSVs (very convenient for BI).
    dept_counts_pd = dept_counts.toPandas()
    top_10_pd = top_10_salaries.toPandas()
    
    dept_csv_path = os.path.join(reports_dir, "department_headcounts.csv")
    top_10_csv_path = os.path.join(reports_dir, "top_10_salaries.csv")
    
    dept_counts_pd.to_csv(dept_csv_path, index=False)
    top_10_pd.to_csv(top_10_csv_path, index=False)
    
    # Write Markdown Dashboard
    dashboard_path = os.path.join(reports_dir, "department_analytics_dashboard.md")
    
    with open(dashboard_path, "w", encoding="utf-8") as f:
        f.write("# 📊 RetailMax Global Department Analytics Dashboard\n\n")
        f.write(f"**Execution Timestamp:** {spark.sparkContext.startTime}\n")
        f.write(f"**Data Source:** `{os.path.basename(data_path)}`\n\n")
        
        f.write("## 📈 Core Corporate Metrics\n")
        f.write("| Metric | Value |\n")
        f.write("| :--- | :--- |\n")
        f.write(f"| **Total Headcount** | {total_employees:,} employees |\n")
        f.write(f"| **Average Annual Salary** | ${avg_salary:,.2f} |\n")
        f.write(f"| **Highest Annual Salary** | ${max_salary:,.2f} |\n\n")
        
        f.write("## 🏢 Headcount by Department\n")
        f.write("| Department | Headcount | Percentage |\n")
        f.write("| :--- | :---: | :---: |\n")
        for row in dept_counts_list:
            pct = (row["count"] / total_employees) * 100
            f.write(f"| {row['Department']} | {row['count']:,} | {pct:.2f}% |\n")
        f.write("\n")
        
        f.write("## 🏆 Top 10 Salaries (Corporate Leaderboard)\n")
        f.write("| Rank | Employee ID | Name | Department | Country | Salary |\n")
        f.write("| :---: | :--- | :--- | :--- | :--- | :--- |\n")
        for i, row in enumerate(top_10_list, 1):
            f.write(f"| {i} | {row['EmployeeID']} | {row['Name']} | {row['Department']} | {row['Country']} | ${row['Salary']:,.2f} |\n")
            
        f.write("\n---\n*Report generated dynamically using Apache Spark Catalyst Optimizer Engine.*")
        
    print("\n" + "=" * 50)
    print("      DEPARTMENT ANALYTICS COMPLETE")
    print("=" * 50)
    print(f"Total Headcount:  {total_employees:,}")
    print(f"Average Salary:   ${avg_salary:,.2f}")
    print(f"Maximum Salary:   ${max_salary:,.2f}")
    print("-" * 50)
    print(f"CSV files exported to:  {reports_dir}")
    print(f"Markdown Dashboard:     {dashboard_path}")
    print("=" * 50)
    
    spark.stop()


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(script_dir, "data", "employees_sample.csv")
    reports_dir = os.path.join(script_dir, "reports")
    
    # Check/generate data
    if not os.path.exists(data_path):
        print("[Setup] Generating sample data (1,000 records) for lab...")
        sys.path.append(script_dir)
        import data_generator
        data_generator.generate_dataset(data_path, num_records=1000)
        
    run_department_analytics(data_path, reports_dir)


if __name__ == "__main__":
    main()
