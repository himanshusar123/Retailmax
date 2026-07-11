#!/usr/bin/env python3
"""
RetailMax Cloud Data Engineering
Week 2 - Day 1: PySpark Basics Tutorial

This script is a hands-on, step-by-step introduction to PySpark.
It illustrates:
1. Creating a SparkSession.
2. Loading structured CSV data.
3. Interrogating the data using basic actions.
4. Performing core transformations.
5. Understanding lazy evaluation and DAGs.

To run this script:
    pip install pyspark
    python spark_basics.py
"""

import sys
import os

# Ensure we can import pyspark; provide guidance if missing.
try:
    from pyspark.sql import SparkSession
    from pyspark.sql.functions import avg, col, desc, max as spark_max
except ImportError:
    print("Error: PySpark is not installed in your current environment.")
    print("Please install it using: pip install pyspark")
    sys.exit(1)


def main():
    print("=" * 60)
    print("       Starting RetailMax PySpark Basics Tutorial")
    print("=" * 60)

    # ---------------------------------------------------------
    # 1. INITIALIZING SPARKSESSION
    # ---------------------------------------------------------
    # Think of SparkSession as the entry point to Spark SQL and DataFrame API.
    # It acts as the driver program that coordinates execution on the cluster.
    # .master("local[*]") tells Spark to run locally and spawn as many worker threads
    # as there are logical CPU cores on your laptop.
    print("\n[Step 1] Initializing SparkSession...")
    spark = SparkSession.builder \
        .appName("RetailMax-Basics-Tutorial") \
        .master("local[*]") \
        .getOrCreate()
        
    print(f"SparkSession active. App Name: {spark.sparkContext.appName}")
    print(f"Spark Version: {spark.version}")

    # ---------------------------------------------------------
    # 2. ENSURING MOCK DATA EXISTS
    # ---------------------------------------------------------
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(script_dir, "data")
    csv_path = os.path.join(data_dir, "employees_sample.csv")

    if not os.path.exists(csv_path):
        print(f"\n[Step 2] Local sample data not found. Invoking generator...")
        # Import the generator script we just created to keep things self-contained
        sys.path.append(script_dir)
        import data_generator
        data_generator.generate_dataset(csv_path, num_records=1000)
    else:
        print(f"\n[Step 2] Using existing sample dataset at: {csv_path}")

    # ---------------------------------------------------------
    # 3. READING CSV FILE
    # ---------------------------------------------------------
    # header=True: Treats first line as column header.
    # inferSchema=True: Spark reads a portion of the file to determine data types.
    # Note: In production enterprise environments, you should explicitly specify the schema
    # using a StructType to avoid the overhead of scanning the file twice.
    print("\n[Step 3] Reading CSV dataset into PySpark DataFrame...")
    df = spark.read.csv(
        csv_path,
        header=True,
        inferSchema=True
    )
    print("Data successfully loaded. Let's inspect the object type:")
    print(f"Object type: {type(df)}")

    # ---------------------------------------------------------
    # 4. FIRST SPARK OPERATIONS (Actions & Metadata)
    # ---------------------------------------------------------
    print("\n[Step 4.1] Displaying the first 5 records (df.show):")
    df.show(5, truncate=False)

    print(f"[Step 4.2] Counting total records (df.count): {df.count()}")

    print("\n[Step 4.3] Printing DataFrame Schema (df.printSchema):")
    df.printSchema()

    print(f"\n[Step 4.4] Listing DataFrame Columns: {df.columns}")

    print("\n[Step 4.5] Generating summary statistics (df.describe):")
    # Note: describe() is a transformation; we call show() to trigger it and display the output.
    df.describe("Salary", "Age").show()

    # ---------------------------------------------------------
    # 5. SPARK TRANSFORMATIONS (Lazy Evaluation)
    # ---------------------------------------------------------
    # In Spark, operations are divided into:
    # 1. Transformations: Lazy operations that build a logical execution plan (DAG) but don't compute results.
    # 2. Actions: Eager operations that trigger execution and return results to the driver.
    
    print("\n[Step 5.1] Transformation: Filter (Finance Department only)")
    # Using column object notation
    finance_df = df.filter(col("Department") == "Finance")
    print(f"  Note: We filtered the dataframe. Spark hasn't run the query yet!")
    print(f"  Triggering Action (show/count) to compute and display results:")
    finance_df.show(5)
    print(f"  Finance headcount: {finance_df.count()}")

    print("\n[Step 5.2] Transformation: Select specific columns")
    selected_df = df.select("Name", "Department", "Salary")
    selected_df.show(3)

    print("\n[Step 5.3] Transformation: Sorting / Ordering")
    # Show top 5 highest paid employees
    sorted_df = df.orderBy(desc("Salary"))
    sorted_df.show(5)

    print("\n[Step 5.4] Transformation: GroupBy & Count")
    # Compute employee counts per department
    dept_counts = df.groupBy("Department").count()
    print("  Department Counts:")
    dept_counts.show()

    print("\n[Step 5.5] Transformation: Aggregations (Average & Max Salary per Department)")
    # Group by department and compute average & maximum salary
    dept_salary_stats = df.groupBy("Department").agg(
        avg("Salary").alias("Average_Salary"),
        spark_max("Salary").alias("Max_Salary")
    )
    print("  Salary Statistics by Department:")
    # Rounding averages for clean presentation
    dept_salary_stats.select(
        col("Department"),
        avg("Average_Salary").alias("Avg_Sal"), # placeholder to illustrate chain
        "Max_Salary"
    )
    # Let's display and format the aggregated DataFrame
    dept_salary_stats.orderBy("Average_Salary", ascending=False).show()

    # ---------------------------------------------------------
    # 6. CLEANUP
    # ---------------------------------------------------------
    # Always close the SparkSession when done to release system resources,
    # shutdown JVM gateways, and cleanup temporary scratch directories.
    print("\n[Step 6] Shutting down SparkSession...")
    spark.stop()
    print("SparkSession stopped. Tutorial execution complete.")
    print("=" * 60)


if __name__ == "__main__":
    main()
