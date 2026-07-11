# Week 2 – Day 1: RetailMax Cloud Data Engineering Sprint 1

## Theme
**RetailMax Cloud Data Engineering Sprint 1**

## Topic
**From Local Data Processing to Distributed Data Engineering (Apache Spark)**

---

## 🎯 Learning Objectives

By the end of today's session, participants will:
- Understand why Big Data technologies emerged and why single-node tools hit physical limits.
- Differentiate between a **Data Warehouse**, **Data Lake**, and **Lakehouse**.
- Explain the **Modern Data Stack (MDS)** architecture.
- Describe core distributed computing concepts (Driver, Executors, Workers, Parallel Processing).
- Install and configure PySpark in a Python environment.
- Initialize a `SparkSession` and write basic PySpark programs.
- Detail the core differences between Pandas and PySpark.
- Ingest and process enterprise-scale datasets using PySpark.

---

## 📖 The Business Story: RetailMax Global Expansion

### 🎙️ Trainer Script
> **Trainer:** "Good Morning Everyone."
>
> *(Pause for response)*
>
> **Trainer:** "Last week, we successfully engineered the **RetailMax Enterprise Data Platform**. We build database tables, created ETL pipelines, parsed JSON APIs, calculated metrics using Pandas, and generated clean Excel sheets. The application is running perfectly. The employees are happy. HR is happy. The CEO is ecstatic.
>
> *(Pause)*
>
> **Trainer:** "But this morning... the CTO called. And we received this urgent company-wide email."

---

### 📧 Email from the CTO
```text
Subject: RetailMax Expansion & Technical Scalability Bottlenecks

Dear Data Engineering Team,

Congratulations on successfully completing Phase 1 of the RetailMax Enterprise Platform. 
Our local data systems are running smoothly.

However, due to rapid business growth, the Board has finalized the acquisition of several 
international retail chains. RetailMax has officially expanded to:
  - 2,000 Stores
  - 45 Countries
  - 30 Million Customers
  - 12 Billion Transactions annually

Our current Python application is no longer able to process this volume of data within 
acceptable SLA times. Attempts to run our aggregation reports result in out-of-memory (OOM) 
crashes.

The Board has approved a migration to a Cloud Data Engineering Platform. Your primary responsibility 
this week is to design and implement the next-generation, distributed data platform for RetailMax.

Regards,
CTO, RetailMax
```

---

### ❓ Interactive Discussion Q&A
- **Trainer:** "Can our local SQLite database store and query 12 billion transactions?"
  - **Students:** *No (it will lock, hit file size bottlenecks, and queries will time out).*
- **Trainer:** "Can Pandas load a 5 Terabyte dataset into a laptop's memory?"
  - **Students:** *No (Pandas is in-memory only; it will run out of memory and crash instantly).*
- **Trainer:** "Can a single standard laptop CPU process billions of transactions?"
  - **Students:** *No (it would take days or weeks of single-threaded compute).*
- **Trainer:** "So what do enterprise companies use to solve this?"
  - **Students:** *Apache Spark, Hadoop, Cloud Storage, Compute Clusters.*
- **Trainer:** "Exactly. Welcome to Distributed Data Engineering."

---

## 🏛️ Conceptual Modules

### Module 1: Why Big Data?
Historically, data fit on local tools:
```text
2010 (Small Data Era)
  Excel ➔ CSV ➔ Relational Database (SQLite/Postgres) ➔ Pandas
```
These tools worked because files were small and fit comfortably inside a single computer's RAM.

Today, enterprise operations look like this:
```text
2026 (Big Data Era)
  Petabytes ➔ Real-time Streaming ➔ Cloud Object Stores ➔ Distributed Compute ➔ Spark
```
Enterprise giants like Walmart, Amazon, and Netflix cannot run on Excel. They rely on distributed architectures where computation is split across hundreds or thousands of nodes.

---

### Module 2: Evolution of Data Engineering
Storage and processing technologies evolved in distinct phases to handle this volume:
```text
Excel ➔ CSV ➔ Relational Databases ➔ Data Warehouses ➔ Data Lakes ➔ Lakehouses
```
- **Excel/CSV:** Simple, readable, but lacks validation, scaling, and concurrency.
- **Relational DB:** Structured storage, SQL, ACID transactions, but limited to a single machine's scale.
- **Data Warehouse:** Centralized repository for structured analytical queries.
- **Data Lake:** Scalable, cheap repository for storing raw structured, semi-structured, and unstructured data.
- **Lakehouse:** Modern design combining the low-cost storage of Data Lakes with the ACID transactions and governance of Data Warehouses.

