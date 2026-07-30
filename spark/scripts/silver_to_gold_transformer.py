import sys
from pyspark.sql import SparkSession

def create_spark_session():
    """Khởi tạo Spark Session với cấu hình mặc định nạp từ spark-defaults.conf inside Docker container."""
    builder = SparkSession.builder.appName("FlightBooking_Silver_to_Gold")
    spark = builder.getOrCreate()
    spark.sparkContext.setLogLevel("WARN")
    return spark

def init_gold_tables(spark):
    """Khởi tạo cấu trúc các bảng tầng Gold (DDL) nếu chưa tồn tại."""
    print("🔄 Đang khởi tạo DDL các bảng tầng Gold...")
    
    # 1. Bảng daily_booking_summary
    spark.sql("""
    CREATE TABLE IF NOT EXISTS demo.gold.daily_booking_summary (
        booking_date DATE,
        booking_channel STRING,
        total_bookings BIGINT
    ) USING iceberg
    PARTITIONED BY (booking_date)
    """)
    
    # 2. Bảng daily_cancellation_rate
    spark.sql("""
    CREATE TABLE IF NOT EXISTS demo.gold.daily_cancellation_rate (
        booking_date DATE,
        total_bookings BIGINT,
        cancelled_bookings BIGINT,
        cancellation_rate DOUBLE
    ) USING iceberg
    PARTITIONED BY (booking_date)
    """)
    
    # 3. Bảng revenue_by_route
    spark.sql("""
    CREATE TABLE IF NOT EXISTS demo.gold.revenue_by_route (
        flight_date DATE,
        origin_airport STRING,
        dest_airport STRING,
        total_revenue DECIMAL(16,2),
        total_bookings BIGINT
    ) USING iceberg
    PARTITIONED BY (flight_date)
    """)
    
    # 4. Bảng payment_status_summary
    spark.sql("""
    CREATE TABLE IF NOT EXISTS demo.gold.payment_status_summary (
        payment_date DATE,
        payment_method STRING,
        payment_status STRING,
        payment_count BIGINT,
        total_amount DECIMAL(16,2)
    ) USING iceberg
    PARTITIONED BY (payment_date)
    """)
    
    print("\033[92m✅ Khởi tạo DDL các bảng tầng Gold hoàn tất!\033[0m")

def process_daily_booking_summary(spark):
    print("🔄 Đang tính toán: daily_booking_summary")
    try:
        spark.sql("""
        INSERT OVERWRITE demo.gold.daily_booking_summary
        SELECT 
            CAST(created_at AS DATE) as booking_date,
            booking_channel,
            COUNT(*) as total_bookings
        FROM demo.silver.pnr_records_clean
        GROUP BY CAST(created_at AS DATE), booking_channel
        """)
        print("\033[92m✅ Tính toán daily_booking_summary thành công!\033[0m")
    except Exception as e:
        print(f"\033[91m❌ Lỗi khi tính toán daily_booking_summary: {e}\033[0m")

def process_daily_cancellation_rate(spark):
    print("🔄 Đang tính toán: daily_cancellation_rate")
    try:
        spark.sql("""
        INSERT OVERWRITE demo.gold.daily_cancellation_rate
        SELECT 
            CAST(created_at AS DATE) as booking_date,
            COUNT(*) as total_bookings,
            SUM(CASE WHEN booking_status = 'CANCELLED' THEN 1 ELSE 0 END) as cancelled_bookings,
            CAST(SUM(CASE WHEN booking_status = 'CANCELLED' THEN 1 ELSE 0 END) AS DOUBLE) / COUNT(*) as cancellation_rate
        FROM demo.silver.pnr_records_clean
        GROUP BY CAST(created_at AS DATE)
        """)
        print("\033[92m✅ Tính toán daily_cancellation_rate thành công!\033[0m")
    except Exception as e:
        print(f"\033[91m❌ Lỗi khi tính toán daily_cancellation_rate: {e}\033[0m")

def process_revenue_by_route(spark):
    print("🔄 Đang tính toán: revenue_by_route")
    try:
        spark.sql("""
        INSERT OVERWRITE demo.gold.revenue_by_route
        WITH segment_counts AS (
            SELECT pnr_id, COUNT(*) as segment_count
            FROM demo.silver.flight_segments_clean
            GROUP BY pnr_id
        ),
        pnr_payments AS (
            SELECT 
                pnr_id,
                SUM(amount) as total_amount
            FROM demo.silver.payments_clean
            WHERE payment_status = 'SUCCESS'
            GROUP BY pnr_id
        ),
        allocated_revenue AS (
            SELECT 
                s.flight_date,
                s.origin_airport,
                s.dest_airport,
                (COALESCE(p.total_amount, 0) / sc.segment_count) as allocated_amount,
                s.pnr_id
            FROM demo.silver.flight_segments_clean s
            JOIN segment_counts sc ON s.pnr_id = sc.pnr_id
            JOIN pnr_payments p ON s.pnr_id = p.pnr_id
        )
        SELECT 
            flight_date,
            origin_airport,
            dest_airport,
            CAST(SUM(allocated_amount) AS DECIMAL(16,2)) as total_revenue,
            COUNT(DISTINCT pnr_id) as total_bookings
        FROM allocated_revenue
        GROUP BY flight_date, origin_airport, dest_airport
        """)
        print("\033[92m✅ Tính toán revenue_by_route thành công!\033[0m")
    except Exception as e:
        print(f"\033[91m❌ Lỗi khi tính toán revenue_by_route: {e}\033[0m")

def process_payment_status_summary(spark):
    print("🔄 Đang tính toán: payment_status_summary")
    try:
        spark.sql("""
        INSERT OVERWRITE demo.gold.payment_status_summary
        SELECT 
            CAST(created_at AS DATE) as payment_date,
            payment_method,
            payment_status,
            COUNT(*) as payment_count,
            CAST(SUM(amount) AS DECIMAL(16,2)) as total_amount
        FROM demo.silver.payments_clean
        GROUP BY CAST(created_at AS DATE), payment_method, payment_status
        """)
        print("\033[92m✅ Tính toán payment_status_summary thành công!\033[0m")
    except Exception as e:
        print(f"\033[91m❌ Lỗi khi tính toán payment_status_summary: {e}\033[0m")

def main():
    spark = create_spark_session()
    
    # 1. Khởi tạo cấu trúc các bảng Gold
    init_gold_tables(spark)
    
    # 2. Xử lý và nạp dữ liệu cho từng bảng
    process_daily_booking_summary(spark)
    process_daily_cancellation_rate(spark)
    process_revenue_by_route(spark)
    process_payment_status_summary(spark)
    
    spark.stop()
    print("\033[92m Đã hoàn thành toàn bộ tiến trình xử lý Gold Layer (Silver -> Gold)!\033[0m")

if __name__ == "__main__":
    main()
