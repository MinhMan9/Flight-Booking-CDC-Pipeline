# Hướng dẫn chạy các tiến trình PySpark (Spark)

Thư mục này quản lý toàn bộ các file `.jar` hỗ trợ và các Python script xử lý dữ liệu của Spark trong pipeline.

## 📁 Cấu trúc thư mục

```text
spark/
├── jars/                                    # Thư mục lưu các file JAR driver vật lý
│   ├── hadoop-aws-3.3.4.jar                # Driver hỗ trợ đọc/ghi S3A MinIO
│   ├── aws-java-sdk-bundle-1.12.262.jar    # SDK kết nối HTTP MinIO
│   └── mssql-jdbc-12.4.2.jre11.jar         # JDBC Driver kết nối SQL Server
└── scripts/                                 # Thư mục chứa các Python Scripts
    ├── minio_loader.py                     # Nạp dữ liệu thô từ MinIO vào Bronze Iceberg
    ├── bronze_to_silver_transformer.py     # Chuẩn hóa & Upsert dữ liệu từ Bronze lên Silver
    ├── silver_to_gold_transformer.py       # Tổng hợp và nạp dữ liệu từ Silver lên Gold
    └── data_reconciliation.py              # Kiểm tra & Đối chiếu dữ liệu toàn hệ thống
```

---

## Hướng dẫn chạy các Scripts qua Docker Compose

Bạn mở Terminal tại thư mục gốc của dự án và chạy các lệnh `spark-submit` dưới đây:

### 1. Nạp dữ liệu từ MinIO vào tầng Bronze (`minio_loader.py`)
Tiến trình đọc các file Parquet thô từ MinIO và append vào bảng Iceberg tầng Bronze.

* **Chạy mặc định (ngày hiện tại):**
  ```bash
  docker compose exec spark-iceberg /opt/spark/bin/spark-submit \
    --jars /home/iceberg/pyspark/jars/hadoop-aws-3.3.4.jar,/home/iceberg/pyspark/jars/aws-java-sdk-bundle-1.12.262.jar \
    /home/iceberg/pyspark/scripts/minio_loader.py
  ```

* **Chạy cho một ngày cụ thể (ví dụ: `2026-07-21`):**
  ```bash
  docker compose exec spark-iceberg /opt/spark/bin/spark-submit \
    --jars /home/iceberg/pyspark/jars/hadoop-aws-3.3.4.jar,/home/iceberg/pyspark/jars/aws-java-sdk-bundle-1.12.262.jar \
    /home/iceberg/pyspark/scripts/minio_loader.py --date 2026-07-21
  ```

---

### 2. Chuẩn hóa dữ liệu từ tầng Bronze lên Silver (`bronze_to_silver_transformer.py`)
Tiến trình đọc từ Bronze, deduplicate và MERGE INTO vào các bảng Silver tương ứng.

* **Chạy tuần tự toàn bộ 6 bảng:**
  ```bash
  docker compose exec spark-iceberg /opt/spark/bin/spark-submit \
    /home/iceberg/pyspark/scripts/bronze_to_silver_transformer.py
  ```

* **Chạy riêng biệt từng bảng (Ví dụ: `pnr_records`):**
  ```bash
  docker compose exec spark-iceberg /opt/spark/bin/spark-submit \
    /home/iceberg/pyspark/scripts/bronze_to_silver_transformer.py pnr_records
  ```
  *(Các bảng khả dụng: `pnr_records`, `passengers`, `flight_segments`, `tickets`, `payments`, `booking_events`)*

---

### 3. Tổng hợp dữ liệu từ tầng Silver lên Gold (`silver_to_gold_transformer.py`)
Tiến trình tổng hợp, tính toán các metrics kinh doanh (doanh thu, tỉ lệ hủy vé,...) từ tầng Silver và ghi đè vào tầng Gold để phục vụ BI (Superset).

* **Chạy tính toán và nạp các bảng Gold:**
  ```bash
  docker compose exec spark-iceberg /opt/spark/bin/spark-submit \
    /home/iceberg/pyspark/scripts/silver_to_gold_transformer.py
  ```

---

### 4. Đối chiếu dữ liệu (`data_reconciliation.py`)
Tiến trình đối chiếu số lượng, trạng thái nghiệp vụ và tính duy nhất của dữ liệu giữa SQL Server Source và Silver Iceberg.

* **Chạy kiểm tra toàn bộ:**
  ```bash
  docker compose exec spark-iceberg /opt/spark/bin/spark-submit \
    --jars /home/iceberg/pyspark/jars/mssql-jdbc-12.4.2.jre11.jar,/home/iceberg/pyspark/jars/hadoop-aws-3.3.4.jar,/home/iceberg/pyspark/jars/aws-java-sdk-bundle-1.12.262.jar \
    /home/iceberg/pyspark/scripts/data_reconciliation.py
  ```

* **Chạy kiểm tra sự kiện theo ngày cụ thể:**
  ```bash
  docker compose exec spark-iceberg /opt/spark/bin/spark-submit \
    --jars /home/iceberg/pyspark/jars/mssql-jdbc-12.4.2.jre11.jar,/home/iceberg/pyspark/jars/hadoop-aws-3.3.4.jar,/home/iceberg/pyspark/jars/aws-java-sdk-bundle-1.12.262.jar \
    /home/iceberg/pyspark/scripts/data_reconciliation.py --events-date --date 2026-07-21
  ```