import sys
from pyspark.sql import SparkSession

def create_spark_session():
    """Khởi tạo Spark Session với cấu hình nạp từ spark-defaults.conf inside Docker container."""
    builder = SparkSession.builder.appName("FlightBooking_Bronze_to_Silver")
    
    spark = builder.getOrCreate()
    spark.sparkContext.setLogLevel("WARN")
    return spark




def process_pnr_records(spark):
    print("🔄 Đang xử lý bảng: pnr_records")
    # Lấy event mới nhất cho mỗi pnr_id từ Bronze (đã là TIMESTAMP)
    spark.sql("""
    CREATE OR REPLACE TEMPORARY VIEW pnr_records_normalized AS
    SELECT 
        pnr_id,
        booking_channel,
        booking_status,
        created_at,
        updated_at,
        __op,
        __source_ts_ms
    FROM (
        SELECT *,
               ROW_NUMBER() OVER (PARTITION BY pnr_id ORDER BY __source_ts_ms DESC) as rn
        FROM demo.bronze.pnr_records
    ) WHERE rn = 1
    """)

    # Merge dữ liệu đã chuẩn hóa vào bảng Silver
    spark.sql("""
    MERGE INTO demo.silver.pnr_records_clean t
    USING pnr_records_normalized s
    ON t.pnr_id = s.pnr_id
    WHEN MATCHED AND s.__op = 'd' THEN DELETE
    WHEN MATCHED AND s.__op != 'd' THEN UPDATE SET 
        t.booking_channel = s.booking_channel,
        t.booking_status = s.booking_status,
        t.created_at = s.created_at,
        t.updated_at = s.updated_at
    WHEN NOT MATCHED AND s.__op != 'd' THEN INSERT (pnr_id, booking_channel, booking_status, created_at, updated_at)
    VALUES (s.pnr_id, s.booking_channel, s.booking_status, s.created_at, s.updated_at)
    """)
    print("\033[92m✅ Đồng bộ pnr_records thành công!\033[0m")

def process_passengers(spark):
    print("🔄 Đang xử lý bảng: passengers")
    spark.sql("""
    CREATE OR REPLACE TEMPORARY VIEW passengers_normalized AS
    SELECT 
        passenger_id,
        pnr_id,
        first_name,
        last_name,
        email,
        passport_number,
        created_at,
        updated_at,
        __op,
        __source_ts_ms
    FROM (
        SELECT *,
               ROW_NUMBER() OVER (PARTITION BY passenger_id ORDER BY __source_ts_ms DESC) as rn
        FROM demo.bronze.passengers
    ) WHERE rn = 1
    """)

    spark.sql("""
    MERGE INTO demo.silver.passengers_clean t
    USING passengers_normalized s
    ON t.passenger_id = s.passenger_id
    WHEN MATCHED AND s.__op = 'd' THEN DELETE
    WHEN MATCHED AND s.__op != 'd' THEN UPDATE SET 
        t.pnr_id = s.pnr_id,
        t.first_name = s.first_name,
        t.last_name = s.last_name,
        t.email = s.email,
        t.passport_number = s.passport_number,
        t.created_at = s.created_at,
        t.updated_at = s.updated_at
    WHEN NOT MATCHED AND s.__op != 'd' THEN INSERT (passenger_id, pnr_id, first_name, last_name, email, passport_number, created_at, updated_at)
    VALUES (s.passenger_id, s.pnr_id, s.first_name, s.last_name, s.email, s.passport_number, s.created_at, s.updated_at)
    """)
    print("\033[92m✅ Đồng bộ passengers thành công!\033[0m")

