import os
import sys
import argparse
from datetime import datetime
import re
from pyspark.sql import SparkSession


class TeeLogger:
    """Ghi xuất dữ liệu đồng thời ra Terminal và ra File báo cáo dạng text."""
    def __init__(self, filepath):
        self.terminal = sys.stdout
        self.log_file = open(filepath, "w", encoding="utf-8")
        # Regex để loại bỏ các mã escape màu ANSI
        self.ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')

    def write(self, message):
        self.terminal.write(message)
        # Loại bỏ mã màu ANSI trước khi ghi vào file báo cáo
        clean_message = self.ansi_escape.sub('', message)
        self.log_file.write(clean_message)

    def flush(self):
        self.terminal.flush()
        self.log_file.flush()

    def close(self):
        self.log_file.close()


def create_spark_session():
    """Khởi tạo Spark Session bên trong Docker container."""
    builder = SparkSession.builder.appName("FlightBooking_Data_Validation")
    
    spark = builder.getOrCreate()
    spark.sparkContext.setLogLevel("WARN")
    return spark




def read_sql_server(spark, table_name):
    """Đọc dữ liệu từ SQL Server, hỗ trợ lấy cấu hình từ environment hoặc .env."""
    db_server = os.getenv("DB_SERVER", "sql-server:1433").strip().replace(",", ":")
    db_name = os.getenv("DB_NAME", "FlightBookingCDC").strip()
    db_username = os.getenv("DB_USERNAME", "sa").strip()
    db_password = os.getenv("DB_PASSWORD", "Password123!").strip()
    
    # Nếu chạy ngoài Docker và host là 'sql-server', tự động chuyển thành 'localhost'
    in_docker = os.path.exists('/.dockerenv')
    if not in_docker:
        if db_server.startswith("sql-server"):
            db_server = db_server.replace("sql-server", "localhost")
            
    jdbc_url = f"jdbc:sqlserver://{db_server};databaseName={db_name};encrypt=false"
    
    return spark.read.format("jdbc") \
        .option("driver", "com.microsoft.sqlserver.jdbc.SQLServerDriver") \
        .option("url", jdbc_url) \
        .option("dbtable", f"dbo.{table_name}") \
        .option("user", db_username) \
        .option("password", db_password) \
        .load()


def load_and_register_views(spark):
    """Nạp dữ liệu từ Source & Target và tạo Temp Views để query SQL cho toàn bộ 6 bảng."""
    print(" BƯỚC 1: Đang nạp dữ liệu từ SQL Server và Iceberg Lakehouse...")
    
    # Danh sách 6 bảng dữ liệu cần đối chiếu
    tables = [
        ("pnr_records", "src_pnr", "slv_pnr", "demo.silver.pnr_records_clean"),
        ("passengers", "src_pas", "slv_pas", "demo.silver.passengers_clean"),
        ("flight_segments", "src_seg", "slv_seg", "demo.silver.flight_segments_clean"),
        ("tickets", "src_tkt", "slv_tkt", "demo.silver.tickets_clean"),
        ("payments", "src_pay", "slv_pay", "demo.silver.payments_clean"),
        ("booking_events", "src_be", "slv_be", "demo.silver.booking_events_clean")
    ]
    
    for tbl_name, src_alias, slv_alias, slv_table_name in tables:
        # Load & Register Source
        src_df = read_sql_server(spark, tbl_name)
        src_df.createOrReplaceTempView(src_alias)
        
        # Load & Register Silver Target
        slv_df = spark.table(slv_table_name)
        slv_df.createOrReplaceTempView(slv_alias)
        
    print("\033[92m✅ Đã load thành công toàn bộ 6 bảng dữ liệu!\033[0m\n")
    return spark.table("src_pnr").count()


