#!/usr/bin/env python3
"""
RetailMax Cloud Data Engineering
Week 2 - Day 1: Pandas vs PySpark Comparison

This script benchmarks and compares Pandas with PySpark side-by-side on equivalent tasks.
It demonstrates:
1. Syntax alignment (how common transformations translate between libraries).
2. Processing paradigms (In-Memory, Eager, Single-threaded vs. Distributed, Lazy, Multi-threaded).
3. Runtime differences for file load, filtering, and aggregation.

Before running, ensure both libraries are installed:
    pip install pandas pyspark
"""

import os
import sys
import time

# Verify import availability
try:
    import pandas as pd
except ImportError:
    print("Error: Pandas is required for this comparison. Run: pip install pandas")
    sys.exit(1)

try:
    from pyspark.sql import SparkSession
    from pyspark.sql.functions import avg, col
except ImportError:
    print("Error: PySpark is required for this comparison. Run: pip install pyspark")
    sys.exit(1)


def benchmark_pandas(file_path):
    print("\n--- Running Pandas Benchmark ---")
    start_total = time.time()
    
    # 1. Load data
    t0 = time.time()
    df = pd.read_csv(file_path)
    t_load = time.time() - t0
    print(f"Pandas load time: {t_load:.4f} seconds")
    
    # 2. Filter & Group By Aggregation
    # Scenario: Find the average salary of Active employees in each Country for the "Engineering" department.
    t0 = time.time()
    filtered_df = df[(df["Department"] == "Engineering") & (df["IsActive"] == "Yes")]
    grouped_df = filtered_df.groupby("Country")["Salary"].mean().reset_index()
    # Sort for deterministic output
    result = grouped_df.sort_values(by="Salary", ascending=False)
    t_process = time.time() - t0
    
    total_time = time.time() - start_total
    print(f"Pandas execution time: {t_process:.4f} seconds")
    print(f"Pandas Total (Load + Execute): {total_time:.4f} seconds")
    
    print("\nPandas top 3 results:")
    print(result.head(3).to_string(index=False))
    
    return total_time


def benchmark_pyspark(file_path):
    print("\n--- Running PySpark Benchmark ---")
    start_total = time.time()
    
    # Initialize Session
    t0 = time.time()
    spark = SparkSession.builder \
        .appName("RetailMax-Pandas-Vs-Spark") \
        .master("local[*]") \
        .config("spark.sql.shuffle.partitions", "8") \
        .getOrCreate()
    t_session = time.time() - t0
    print(f"SparkSession startup time: {t_session:.4f} seconds")
    
    # 1. Load data
    # Note: Spark's read is lazy (especially with schema inference turned off,
    # but with inferSchema=True, it reads some lines eagerly to guess columns).
    t0 = time.time()
    df = spark.read.csv(file_path, header=True, inferSchema=True)
    # We force a count action to ensure the file is actually parsed/loaded for timing purposes.
    row_count = df.count()
    t_load = time.time() - t0
    print(f"Spark read & count time ({row_count:,} records): {t_load:.4f} seconds")
    
    # 2. Filter & Group By Aggregation
    t0 = time.time()
    # Build the transformation DAG (lazy)
    transformed_df = df.filter(
        (col("Department") == "Engineering") & (col("IsActive") == "Yes")
    ).groupBy("Country").agg(
        avg("Salary").alias("Average_Salary")
    ).orderBy("Average_Salary", ascending=False)
    
    # Trigger execution action (.collect() brings results to the driver node)
    results = transformed_df.collect()
    t_process = time.time() - t0
    
    total_time = time.time() - start_total
    print(f"Spark execution time (Collect): {t_process:.4f} seconds")
    print(f"Spark Total (Session + Load + Execute): {total_time:.4f} seconds")
    
    print("\nPySpark top 3 results:")
    for row in results[:3]:
        print(f"Country: {row['Country']:<15} Average_Salary: {row['Average_Salary']:.2f}")
        
    spark.stop()
    return total_time


def main():
    print("=" * 70)
    print("       RetailMax Technology Benchmark: Pandas vs. PySpark")
    print("=" * 70)
    
    # Generate data if not exists (using 100k rows for realistic bench)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.normpath(os.path.join(script_dir, "data", "employees_benchmark.csv"))
    
    if not os.path.exists(csv_path):
        print("[Setup] Generating benchmark dataset of 100,000 records...")
        sys.path.append(script_dir)
        import data_generator
        data_generator.generate_dataset(csv_path, num_records=100000)
    else:
        print(f"[Setup] Benchmark dataset exists: {csv_path}")
        
    # Run benchmarks
    pandas_time = benchmark_pandas(csv_path)
    spark_time = benchmark_pyspark(csv_path)
    
    print("\n" + "=" * 70)
    print("                    KEY PARADIGM COMPARISON")
    print("=" * 70)
    print("""
Feature               | Pandas                           | PySpark
----------------------|----------------------------------|----------------------------------
Scale Capability      | Small Data (< RAM size of node)  | Big Data (Multi-Terabyte / PB)
Execution Model       | Eager Evaluation                 | Lazy Evaluation (DAG execution)
CPU Utilization       | Single Core (GIL Constrained)    | Multi-core & Multi-node Parallel
Memory Management     | All in RAM (Crashes on OOM)      | In-memory caching + disk spillover
Architecture          | Single Process                   | Driver/Executor Cluster model
    """)
    print("=" * 70)
    
    # Analysis note
    print("\n[Trainer Note] Benchmark observations:")
    print("1. For small-to-medium files (100k rows), Pandas can be faster than Spark because Spark")
    # Clean output formatting
    print("   has initialization overhead (JVM startup, Driver/Executor handshake).")
    print("2. When dataset size exceeds physical RAM (e.g. 50GB file on 16GB RAM laptop), Pandas will crash")
    print("   with an Out of Memory (OOM) error, whereas Spark will process it in partitions and succeed.")
    print("=" * 70)


if __name__ == "__main__":
    main()
