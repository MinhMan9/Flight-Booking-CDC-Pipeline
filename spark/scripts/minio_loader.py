import os
import argparse
from datetime import datetime
from pyspark.sql import SparkSession

def create_spark_session(run_date):
    """Khởi tạo Spark Session với cấu hình nạp từ spark-defaults.conf inside Docker container."""
    builder = SparkSession.builder.appName(f"FlightBooking_Minio_Loader_{run_date}")
    
    # Cấu hình Iceberg được nạp tự động qua spark-defaults.conf của Spark trong Docker
    spark = builder.getOrCreate()
    spark.sparkContext.setLogLevel("WARN")
    return spark


def main():

    
    # Cấu hình để có thể truyền tham số ngày từ dòng lệnh (mặc định là ngày hiện tại)
    parser = argparse.ArgumentParser(description="MinIO to Bronze Loader")
    parser.add_argument(
        "--date", 
        type=str, 
        help="Ngày cần nạp dữ liệu (Định dạng: YYYY-MM-DD)", 
        default=datetime.now().strftime("%Y-%m-%d")
    )
    args = parser.parse_args()
    
    run_date = args.date

    # Khởi tạo Spark Session
    spark = create_spark_session(run_date)

    print(f"Bắt đầu tiến trình nạp dữ liệu MinIO to Iceberg Bronze cho ngày: {run_date}")

    tables = ["pnr_records", "passengers", "flight_segments", "tickets", "payments", "booking_events"]


    for table in tables:
        # Cập nhật đường dẫn chỉ đọc thư mục của đúng event_date được yêu cầu
        topic_path = f"s3a://datalake/topics/FlightBookingCDC.dbo.{table}/event_date={run_date}/"
        bronze_table = f"demo.bronze.{table}"
        
        print(f"\nĐang đọc dữ liệu từ đường dẫn: {topic_path}")
        try:
            # Đọc dữ liệu thô dạng parquet từ topic
            raw_df = spark.read.parquet(topic_path)
            
            # Ghi nối tiếp (mode append) vào bảng Bronze Iceberg tương ứng
            raw_df.write.format("iceberg").mode("append").saveAsTable(bronze_table)
            print(f"\033[92m✅ Đã ghi dữ liệu thành công vào bảng Bronze Iceberg: {bronze_table}\033[0m")
            
        except Exception as e:
            # Nếu trong ngày không có dữ liệu, Spark sẽ quăng lỗi Path does not exist
            print(f"\033[91m❌ Không thể nạp dữ liệu bảng {table} cho ngày {run_date}. Chi tiết lỗi: {str(e)[:100]}...\033[0m")

    print("\n\033[92m✅ Hoàn thành tiến trình nạp dữ liệu từ MinIO vào tầng Bronze!\033[0m")


if __name__ == "__main__":
    main()