---

### Module 3: Data Warehouse
A Data Warehouse is optimized for reading, aggregating, and analyzing large volumes of structured data.
```text
ERP Systems
CRM Systems   ➔   Data Warehouse (Schema-on-Write)   ➔   BI Reports / Dashboards
Finance DBs
```
* **Core Characteristics:**
  - **Structured Data Only:** Data must match a rigid schema before being loaded.
  - **Schema-on-Write:** Schema validation happens during the ingestion phase.
  - **Examples:** Snowflake, Google BigQuery, Amazon Redshift.
* **Limitation:** Cannot store unstructured data like video files, audio logs, or raw PDF receipts.

---

### Module 4: Data Lake
A Data Lake is a vast pool of raw data, stored in its native format until needed.
```text
CSV/JSON Files
PDF Invoices   ➔   Data Lake (Schema-on-Read)   ➔   Data Science / Raw Queries
Images/Audio
```
* **Core Characteristics:**
  - **Any Data Type:** Stores structured, semi-structured, and unstructured data.
  - **Schema-on-Read:** Schemas are applied dynamically only when the data is read.
  - **Examples:** Amazon S3, Azure Data Lake Storage (ADLS), Google Cloud Storage.
* **Limitation:** Hard to run fast business intelligence (BI) queries directly; lack of transactions can lead to corrupt data.

---

### Module 5: Lakehouse
A Lakehouse implements ACID transactions, data quality controls, and indexing directly on top of cheap cloud object storage (Data Lake).
```text
  Data Lake Storage (S3 / GCS)
+ ACID Transaction Metadata
---------------------------------
= Lakehouse (Delta Lake / Iceberg)
```
* **Core Characteristics:**
  - ACID transactions (prevents dirty reads/incomplete writes).
  - Schema enforcement and schema evolution.
  - Time Travel (querying previous states of the dataset).
  - **Examples:** Delta Lake, Apache Iceberg, Apache Hudi.

---

### Module 6: Modern Data Stack (MDS)
The Modern Data Stack represents the set of cloud-native tools companies use to ingest, transform, store, and visualize data:
```text
Source Systems ➔ Kafka (Ingest) ➔ Cloud Storage (Lake) ➔ Spark / Delta (Process) ➔ dbt (Transform) ➔ Power BI (Viz)
```
1. **Source:** Where the data is generated (POS machines, websites, CRM).
2. **Kafka:** Event streaming backbone that captures data in real-time.
3. **Data Lake:** Cheap raw storage.
4. **Spark / Delta:** Distributed processing engine to clean and structure raw data.
5. **dbt (data build tool):** Transforms clean data into business-ready tables using SQL.
6. **Power BI / Looker:** Displays dashboards to business users.

---

### Module 7: Distributed Computing Fundamentals
If you need to count 100 Crore (1 billion) records, a single computer will struggle. 
```text
Single Laptop:
  [ 1 CPU / RAM ] ➔ Processes records sequentially (Bottleneck).

Spark Cluster:
  [ Driver Node ] ➔ Coordinates tasks and partitions
         ↓
  [ Executor 1 ] [ Executor 2 ] [ Executor 3 ] ➔ Parallel processing (Fast).
```
- **Driver Node:** The master process. It maintains the application state, plans execution, and divides the work into tasks.
- **Workers/Executors:** Worker processes running on cluster nodes. They execute the tasks allocated by the driver and store cache data.
- **Parallel Processing:** Breaking a large file into partitions and having multiple CPU threads process separate partitions simultaneously.

---

## 🛠️ Getting Started with PySpark

### 1. Installation
Participants can install PySpark locally via pip:
```bash
pip install pyspark
```

### 2. Initialization: The SparkSession
To run Spark, we must initialize a `SparkSession` (the connection to the Spark cluster):
```python
from pyspark.sql import SparkSession

# Initialize Spark Session
spark = SparkSession.builder \
    .appName("RetailMax-Spark-App") \
    .master("local[*]") \
    .getOrCreate()
```

### 3. Basic DataFrame Ingestion
Instead of Pandas, we load data using the Spark reader:
```python
df = spark.read.csv(
    "data/employees.csv", 
    header=True, 
    inferSchema=True
)
```

---

## 📁 Code Repository Artifacts & Guides

We have prepared 5 fully annotated scripts in this directory to guide you through the transition:

