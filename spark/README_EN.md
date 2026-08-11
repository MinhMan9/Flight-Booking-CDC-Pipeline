# PySpark (Spark) Execution Guide

This directory manages all supporting `.jar` driver files and Python data processing scripts for Spark in the pipeline.

## 📁 Directory Structure

```text
spark/
├── jars/                                    # Physical JAR driver folder
│   ├── hadoop-aws-3.3.4.jar                # Driver to support S3A MinIO read/write
│   ├── aws-java-sdk-bundle-1.12.262.jar    # SDK to connect to HTTP MinIO
│   └── mssql-jdbc-12.4.2.jre11.jar         # JDBC Driver to connect to SQL Server
└── scripts/                                 # Python Scripts folder
    ├── minio_loader.py                     # Loads raw data from MinIO to Bronze Iceberg
    ├── bronze_to_silver_transformer.py     # Cleans & Upserts data from Bronze to Silver
    ├── silver_to_gold_transformer.py       # Aggregates and loads data from Silver to Gold
    └── data_reconciliation.py              # Validates & Reconciles system-wide data
```

---

## Running Scripts via Docker Compose

Open your Terminal at the project root directory and run the following `spark-submit` commands:

### 1. Load Raw Data from MinIO to Bronze (`minio_loader.py`)
Reads raw Parquet files from MinIO and appends them to corresponding Iceberg Bronze tables.

* **Run with default date (current date):**
  ```bash
  docker compose exec spark-iceberg /opt/spark/bin/spark-submit \
    --jars /home/iceberg/pyspark/jars/hadoop-aws-3.3.4.jar,/home/iceberg/pyspark/jars/aws-java-sdk-bundle-1.12.262.jar \
    /home/iceberg/pyspark/scripts/minio_loader.py
  ```

* **Run for a specific date (e.g., `2026-07-21`):**
  ```bash
  docker compose exec spark-iceberg /opt/spark/bin/spark-submit \
    --jars /home/iceberg/pyspark/jars/hadoop-aws-3.3.4.jar,/home/iceberg/pyspark/jars/aws-java-sdk-bundle-1.12.262.jar \
    /home/iceberg/pyspark/scripts/minio_loader.py --date 2026-07-21
  ```

---

### 2. Clean and Merge Data from Bronze to Silver (`bronze_to_silver_transformer.py`)
Reads data from Bronze, de-duplicates, and performs MERGE INTO (upsert) on corresponding Silver tables.

* **Synchronize all 6 tables sequentially:**
  ```bash
  docker compose exec spark-iceberg /opt/spark/bin/spark-submit \
    /home/iceberg/pyspark/scripts/bronze_to_silver_transformer.py
  ```

* **Synchronize a single specific table (e.g., `pnr_records`):**
  ```bash
  docker compose exec spark-iceberg /opt/spark/bin/spark-submit \
    /home/iceberg/pyspark/scripts/bronze_to_silver_transformer.py pnr_records
  ```
  *(Available tables: `pnr_records`, `passengers`, `flight_segments`, `tickets`, `payments`, `booking_events`)*

---

### 3. Aggregate Data from Silver to Gold (`silver_to_gold_transformer.py`)
Aggregates and calculates business metrics (revenue, cancellation rate, etc.) from the Silver layer, and inserts/overwrites them into the Gold layer for BI (Superset) consumption.

* **Calculate and load Gold tables:**
  ```bash
  docker compose exec spark-iceberg /opt/spark/bin/spark-submit \
    /home/iceberg/pyspark/scripts/silver_to_gold_transformer.py
  ```

---

### 4. Data Reconciliation (`data_reconciliation.py`)
Reconciles record counts, business states, and primary key uniqueness between the source SQL Server and target Silver Iceberg tables.

* **Run full reconciliation checks:**
  ```bash
  docker compose exec spark-iceberg /opt/spark/bin/spark-submit \
    --jars /home/iceberg/pyspark/jars/mssql-jdbc-12.4.2.jre11.jar,/home/iceberg/pyspark/jars/hadoop-aws-3.3.4.jar,/home/iceberg/pyspark/jars/aws-java-sdk-bundle-1.12.262.jar \
    /home/iceberg/pyspark/scripts/data_reconciliation.py
  ```

* **Run event reconciliation for a specific date:**
  ```bash
  docker compose exec spark-iceberg /opt/spark/bin/spark-submit \
    --jars /home/iceberg/pyspark/jars/mssql-jdbc-12.4.2.jre11.jar,/home/iceberg/pyspark/jars/hadoop-aws-3.3.4.jar,/home/iceberg/pyspark/jars/aws-java-sdk-bundle-1.12.262.jar \
    /home/iceberg/pyspark/scripts/data_reconciliation.py --events-date --date 2026-07-21
  ```