def validate_silver_completeness_uniqueness(spark):
    """Đối chiếu số lượng bản ghi và kiểm tra trùng lặp cho toàn bộ 6 bảng."""
    print(" BƯỚC 2: ĐỐI CHIẾU SỐ LƯỢNG & TÍNH DUY NHẤT TẤT CẢ CÁC BẢNG")
    
    # 1. Check số lượng tổng cho 6 bảng
    count_df = spark.sql("""
        SELECT 'pnr_records' as table_name, (SELECT COUNT(*) FROM src_pnr) as source_count, (SELECT COUNT(*) FROM slv_pnr) as silver_count, (SELECT COUNT(*) FROM slv_pnr) - (SELECT COUNT(*) FROM src_pnr) as difference
        UNION ALL
        SELECT 'passengers' as table_name, (SELECT COUNT(*) FROM src_pas) as source_count, (SELECT COUNT(*) FROM slv_pas) as silver_count, (SELECT COUNT(*) FROM slv_pas) - (SELECT COUNT(*) FROM src_pas) as difference
        UNION ALL
        SELECT 'flight_segments' as table_name, (SELECT COUNT(*) FROM src_seg) as source_count, (SELECT COUNT(*) FROM slv_seg) as silver_count, (SELECT COUNT(*) FROM slv_seg) - (SELECT COUNT(*) FROM src_seg) as difference
        UNION ALL
        SELECT 'tickets' as table_name, (SELECT COUNT(*) FROM src_tkt) as source_count, (SELECT COUNT(*) FROM slv_tkt) as silver_count, (SELECT COUNT(*) FROM slv_tkt) - (SELECT COUNT(*) FROM src_tkt) as difference
        UNION ALL
        SELECT 'payments' as table_name, (SELECT COUNT(*) FROM src_pay) as source_count, (SELECT COUNT(*) FROM slv_pay) as silver_count, (SELECT COUNT(*) FROM slv_pay) - (SELECT COUNT(*) FROM src_pay) as difference
        UNION ALL
        SELECT 'booking_events' as table_name, (SELECT COUNT(*) FROM src_be) as source_count, (SELECT COUNT(*) FROM slv_be) as silver_count, (SELECT COUNT(*) FROM slv_be) - (SELECT COUNT(*) FROM src_be) as difference
    """)
    count_df.show()
    
    # 2. Check trùng lặp ID cho toàn bộ 6 bảng
    pk_checks = [
        ("pnr_records", "slv_pnr", "pnr_id"),
        ("passengers", "slv_pas", "passenger_id"),
        ("flight_segments", "slv_seg", "segment_id"),
        ("tickets", "slv_tkt", "ticket_number"),
        ("payments", "slv_pay", "payment_id"),
        ("booking_events", "slv_be", "event_id")
    ]
    
    total_duplicates = 0
    for tbl_name, slv_alias, pk_col in pk_checks:
        dup_df = spark.sql(f"""
            SELECT {pk_col}, COUNT(*) as occurrence
            FROM {slv_alias}
            GROUP BY {pk_col}
            HAVING COUNT(*) > 1
        """)
        dup_count = dup_df.count()
        if dup_count > 0:
            total_duplicates += dup_count
            print(f"\033[91m❌ LỖI: Bảng {tbl_name} có {dup_count} khóa chính ({pk_col}) bị trùng lặp!\033[0m")
            dup_df.show(5)
            
    if total_duplicates == 0:
        print("\033[92m✅ OK: Không có bản ghi nào bị trùng lặp trên cả 6 bảng.\033[0m\n")


def validate_state_consistency(spark):
    """Kiểm tra tính đồng nhất về trạng thái nghiệp vụ giữa Source và Target."""
    print(" BƯỚC 3: ĐỐI CHIẾU TRẠNG THÁI NGHIỆP VỤ PNR VÀ PAYMENT")
    
    # 1. PNR Status
    pnr_mismatch = spark.sql("""
        SELECT s.pnr_id, s.booking_status as src_status, t.booking_status as target_status
        FROM src_pnr s
        JOIN slv_pnr t ON s.pnr_id = t.pnr_id
        WHERE s.booking_status != t.booking_status
    """)
    if pnr_mismatch.count() > 0:
        print(f"\033[91m⚠️ CẢNH BÁO: Phát hiện {pnr_mismatch.count()} vé PNR bị sai lệch trạng thái!\033[0m")
        pnr_mismatch.show(5)
    else:
        print("\033[92m✅ PNR Status: Khớp 100% giữa Source và Target.\033[0m")
        
    # 2. Payment Status
    pay_mismatch = spark.sql("""
        SELECT s.payment_id, s.payment_status as src_pay_status, t.payment_status as target_pay_status
        FROM src_pay s
        JOIN slv_pay t ON s.payment_id = t.payment_id
        WHERE s.payment_status != t.payment_status
    """)
    if pay_mismatch.count() > 0:
        print(f"\033[91m⚠️ CẢNH BÁO: Phát hiện {pay_mismatch.count()} giao dịch thanh toán bị sai lệch!\033[0m")
        pay_mismatch.show(5)
    else:
        print("\033[92m✅ Payment Status: Khớp 100% giữa Source và Target.\033[0m\n")

