# Flight-Booking-CDC-Pipeline
[Intern] CDC Pipeline Project

![Pipeline Architecture](images/architecture.png)


## Cấu trúc thư mục
```
flight-booking-cdc-pipeline/
│
├── docker-compose.yml          # File khởi tạo toàn bộ hạ tầng (Kafka, SQL Server, Kafka UI, MinIO, Spark, Iceberg REST,...)
├── .env.example                # Hướng dẫn các biến môi trường cấu hình hệ thống
├── requirements.txt            # Danh sách thư viện Python cần cài đặt (faker, pyodbc,...)
├── README.md                   # Tài liệu hướng dẫn cách chạy dự án
├── README_EN.md                # Tài liệu hướng dẫn cách chạy dự án (Tiếng Anh)
├── download_jars.sh            # Script bash tải các file jar phục vụ Spark
│
├── db/                         # Thư mục chứa toàn bộ script Database
│   ├── schemas/
│   │   ├── init_schema.sql     # Thiết lập cấu trúc cơ sở dữ liệu ban đầu
│   │   ├── drop_schema.sql     # Xóa toàn bộ các bảng trong database
│   │   └── reset_schema.sql    # Reset sạch dữ liệu các bảng và đặt lại ID tự tăng về 0
│   └── cdc_setup/
│       └── enable_cdc.sql      # Bật CDC (Change Data Capture) cấp độ DB và bảng
│
├── datagen_app/                # Thư mục chứa App Python sinh dữ liệu giả & Trình giả lập PNR
│   ├── generate_data.py        # File sinh dữ liệu mẫu ban đầu (100,000 bản ghi)
│   ├── db_connection.py        # File xử lý kết nối đến SQL Server
│   ├── main_simulator.py       # File chính chạy Trình giả lập giao dịch PNR Simulator
│   └── scenarios/              # Thư mục chứa các kịch bản nghiệp vụ giả lập
│       ├── __init__.py
│       ├── book_new_flight.py  # Kịch bản đặt vé mới (Book New Flight)
│       ├── cancel_booking.py   # Kịch bản hủy đặt vé (Cancel Booking)
│       ├── change_flight.py    # Kịch bản thay đổi chuyến bay (Change Flight)
│       └── make_payment.py     # Kịch bản thanh toán (Make Payment)
│
├── connectors/                 # Thư mục chứa cấu hình của Kafka Connect
│   ├── README.md               # Hướng dẫn kết nối Connector (Tiếng Việt)
│   ├── README_EN.md            # Hướng dẫn kết nối Connector (Tiếng Anh)
│   ├── debezium-source.json    # File JSON cấu hình Debezium đọc từ SQL Server
│   └── minio-sink.json         # File JSON cấu hình đẩy dữ liệu từ Kafka xuống Data Lake (MinIO)
│
├── notebooks/                  # Chứa Jupyter Notebook để khởi tạo môi trường
│   └── create_iceberg_tables.ipynb  # Notebook tạo các bảng Iceberg
│
├── spark/                      # Thư mục quản lý Spark
│   ├── README.md               # Hướng dẫn chạy tiến trình Spark (Tiếng Việt)
│   ├── README_EN.md            # Hướng dẫn chạy tiến trình Spark (Tiếng Anh)
│   ├── jars/                   # Thư mục chứa các driver JAR (MSSQL JDBC, AWS Bundle, Hadoop AWS)
│   └── scripts/                # Thư mục chứa các script xử lý PySpark (minio_loader, bronze_to_silver_transformer,...)
│
├── trino/                      # Thư mục cấu hình Trino phục vụ truy vấn dữ liệu từ Iceberg
│   └── etc/
│       └── catalog/
│           └── iceberg.properties # Cấu hình kết nối Iceberg catalog cho Trino
│
├── superset/                   # Thư mục cấu hình Apache Superset để trực quan hóa dữ liệu (BI)
│   ├── Dockerfile              # Dockerfile tùy chỉnh cho Superset
│   └── superset_home/          # Lưu trữ cấu hình và dashboard của Superset
│
├── monitoring/                 # Thư mục cấu hình giám sát hệ thống (Prometheus, Grafana)
│   ├── prometheus.yml          # File cấu hình Prometheus thu thập metrics
│   ├── debezium-dashboard.json # Grafana Dashboard mẫu cho Debezium
│   ├── kafka-dashboard.json    # Grafana Dashboard mẫu cho Kafka
│   └── grafana/                # Thư mục chứa các file provisioning cho Grafana
│
└── conf/                       # Thư mục cấu hình hệ thống
    └── spark-defaults.conf     # File cấu hình mặc định cho Spark Iceberg
```