def process_flight_segments(spark):
    print("🔄 Đang xử lý bảng: flight_segments")
    # flight_date đã là DATE, created_at/updated_at đã là TIMESTAMP
    # THÊM ORDER BY flight_date để tối ưu hóa bộ nhớ khi ghi vào bảng partitioned
    spark.sql("""
    CREATE OR REPLACE TEMPORARY VIEW flight_segments_normalized AS
    SELECT 
        segment_id,
        pnr_id,
        origin_airport,
        dest_airport,
        flight_date, 
        airline_code,
        flight_number,
        created_at,
        updated_at,
        __op,
        __source_ts_ms
    FROM (
        SELECT *,
               ROW_NUMBER() OVER (PARTITION BY segment_id ORDER BY __source_ts_ms DESC) as rn
        FROM demo.bronze.flight_segments
    ) WHERE rn = 1
    ORDER BY flight_date
    """)

    spark.sql("""
    MERGE INTO demo.silver.flight_segments_clean t
    USING flight_segments_normalized s
    ON t.segment_id = s.segment_id
    WHEN MATCHED AND s.__op = 'd' THEN DELETE
    WHEN MATCHED AND s.__op != 'd' THEN UPDATE SET 
        t.pnr_id = s.pnr_id,
        t.origin_airport = s.origin_airport,
        t.dest_airport = s.dest_airport,
        t.flight_date = s.flight_date,
        t.airline_code = s.airline_code,
        t.flight_number = s.flight_number,
        t.created_at = s.created_at,
        t.updated_at = s.updated_at
    WHEN NOT MATCHED AND s.__op != 'd' THEN INSERT (segment_id, pnr_id, origin_airport, dest_airport, flight_date, airline_code, flight_number, created_at, updated_at)
    VALUES (s.segment_id, s.pnr_id, s.origin_airport, s.dest_airport, s.flight_date, s.airline_code, s.flight_number, s.created_at, s.updated_at)
    """)
    print("\033[92m✅ Đồng bộ flight_segments thành công!\033[0m")

def process_tickets(spark):
    print("🔄 Đang xử lý bảng: tickets")
    spark.sql("""
    CREATE OR REPLACE TEMPORARY VIEW tickets_normalized AS
    SELECT 
        ticket_number,
        passenger_id,
        fare_class,
        ticket_status,
        created_at,
        updated_at,
        __op,
        __source_ts_ms
    FROM (
        SELECT *,
               ROW_NUMBER() OVER (PARTITION BY ticket_number ORDER BY __source_ts_ms DESC) as rn
        FROM demo.bronze.tickets
    ) WHERE rn = 1
    """)

    spark.sql("""
    MERGE INTO demo.silver.tickets_clean t
    USING tickets_normalized s
    ON t.ticket_number = s.ticket_number
    WHEN MATCHED AND s.__op = 'd' THEN DELETE
    WHEN MATCHED AND s.__op != 'd' THEN UPDATE SET 
        t.passenger_id = s.passenger_id,
        t.fare_class = s.fare_class,
        t.ticket_status = s.ticket_status,
        t.created_at = s.created_at,
        t.updated_at = s.updated_at
    WHEN NOT MATCHED AND s.__op != 'd' THEN INSERT (ticket_number, passenger_id, fare_class, ticket_status, created_at, updated_at)
    VALUES (s.ticket_number, s.passenger_id, s.fare_class, s.ticket_status, s.created_at, s.updated_at)
    """)
    print("\033[92m✅ Đồng bộ tickets thành công!\033[0m")