1. **[data_generator.py](file:///C:/Users/Himanshu%20Sardana/.gemini/antigravity-ide/scratch/RetailMax/week2/day1_spark/data_generator.py)**
   - Use this script to generate datasets of any size.
   - Run `python data_generator.py -n 10000` to create a sample file for basic tutorials.
   - Run `python data_generator.py -n 5000000 -o data/employees_large.csv` to create the 5 million row dataset for the scaling assessment.

2. **[spark_basics.py](file:///C:/Users/Himanshu%20Sardana/.gemini/antigravity-ide/scratch/RetailMax/week2/day1_spark/spark_basics.py)**
   - Step-by-step introduction to starting sessions, checking schemas, running actions (`show`, `count`), and basic transformations (`filter`, `select`, `groupBy`).

3. **[pandas_vs_pyspark.py](file:///C:/Users/Himanshu%20Sardana/.gemini/antigravity-ide/scratch/RetailMax/week2/day1_spark/pandas_vs_pyspark.py)**
   - Side-by-side benchmarking. Demonstrates why Pandas crashes on large volumes while Spark scales by spilling data to disk when memory limit is exceeded.

4. **[hands_on_lab.py](file:///C:/Users/Himanshu%20Sardana/.gemini/antigravity-ide/scratch/RetailMax/week2/day1_spark/hands_on_lab.py)**
   - Solutions for the Day 1 Hands-on Lab department analytics exercise. Outputs results to a polished Markdown dashboard.

5. **[assessment_solution.py](file:///C:/Users/Himanshu%20Sardana/.gemini/antigravity-ide/scratch/RetailMax/week2/day1_spark/assessment_solution.py)**
   - Advanced solutions illustrating caching, explicit schema declarations, window functions, and partitioned parallel data writes (Parquet format) on a dataset of millions of records.

---

## 🚀 Hands-On Lab: RetailMax Global Analytics

### Challenge Description
Our HR and Executive leadership need a high-performance department analysis tool. Using PySpark, compute the following metrics from the employee dataset:
1. Total Employee headcount.
2. Company-wide Average Salary.
3. Company-wide Highest Salary.
4. Count of employees in each department, ordered descending.
5. Top 10 highest-earning employees in the company.

### How to Run the Solution
```bash
python hands_on_lab.py
```
This generates raw outputs in `reports/` and a styled executive dashboard in `reports/department_analytics_dashboard.md`.

---

## 📝 Assessment: 300 Store Acquisition Ingestion (5M Records)

### Challenge Scenario
RetailMax has acquired 300 stores. You are provided with a raw 5,000,000 row CSV. You must aggregate:
1. Payroll statistics (Headcount, average salary, max salary) per Store ID.
2. The highest-paying department within each Country using Window partitioning.
3. Write the output to a distributed parquet directory partitioned by Country.

### Performance Tuning Requirements
- Configure Spark with `spark.driver.memory = 4g`.
- Configure Spark shuffle partitions to `16`.
- Define the schema explicitly using `StructType` to eliminate the double-read overhead.
- Cache the dataset to prevent redundant computations.

### How to Run the Solution
```bash
# 1. Generate the 5M records file
python data_generator.py -n 5000000 -o data/employees_large.csv

# 2. Run the tuned Spark assessment script
python assessment_solution.py
```

---

## 🏁 End of Day & Look Ahead
Congratulations! Today, you migrated **RetailMax** from a single-machine local processor to a distributed, parallelized analytics engine. 

**Looking Ahead:**
Tomorrow, our data volumes increase again. Our global stores will begin emitting millions of real-time transactional events every second from:
- Point-of-Sale (POS) registers
- Mobile Shopping apps
- Website clickstreams
- Warehouse IoT scanners

*Trainer:* "Can CSV files or batch PySpark sessions handle real-time streaming?"
*Students:* "No."
*Trainer:* *(Smile)* "Tomorrow, we'll build **Real-Time Data Pipelines** using **Apache Kafka**."

---

## 💡 Trainer Tips
- Emphasize that Spark is not "just another library" like Pandas. Keep connecting it back to the business story:
  - *"Yesterday, SQLite/Pandas worked because our dataset fit inside standard RAM. Today, our business has expanded globally. The business problem scaled, so our technology stack had to evolve."*
- Highlight Spark's **Lazy Evaluation** concept repeatedly. Use the analogy of a chef: building a recipe (DAG) vs cooking the meal (Triggering Action).
- Show the visual directory structure after running `assessment_solution.py` to explain how Spark partitioning writes data. Explain why there are multiple `.parquet` files and a `_SUCCESS` file.
