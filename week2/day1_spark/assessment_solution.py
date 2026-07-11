#!/usr/bin/env python3
"""
RetailMax Cloud Data Engineering
Week 2 - Day 1: Assessment Solution - Large-Scale Global Acquisition Analytics

Scenario:
RetailMax has acquired 300 new stores, bringing in an employee dataset of 5,000,000 records.
We must run analytical jobs on this scale using Spark, applying optimization techniques:
1. Custom Spark Configuration (tuning memory, parallelism).
2. Explicit DDL Schema definition to avoid double-read inferSchema overhead.
3. Caching/Persisting intermediate dataframes.
4. Window Functions to rank departments within countries.
5. Scaled Write operations (partitioning on write to parallelize disk IO).

Usage:
    # 1. Generate 5 Million records (Warning: This will create a ~350MB CSV file in data/)
    python data_generator.py --records 5000000 --output data/employees_large.csv
    
    # 2. Run the optimized Spark analytics
    python assessment_solution.py
"""

import os
import sys
import time

try:
    from pyspark.sql import SparkSession
    from pyspark.sql.functions import col, avg, when, count, rank, desc, round as spark_round
    from pyspark.sql.window import Window
    from pyspark.sql.types import StructType, StructField, IntegerType, StringType, DoubleType
except ImportError:
    print("Error: PySpark is not installed. Run: pip install pyspark")
    sys.exit(1)