## Hướng Dẫn Khởi Tạo Và Sinh Dữ Liệu

Dưới đây là các bước chi tiết để thiết lập môi trường, chuẩn bị cơ sở dữ liệu và thực hiện chạy script sinh 100,000 bản ghi dữ liệu mô phỏng giao dịch đặt vé máy bay.


### 1. Chuẩn bị Môi trường Python (Local)
Trước tiên, hãy tạo và kích hoạt môi trường ảo (virtual environment), sau đó cài đặt các thư viện cần thiết:

```bash
# Tạo môi trường ảo venv (nếu chưa tạo)
python3 -m venv venv

# Kích hoạt môi trường ảo (trên macOS/Linux)
source venv/bin/activate

# Cài đặt các thư viện phụ thuộc
pip install -r requirements.txt
```


### 2. Thiết lập cấu hình kết nối (.env)
Đảm bảo bạn đã cấu hình tệp `.env` ở thư mục gốc của dự án chứa các cấu hình phù hợp, có ví dụ trong file `.env.example`:


### 3. Chạy hạ tầng bằng Docker
Khởi động toàn bộ các dịch vụ hạ tầng bằng Docker Compose:
- **SQL Server (mssql)**: Lưu trữ dữ liệu giao dịch ban đầu.
- **Apache Kafka (kafka)**: Hệ thống hàng đợi tin nhắn thu thập log CDC.
- **Kafka UI (kafka-ui)**: Giao diện trực quan để theo dõi Kafka topic, consumer group.
- **Debezium (debezium)**: Kafka Connect source connector chụp các thay đổi dữ liệu từ SQL Server.
- **MinIO (minio)**: S3 compatible Object Storage làm Data Lake lưu trữ file Parquet.
- **Schema Registry (schema-registry)**: Quản lý và lưu trữ schema định dạng Avro.
- **Iceberg REST Catalog (rest)**: REST Catalog quản lý metadata cho Apache Iceberg.
- **Spark Iceberg (spark-iceberg)**: Môi trường chạy PySpark & Jupyter Notebook để tương tác và ETL dữ liệu.

```bash
# Khởi động các dịch vụ
docker-compose up -d
```


### 4. Thiết lập Cơ sở dữ liệu và CDC trong Docker (SQL Server)
Sau khi SQL Server khởi động thành công, chạy các lệnh sau để khởi tạo cấu trúc bảng và kích hoạt CDC (Change Data Capture) trực tiếp bên trong container:

1. **Khởi tạo Database và bảng:**
   ```bash
   docker exec -i mssql /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P 'yourPasswordHere' -C -d master < db/schemas/init_schema.sql
   ```
   hoặc chạy file init_schema.sql trong IDE.

2. **Kích hoạt CDC (Change Data Capture):**
   ```bash
   docker exec -i mssql /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P 'yourPasswordHere' -C -d master < db/cdc_setup/enable_cdc.sql
   ```
   hoặc chạy file enable_cdc.sql trong IDE.

*(Lưu ý: Nếu chỉ muốn xóa sạch dữ liệu trong các bảng mà không muốn xóa cấu trúc bảng hoặc tắt CDC, bạn có thể chạy tệp `reset_schema.sql`):*
```bash
docker exec -i mssql /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P 'yourPasswordHere' -C -d master < db/schemas/reset_schema.sql
```


