# Flight-Booking-CDC-Pipeline
[Intern] CDC Pipeline Project


# Cấu trúc thư mục
flight-booking-cdc-pipeline/
│
├── docker-compose.yml          # File khởi tạo toàn bộ hạ tầng (Kafka, MinIO, SQL Server)
├── .env                        # Chứa các biến môi trường bảo mật (Mật khẩu DB, SecretKey của MinIO)
├── requirements.txt            # Danh sách thư viện Python cần cài đặt (faker, pyodbc,...)
├── README.md                   # Tài liệu hướng dẫn cách chạy dự án
│
├── db/                        # Thư mục chứa toàn bộ script Database
│   └── init_schema.sql         # <--- File chứa schema
│
├── datagen_app/                # Thư mục chứa App Python sinh dữ liệu giả
│   ├── generate_data.py        # File main chạy vòng lặp Faker
│   └── db_connection.py        # (Tùy chọn) File chuyên xử lý kết nối đến SQL Server
│
└── connectors/                 # Thư mục chứa cấu hình của Kafka Connect
    ├── debezium-source.json    # File JSON cấu hình Debezium đọc từ SQL Server
    └── minio-sink.json         # File JSON cấu hình đẩy dữ liệu từ Kafka xuống Data Lake (MinIO)