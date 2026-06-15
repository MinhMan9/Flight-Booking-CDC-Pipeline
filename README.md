# Flight-Booking-CDC-Pipeline
[Intern] CDC Pipeline Project

## Cấu trúc thư mục
```
flight-booking-cdc-pipeline/
│
├── docker-compose.yml          # File khởi tạo toàn bộ hạ tầng (Kafka, MinIO, SQL Server)
├── .env                        # Chứa các biến môi trường bảo mật (Mật khẩu DB, SecretKey của MinIO)
├── requirements.txt            # Danh sách thư viện Python cần cài đặt (faker, pyodbc,...)
├── README.md                   # Tài liệu hướng dẫn cách chạy dự án
│
├── db/                        # Thư mục chứa toàn bộ script Database
│   └── schemas/
│       ├── init_schema.sql     # Thiết lập cấu trúc cơ sở dữ liệu ban đầu
│       ├── drop_schema.sql     # Xóa toàn bộ các bảng trong database
│       └── reset_schema.sql    # Reset sạch dữ liệu các bảng và đặt lại ID tự tăng về 0
│
├── datagen_app/                # Thư mục chứa App Python sinh dữ liệu giả
│   ├── generate_data.py        # File main chạy vòng lặp Faker để sinh dữ liệu
│   └── db_connection.py        # (Tùy chọn) File chuyên xử lý kết nối đến SQL Server
│
└── connectors/                 # Thư mục chứa cấu hình của Kafka Connect
    ├── debezium-source.json    # File JSON cấu hình Debezium đọc từ SQL Server
    └── minio-sink.json         # File JSON cấu hình đẩy dữ liệu từ Kafka xuống Data Lake (MinIO)
```

## Hướng Dẫn Khởi Tạo Và Sinh Dữ Liệu

Dưới đây là các bước chi tiết để thiết lập môi trường, chuẩn bị cơ sở dữ liệu và thực hiện chạy script sinh 100,000 bản ghi dữ liệu mô phỏng giao dịch đặt vé máy bay.

### 1. Chuẩn bị Môi trường Python
Trước tiên, hãy tạo và kích hoạt môi trường ảo (virtual environment), sau đó cài đặt các thư viện cần thiết.

```bash
# Tạo môi trường ảo venv (nếu chưa tạo)
python3 -m venv venv

# Kích hoạt môi trường ảo (trên macOS/Linux)
source venv/bin/activate

# Cài đặt các thư viện phụ thuộc
pip install -r requirements.txt
```

### 2. Thiết lập cấu hình kết nối (.env)
Đảm bảo bạn đã cấu hình tệp `.env` ở thư mục gốc của dự án chứa mật khẩu SQL Server phù hợp:
```env
DB_PASSWORD=Mật_Khẩu_SQL_Server_Của_Bạn
```

### 3. Thiết lập Cơ sở dữ liệu (SQL Server)
Nếu bạn cần khởi tạo mới hoặc cập nhật lại cấu trúc bảng:

1. **Xóa cấu trúc bảng cũ (nếu có):**
   Thực thi tệp SQL [drop_schema.sql] trên SQL Server của bạn. Lệnh này sẽ xóa các bảng theo đúng thứ tự để không bị ràng buộc bởi Khóa ngoại (Foreign Key).
   
2. **Tạo lại cấu trúc bảng mới:**
   Thực thi tệp SQL [init_schema.sql]. Lệnh này sẽ tạo lại database `FlightBookingCDC` cùng các bảng liên quan.

*(Lưu ý: Nếu chỉ muốn dọn sạch dữ liệu trong bảng mà không muốn xóa cấu trúc bảng cũ, bạn có thể thực thi tệp [reset_schema.sql]).*

### 4. Chạy Script sinh dữ liệu giả lập (Data Generator)
Chạy script Python để bắt đầu tự động sinh 100,000 bản ghi giao dịch đặt vé máy bay vào database:

```bash
python3 datagen_app/generate_data.py
```

* **Cơ chế hoạt động:** Script sẽ tự động sinh ngẫu nhiên các PNR, thông tin khách hàng (1-3 khách mỗi giao dịch), chặng bay (1 chiều hoặc khứ hồi), thực hiện cập nhật thanh toán thành công (80%) hoặc giữ ở trạng thái mới đặt (20%).