### 5. Chạy Script sinh dữ liệu giả lập (Data Generator)
Chạy script Python từ máy local (trong môi trường `venv` đã kích hoạt) để bắt đầu tự động sinh 100,000 bản ghi giao dịch đặt vé máy bay vào database:

```bash
python3 datagen_app/generate_data.py
```
* **Cơ chế hoạt động:** Script sẽ tự động sinh ngẫu nhiên các PNR, thông tin khách hàng (1-3 khách mỗi giao dịch), chặng bay (1 chiều hoặc khứ hồi), thực hiện cập nhật thanh toán thành công (80%) hoặc giữ ở trạng thái mới đặt (20%).


### 6. Chạy Script giả lập giao dịch PNR (PNR Simulator)
Trình giả lập PNR Simulator được sử dụng để mô phỏng các hoạt động thực tế diễn ra liên tục theo thời gian (như đặt vé mới, thanh toán, thay đổi chuyến bay, hủy đặt vé). Trình giả lập hỗ trợ 2 chế độ chạy:

#### Chế độ 1: Chạy ngẫu nhiên liên tục (Mặc định)
Chế độ này sẽ lựa chọn ngẫu nhiên các kịch bản theo trọng số định sẵn (Đặt vé mới: 50%, Thanh toán: 30%, Đổi chuyến bay: 10%, Hủy đặt vé: 10%) và lặp lại liên tục sau mỗi khoảng thời gian nghỉ ngẫu nhiên từ 1 đến 3 giây.
```bash
python3 datagen_app/main_simulator.py
```
*Nhấn `Ctrl+C` để dừng trình giả lập.*

#### Chế độ 2: Chỉ định cụ thể kịch bản và số lần chạy
Chạy một kịch bản cụ thể với số lần lặp mong muốn. Cú pháp:
```bash
python3 datagen_app/main_simulator.py <tên_kịch_bản> <số_lần_chạy>
```

Danh sách các kịch bản hợp lệ (`<tên_kịch_bản>`):
- `book_new_flight`: Mô phỏng đặt vé máy bay mới (tạo PNR ở trạng thái `Created`, hành khách, chặng bay).
- `make_payment`: Tìm ngẫu nhiên các PNR chưa thanh toán và thực hiện thanh toán (chuyển trạng thái sang `Ticketed` hoặc `Cancelled`).
- `change_flight`: Tìm ngẫu nhiên các PNR đã được xuất vé (`Ticketed`) và thay đổi thông tin chặng bay.
- `cancel_booking`: Tìm ngẫu nhiên các PNR hợp lệ và tiến hành hủy đặt vé (chuyển trạng thái sang `Cancelled`).

**Ví dụ:**
* Chạy kịch bản đặt vé mới 5 lần:
  ```bash
  python3 datagen_app/main_simulator.py book_new_flight 5
  ```
* Chạy kịch bản thanh toán 3 lần:
  ```bash
  python3 datagen_app/main_simulator.py make_payment 3
  ```

---

## Hướng Dẫn Vận Hành Hệ Thống

Dưới đây là các bước chi tiết để cấu hình connector, khởi tạo Data Lake và chạy ETL chuyển đổi dữ liệu.

### 1. Đăng ký Source Connector
Đăng ký Debezium Source Connector để bắt đầu lắng nghe sự thay đổi (CDC) từ SQL Server và đẩy vào Kafka. Tham khảo chi tiết tại [connectors/README.md].
```bash
curl -i -X POST -H "Accept:application/json" -H "Content-Type:application/json" localhost:8083/connectors/ -d @connectors/debezium-source.json
```

### 2. Tạo Bucket trên MinIO
- Truy cập vào MinIO Web UI tại địa chỉ: http://localhost:9001.
- Vào phần **Buckets** -> Nhấp vào **Create Bucket** -> Đặt tên bucket là `datalake`

### 3. Đăng ký Sink Connector
Sau khi đã tạo bucket trên MinIO, tiến hành đăng ký MinIO Sink Connector để đẩy dữ liệu từ Kafka xuống Data Lake:
```bash
curl -i -X POST -H "Accept:application/json" -H "Content-Type:application/json" localhost:8083/connectors/ -d @connectors/minio-sink.json
```