def validate_events_by_date(spark, target_date):
    """
    Đối chiếu chi tiết booking_events giữa Source và Silver theo từng ngày.
    So sánh tổng số event và phân rã theo từng loại event_type.
    """
    print(f" BƯỚC 4: ĐỐI CHIẾU BOOKING EVENTS THEO NGÀY (NGÀY {target_date})")
    
    # 1. So sánh tổng số event theo ngày
    src_total = spark.sql(f"SELECT COUNT(*) FROM src_be WHERE CAST(created_at AS DATE) = '{target_date}'").collect()[0][0] or 0
    slv_total = spark.sql(f"SELECT COUNT(*) FROM slv_be WHERE CAST(created_at AS DATE) = '{target_date}'").collect()[0][0] or 0
    
    print(f"  [Source] booking_events ngày {target_date}: {src_total} events")
    print(f"  [Silver] booking_events ngày {target_date}: {slv_total} events")
    
    # 2. So sánh chi tiết từng loại event_type
    detail_df = spark.sql(f"""
        SELECT 
            COALESCE(s.event_type, t.event_type) as event_type,
            COALESCE(s.src_cnt, 0) as source_count,
            COALESCE(t.slv_cnt, 0) as silver_count,
            COALESCE(t.slv_cnt, 0) - COALESCE(s.src_cnt, 0) as difference
        FROM (
            SELECT event_type, COUNT(*) as src_cnt
            FROM src_be
            WHERE CAST(created_at AS DATE) = '{target_date}'
            GROUP BY event_type
        ) s
        FULL OUTER JOIN (
            SELECT event_type, COUNT(*) as slv_cnt
            FROM slv_be
            WHERE CAST(created_at AS DATE) = '{target_date}'
            GROUP BY event_type
        ) t ON s.event_type = t.event_type
        ORDER BY event_type
    """)
    detail_df.show()
    
    if src_total == slv_total:
        print(f"  \033[92m✅ OK: Số lượng event giữa Source và Target ngày {target_date} khớp 100%!\033[0m\n")
    else:
        print(f"  \033[91m⚠️ CẢNH BÁO: Lệch {abs(src_total - slv_total)} event giữa Source và Target vào ngày {target_date}!\033[0m\n")

def main():
    parser = argparse.ArgumentParser(description="Đối chiếu chất lượng dữ liệu Flight Booking")
    parser.add_argument("--silver", action="store_true", help="Chạy kiểm định tầng Silver")
    parser.add_argument("--state", action="store_true", help="Chạy đối chiếu trạng thái nghiệp vụ")
    parser.add_argument("--events-date", action="store_true", help="Chạy đối chiếu booking_events theo ngày")
    parser.add_argument(
        "--steps",
        nargs="+",
        choices=["silver", "state", "events_date"],
        help="Danh sách cụ thể các bước kiểm định cần chạy (silver, state, events_date)"
    )
    parser.add_argument(
        "--date",
        type=str,
        default=datetime.now().strftime("%Y-%m-%d"),
        help="Ngày cần kiểm định sự kiện (Định dạng YYYY-MM-DD, mặc định là hôm nay)"
    )
    
    args = parser.parse_args()
    target_date = args.date
    
    # Xác định các bước kiểm định cần chạy
    steps_to_run = set()
    if args.steps:
        steps_to_run.update(args.steps)
    if args.silver:
        steps_to_run.add("silver")
    if args.state:
        steps_to_run.add("state")
    if args.events_date:
        steps_to_run.add("events_date")
        
    # Mặc định chạy tất cả nếu không chỉ định cụ thể bước nào
    if not steps_to_run:
        steps_to_run = {"silver", "state", "events_date"}

    # 1. Tạo thư mục reports nếu chưa tồn tại

    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    reports_dir = os.path.join(project_root, 'reports')
    os.makedirs(reports_dir, exist_ok=True)
    
    # 2. Tạo tên file theo định dạng: report_YYYYMMDD_HHMMSS.txt
    now = datetime.now()
    timestamp_str = now.strftime("%Y%m%d_%H%M%S")
    report_filename = f"report_{timestamp_str}.txt"
    report_filepath = os.path.join(reports_dir, report_filename)
    
    # 3. Kích hoạt TeeLogger
    logger = TeeLogger(report_filepath)
    original_stdout = sys.stdout
    sys.stdout = logger
    report_filepath = "/" + "/".join(report_filepath.split("/")[4:])

    
    spark = None
    try:
        print("=" * 70)
        print("   DATA QUALITY RECONCILIATION REPORT ")
        print(f"   Các bước chạy: {', '.join(sorted(steps_to_run)).upper()}")
        print(f"   Thời gian tạo: {now.strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)
        
        # Khởi tạo Spark Session
        spark = create_spark_session()
        
        total_source_pnr = load_and_register_views(spark)
        
        if "silver" in steps_to_run:
            validate_silver_completeness_uniqueness(spark)

        if "state" in steps_to_run:
            validate_state_consistency(spark)
        if "events_date" in steps_to_run:
            validate_events_by_date(spark, target_date)
            
        print("=" * 70)
        print("\033[92m   HOÀN THÀNH TIẾN TRÌNH KIỂM ĐỊNH DỮ LIỆU!\033[0m")
        print("=" * 70)
         
    except Exception as e:
        print(f"\033[91m❌ Có lỗi xảy ra trong quá trình đối chiếu: {str(e)}\033[0m")
    finally:
        if spark:
            spark.stop()
        sys.stdout = original_stdout
        logger.close()
        print(f"\n--> Báo cáo đối chiếu dữ liệu đã được lưu thành công tại:\n   {report_filepath}\n")


if __name__ == "__main__":
    main()