def process_payments(spark):
    print("🔄 Đang xử lý bảng: payments")
    spark.sql("""
    CREATE OR REPLACE TEMPORARY VIEW payments_normalized AS
    SELECT 
        payment_id,
        pnr_id,
        payment_method,
        amount,
        currency,
        payment_status,
        created_at,
        updated_at,
        __op,
        __source_ts_ms
    FROM (
        SELECT *,
               ROW_NUMBER() OVER (PARTITION BY payment_id ORDER BY __source_ts_ms DESC) as rn
        FROM demo.bronze.payments
    ) WHERE rn = 1
    """)

    spark.sql("""
    MERGE INTO demo.silver.payments_clean t
    USING payments_normalized s
    ON t.payment_id = s.payment_id
    WHEN MATCHED AND s.__op = 'd' THEN DELETE
    WHEN MATCHED AND s.__op != 'd' THEN UPDATE SET 
        t.pnr_id = s.pnr_id,
        t.payment_method = s.payment_method,
        t.amount = s.amount,
        t.currency = s.currency,
        t.payment_status = s.payment_status,
        t.created_at = s.created_at,
        t.updated_at = s.updated_at
    WHEN NOT MATCHED AND s.__op != 'd' THEN INSERT (payment_id, pnr_id, payment_method, amount, currency, payment_status, created_at, updated_at)
    VALUES (s.payment_id, s.pnr_id, s.payment_method, s.amount, s.currency, s.payment_status, s.created_at, s.updated_at)
    """)
    print("\033[92m✅ Đồng bộ payments thành công!\033[0m")

def process_booking_events(spark):
    print("🔄 Đang xử lý bảng: booking_events")
    spark.sql("""
    CREATE OR REPLACE TEMPORARY VIEW booking_events_normalized AS
    SELECT 
        event_id,
        pnr_id,
        event_type,
        created_at,
        __op,
        __source_ts_ms
    FROM (
        SELECT *,
               ROW_NUMBER() OVER (PARTITION BY event_id ORDER BY __source_ts_ms DESC) as rn
        FROM demo.bronze.booking_events
    ) WHERE rn = 1
    """)

    spark.sql("""
    MERGE INTO demo.silver.booking_events_clean t
    USING booking_events_normalized s
    ON t.event_id = s.event_id
    WHEN MATCHED AND s.__op = 'd' THEN DELETE
    WHEN MATCHED AND s.__op != 'd' THEN UPDATE SET 
        t.pnr_id = s.pnr_id,
        t.event_type = s.event_type,
        t.created_at = s.created_at
    WHEN NOT MATCHED AND s.__op != 'd' THEN INSERT (event_id, pnr_id, event_type, created_at)
    VALUES (s.event_id, s.pnr_id, s.event_type, s.created_at)
    """)
    print("\033[92m✅ Đồng bộ booking_events thành công!\033[0m")

def main():
    spark = create_spark_session()



    # Cấu hình tối ưu bộ nhớ: Giảm shuffle partitions từ 200 mặc định xuống 10
    spark.conf.set("spark.sql.shuffle.partitions", "10")
    spark.conf.set("spark.sql.adaptive.coalescePartitions.enabled", "true")

    # Bản đồ hàm xử lý
    handlers = {
        "pnr_records": process_pnr_records,
        "passengers": process_passengers,
        "flight_segments": process_flight_segments,
        "tickets": process_tickets,
        "payments": process_payments,
        "booking_events": process_booking_events
    }

    # Đọc tham số dòng lệnh để xác định bảng cần chạy
    target_table = sys.argv[1] if len(sys.argv) > 1 else None

    if target_table:
        if target_table in handlers:
            print(f"🚀 Chạy đồng bộ cho riêng bảng: {target_table}")
            try:
                handlers[target_table](spark)
            except Exception as e:
                print(f"\033[91m❌ Thất bại khi đồng bộ {target_table}: {str(e)}\033[0m")
                sys.exit(1)
        else:
            print(f"\033[91m❌ Tham số bảng '{target_table}' không hợp lệ. Chọn một trong: {list(handlers.keys())}\033[0m")
            sys.exit(1)
    else:
        print("🚀 Chạy đồng bộ tuần tự cho toàn bộ 6 bảng...")
        for name, handler in handlers.items():
            try:
                handler(spark)
            except Exception as e:
                print(f"\033[91m❌ Thất bại khi đồng bộ {name}: {str(e)}\033[0m")
                # Tiếp tục chạy bảng tiếp theo bất kể lỗi
                continue

    print("\n\033[92m🏁 Hoàn tất đồng bộ tầng Silver!\033[0m")

if __name__ == "__main__":
    main()