def main():
    print("=" * 70)
    print("       RetailMax Large-Scale Analytics: 5 Million Employee Records")
    print("=" * 70)
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    input_path = os.path.join(script_dir, "data", "employees_large.csv")
    output_dir = os.path.normpath(os.path.join(script_dir, "output", "store_analytics_report"))
    
    # Check if the large file exists. If not, ask the user to generate it, or
    # fallback to a smaller dataset (e.g. 500k records) and generate it to avoid crash.
    if not os.path.exists(input_path):
        print(f"[Warning] Large dataset not found at: {input_path}")
        print("To run the full 5 Million records assessment, generate the data first:")
        print("  python data_generator.py --records 5000000 --output data/employees_large.csv")
        print("\nFalling back to generating a 250,000 records dataset for demonstration...")
        sys.path.append(script_dir)
        import data_generator
        data_generator.generate_dataset(input_path, num_records=250000)
    
    print(f"\n[Step 1] Initializing Tuned SparkSession...")
    # TUNE SPARK SESSION CONFIGURATIONS:
    # - driver.memory: Allocates 4GB memory to JVM driver to handle aggregation metadata.
    # - sql.shuffle.partitions: Controls partition counts during wide-dependency shuffles.
    #   Default is 200, which creates too many tiny tasks on a local machine. Tuning it
    #   to 16-32 improves execution speed significantly on a single laptop.
    spark = SparkSession.builder \
        .appName("RetailMax-Large-Scale-Analytics") \
        .master("local[*]") \
        .config("spark.driver.memory", "4g") \
        .config("spark.sql.shuffle.partitions", "16") \
        .getOrCreate()
        
    print(f"SparkSession running with custom configurations.")
    
    # ---------------------------------------------------------
    # 2. EXPLICIT SCHEMA DEFINITION
    # ---------------------------------------------------------
    # In enterprise data engineering, NEVER use inferSchema=True for files larger than a few MBs.
    # InferSchema scans the entire file once to find columns types, then scans again to load.
    # Explicit schema definition eliminates the first scan completely.
    print("\n[Step 2] Defining schema explicitly and reading data...")
    schema = StructType([
        StructField("EmployeeID", IntegerType(), True),
        StructField("Name", StringType(), True),
        StructField("Department", StringType(), True),
        StructField("Salary", DoubleType(), True),
        StructField("Age", IntegerType(), True),
        StructField("Gender", StringType(), True),
        StructField("Country", StringType(), True),
        StructField("StoreID", IntegerType(), True),
        StructField("HireDate", StringType(), True),
        StructField("IsActive", StringType(), True)
    ])
    
    t0 = time.time()
    raw_df = spark.read.schema(schema).csv(input_path, header=True)
    
    # ---------------------------------------------------------
    # 3. FILTERING & CACHING/PERSISTING
    # ---------------------------------------------------------
    # We filter for active records early and cache the dataframe since it will be
    # reused in multiple downsteam calculations (Store Analytics and Window Functions).
    print("\n[Step 3] Filtering active workforce and caching DataFrame...")
    active_employees_df = raw_df.filter(col("IsActive") == "Yes").cache()
    
    # Force evaluation using a count action to populate the Spark memory cache
    cached_count = active_employees_df.count()
    t_load = time.time() - t0
    print(f"Loaded and Cached {cached_count:,} active employee records in {t_load:.2f} seconds.")

    # ---------------------------------------------------------
    # 4. STORE PERFORMANCE & PAYROLL ANALYTICS
    # ---------------------------------------------------------
    print("\n[Step 4] Running Store Payroll & Staffing Analytics...")
    t0 = time.time()
    store_analytics = active_employees_df.groupBy("StoreID").agg(
        count("EmployeeID").alias("Staff_Count"),
        spark_round(avg("Salary"), 2).alias("Average_Salary"),
        spark_round(spark_max("Salary"), 2).alias("Max_Salary")
    ).orderBy(desc("Staff_Count"))
    
    # Display top 5 stores
    store_analytics.show(5)
    print(f"Store analytics completed in {time.time() - t0:.2f} seconds.")

    # ---------------------------------------------------------
    # 5. WINDOW FUNCTION: DEPT RANKINGS PER COUNTRY
    # ---------------------------------------------------------
    # Window functions let us perform calculations across a set of table rows that are
    # related to the current row. Here we rank departments by average salary inside EACH country.
    print("\n[Step 5] Computing Department Rankings by Country using Window Functions...")
    t0 = time.time()
    
    # 5.1 Group by Country and Department to get average salary
    dept_country_avg = active_employees_df.groupBy("Country", "Department").agg(
        avg("Salary").alias("avg_salary")
    )
    
    # 5.2 Define the Window spec: Partition by Country, Sort by Average Salary descending
    country_window = Window.partitionBy("Country").orderBy(desc("avg_salary"))
    
    # 5.3 Apply window and calculate dense rank
    ranked_depts = dept_country_avg.withColumn("Rank", rank().over(country_window))
    
    # 5.4 Filter for the top 1 department (Rank 1) in each country
    top_dept_per_country = ranked_depts.filter(col("Rank") == 1) \
                                      .select("Country", "Department", spark_round("avg_salary", 2).alias("Highest_Avg_Salary")) \
                                      .orderBy("Country")
                                      
    top_dept_per_country.show(10, truncate=False)
    print(f"Window ranking completed in {time.time() - t0:.2f} seconds.")

    # ---------------------------------------------------------
    # 6. SCALED PARTITIONED WRITING
    # ---------------------------------------------------------
    # Writing big datasets back to disk should be parallelized.
    # By partitionBy("Country"), Spark creates separate subdirectories for each country.
    # Future query engines (like Athena or Spark SQL) can read a specific country
    # without scanning other countries (Partition Pruning).
    print(f"\n[Step 6] Writing Store Analytics out to partitioned directory: {output_dir}")
    t0 = time.time()
    
    # We will write store_analytics partitioned by Country
    # Wait, store_analytics doesn't have Country! Let's join back or write the full active employees dataframe partitioned.
    # Let's write the active_employees_df partitioned by Country.
    active_employees_df.write.mode("overwrite") \
                       .partitionBy("Country") \
                       .parquet(output_dir)
                       
    print(f"Successfully wrote partitioned Parquet dataset in {time.time() - t0:.2f} seconds.")
    print("Partitioned structure created: check folders under 'output/store_analytics_report/'")

    # ---------------------------------------------------------
    # 7. CLEANUP
    # ---------------------------------------------------------
    print("\n[Step 7] Stopping SparkSession and releasing memory...")
    active_employees_df.unpersist() # explicitly clear memory cache
    spark.stop()
    print("Large-scale assessment completed successfully.")
    print("=" * 70)


if __name__ == "__main__":
    main()