### 4. Tạo các bảng Iceberg
- Truy cập Jupyter Notebook tại địa chỉ: http://localhost:8888.
- Tìm đến notebook [notebooks/create_iceberg_tables.ipynb] và chạy toàn bộ các cells để khởi tạo database và các bảng Iceberg.

### 5. Tải Drivers JAR & Đợi đồng bộ dữ liệu
- Chờ cho dữ liệu CDC được đồng bộ hoàn toàn từ Kafka xuống bucket `datalake` dưới dạng file Parquet.
- Cài đặt driver JAR cần thiết cho Spark (nếu chưa chạy trước đó):
  ```bash
  chmod +x download_jars.sh
  ./download_jars.sh
  ```

### 6. Chạy các lệnh nạp dữ liệu vào bảng Iceberg
Dùng Spark-submit để chạy các script ETL trong Spark container (xem thêm trong [spark/README.md]):
- **Nạp dữ liệu từ MinIO vào tầng Bronze:**
  ```bash
  docker compose exec spark-iceberg /opt/spark/bin/spark-submit \
    --jars /home/iceberg/pyspark/jars/hadoop-aws-3.3.4.jar,/home/iceberg/pyspark/jars/aws-java-sdk-bundle-1.12.262.jar \
    /home/iceberg/pyspark/scripts/minio_loader.py
  ```
- **Chuẩn hóa và Merge dữ liệu từ tầng Bronze lên tầng Silver:**
  ```bash
  docker compose exec spark-iceberg /opt/spark/bin/spark-submit \
    /home/iceberg/pyspark/scripts/bronze_to_silver_transformer.py
  ```
- **Tổng hợp và nạp dữ liệu từ tầng Silver lên tầng Gold:**
  ```bash
  docker compose exec spark-iceberg /opt/spark/bin/spark-submit \
    /home/iceberg/pyspark/scripts/silver_to_gold_transformer.py
  ```
- *(Tùy chọn) Đối chiếu dữ liệu giữa SQL Server Source và Silver Iceberg:*
  ```bash
  docker compose exec spark-iceberg /opt/spark/bin/spark-submit \
    --jars /home/iceberg/pyspark/jars/mssql-jdbc-12.4.2.jre11.jar,/home/iceberg/pyspark/jars/hadoop-aws-3.3.4.jar,/home/iceberg/pyspark/jars/aws-java-sdk-bundle-1.12.262.jar \
    /home/iceberg/pyspark/scripts/data_reconciliation.py
  ```

### 7. Truy cập và Dựng BI (Superset) & Giám sát hệ thống (Prometheus/Grafana)

Sau khi khởi chạy Docker Compose, các dịch vụ trực quan hóa dữ liệu (BI) và giám sát hệ thống có thể được truy cập qua các địa chỉ và port sau:

* **Apache Superset (BI Tool):**
  * Địa chỉ: [http://localhost:8088](http://localhost:8088)
  * Tài khoản mặc định: `admin` / `admin`
  * **Hướng dẫn kết nối với Apache Iceberg thông qua Trino:**
    1. Trên giao diện Superset, chọn **Settings** -> **Database Connections** -> **+ Database**.
    2. Chọn database type là **Trino**.
    3. Nhập chuỗi kết nối (Connection URI): `trino://admin@trino:8080/iceberg`
    4. Nhấp **Connect** và lưu lại. Bây giờ bạn có thể truy vấn và xây dựng dashboard từ các bảng dữ liệu Iceberg (Silver, Gold).

* **Prometheus (Thu thập Metrics):**
  * Địa chỉ: [http://localhost:9090](http://localhost:9090)
  * Dùng để kiểm tra trạng thái các target giám sát (Kafka, Debezium,...).

* **Grafana (Trực quan hóa giám sát):**
  * Địa chỉ: [http://localhost:3000](http://localhost:3000)
  * Tài khoản mặc định: `admin` / `admin`
  * Hệ thống đã tích hợp sẵn các dashboard mẫu cho Kafka và Debezium Connect.