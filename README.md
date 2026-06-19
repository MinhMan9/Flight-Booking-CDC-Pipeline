# Flight-Booking-CDC-Pipeline
[Intern] CDC Pipeline Project

## Cấu trúc thư mục
```
flight-booking-cdc-pipeline/
│
├── docker-compose.yml          # File khởi tạo toàn bộ hạ tầng (Kafka, SQL Server, Kafka UI)
├── .env                        # Chứa các biến môi trường bảo mật (Mật khẩu DB, Kafka Cluster ID)
├── requirements.txt            # Danh sách thư viện Python cần cài đặt (faker, pyodbc,...)
├── README.md                   # Tài liệu hướng dẫn cách chạy dự án
│
├── db/                        # Thư mục chứa toàn bộ script Database
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
└── connectors/                 # Thư mục chứa cấu hình của Kafka Connect
    ├── debezium-source.json    # File JSON cấu hình Debezium đọc từ SQL Server
    └── minio-sink.json         # File JSON cấu hình đẩy dữ liệu từ Kafka xuống Data Lake (MinIO)
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
Đảm bảo bạn đã cấu hình tệp `.env` ở thư mục gốc của dự án chứa mật khẩu SQL Server phù hợp, có ví dụ trong file `.env.example`:


### 3. Chạy hạ tầng bằng Docker
Khởi động toàn bộ các service hạ tầng (SQL Server, Kafka, Kafka UI) bằng Docker Compose:

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