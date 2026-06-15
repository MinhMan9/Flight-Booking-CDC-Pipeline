import pyodbc
import random
import string
import uuid
import time
import os
import unicodedata
from dotenv import load_dotenv
from datetime import datetime, timedelta
from faker import Faker

# Load biến môi trường từ file .env
load_dotenv()

# Khởi tạo Faker tiếng Việt
fake = Faker('vi_VN')

# ==========================================
# 1. CẤU HÌNH KẾT NỐI SQL SERVER
# ==========================================
SERVER = 'localhost,1433' # Hoặc tên container nếu chạy trong docker-network
DATABASE = 'FlightBookingCDC'
USERNAME = 'sa'
PASSWORD = os.getenv('DB_PASSWORD') # Đọc mật khẩu từ file .env

# Chuỗi kết nối (Dùng ODBC Driver 17 hoặc 18 tùy máy)
conn_str = f'DRIVER={{ODBC Driver 18 for SQL Server}};SERVER={SERVER};DATABASE={DATABASE};UID={USERNAME};PWD={PASSWORD};TrustServerCertificate=yes'

# ==========================================
# 2. KHAI BÁO MIỀN DỮ LIỆU (DOMAIN VALUES)
# ==========================================
CHANNELS = ['WEB', 'APP', 'AGENCY', 'TICKET_OFFICE', 'CALL_CENTER']
AIRPORTS = ['SGN', 'HAN', 'DAD', 'CXR', 'PQC', 'VCA', 'HUI', 'VDO']
AIRLINES = ['VN', 'VJ', 'QH', 'VU']
PAYMENT_METHODS = ['CREDIT_CARD', 'ATM_CARD', 'E_WALLET', 'CASH']

generated_pnrs = set()

def generate_pnr():
    while True:
        pnr = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        if pnr not in generated_pnrs:
            generated_pnrs.add(pnr)
            return pnr

# ==========================================
# 3. HÀM CHẠY LOGIC SINH DỮ LIỆU CHÍNH
# ==========================================
def simulate_booking_transaction(cursor, count):
    # Thời gian giả lập
    created_at = fake.date_time_between(start_date='-30d', end_date='now')
    updated_at = created_at + timedelta(minutes=random.randint(5, 120))
    flight_date = (created_at + timedelta(days=random.randint(3, 90))).strftime('%Y-%m-%d')
    
    # 1. TẠO PNR
    pnr_id = generate_pnr()
    channel = random.choices(CHANNELS, weights=[40, 30, 20, 5, 5], k=1)[0]
    
    cursor.execute("""
        INSERT INTO pnr_records (pnr_id, booking_channel, booking_status, created_at, updated_at)
        VALUES (?, ?, 'CREATED', ?, ?)
    """, (pnr_id, channel, created_at, updated_at))

    # 2. GHI NHẬN SỰ KIỆN: CREATED
    cursor.execute("""
        INSERT INTO booking_events (pnr_id, event_type, created_at)
        VALUES (?, 'CREATED', ?)
    """, (pnr_id, created_at))

    # 3. TẠO HÀNH KHÁCH (1 đến 3 người)
    num_passengers = random.randint(1, 3)
    passenger_ids = []
    
    for _ in range(num_passengers):
        # Dùng gender ngẫu nhiên để lấy đúng tên tiếng việt
        gender = random.choice(['male', 'female'])
        fname = fake.first_name_male() if gender == 'male' else fake.first_name_female()
        lname = fake.last_name()
        
        # Xóa dấu tiếng Việt và tạo email từ tên
        clean_fname = unicodedata.normalize('NFKD', fname).encode('ASCII', 'ignore').decode('utf-8').lower().replace(' ', '')
        clean_lname = unicodedata.normalize('NFKD', lname).encode('ASCII', 'ignore').decode('utf-8').lower().replace(' ', '')
        
        # Đa dạng hóa các kiểu đặt tên email của người dùng thật
        email_formats = [
            f"{clean_fname}.{clean_lname}{random.randint(1, 999)}",
            f"{clean_lname}{clean_fname}{random.randint(1, 99)}",
            f"{clean_fname}_{random.randint(1970, 2005)}", # giống kiểu đặt năm sinh
            f"{clean_fname}{clean_lname[0]}{random.randint(10, 99)}" 
        ]
        email = f"{random.choice(email_formats)}@{fake.free_email_domain()}"
        
        passport = fake.bothify(text=random.choice(['C#######', '############']))
        
        # Dùng OUTPUT INSERTED để lấy ID tự tăng vừa được tạo
        cursor.execute("""
            INSERT INTO passengers (pnr_id, first_name, last_name, email, passport_number, created_at, updated_at)
            OUTPUT INSERTED.passenger_id
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (pnr_id, fname, lname, email, passport, created_at, updated_at))
        
        passenger_id = cursor.fetchone()[0]
        passenger_ids.append(passenger_id)

    # 4. TẠO CHẶNG BAY (1 chiều hoặc Khứ hồi)
    num_segments = random.choices([1, 2], weights=[70, 30], k=1)[0]
    route = random.sample(AIRPORTS, 2)
    airline = random.choice(AIRLINES)
    
    # Chiều đi
    cursor.execute("""
        INSERT INTO flight_segments (pnr_id, origin_airport, dest_airport, flight_date, airline_code, flight_number, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (pnr_id, route[0], route[1], flight_date, airline, str(random.randint(10, 9999)), created_at, updated_at))
    
    if num_segments == 2: # Chiều về
        return_date = (datetime.strptime(flight_date, '%Y-%m-%d') + timedelta(days=random.randint(2, 10))).strftime('%Y-%m-%d')
        cursor.execute("""
            INSERT INTO flight_segments (pnr_id, origin_airport, dest_airport, flight_date, airline_code, flight_number, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (pnr_id, route[1], route[0], return_date, airline, str(random.randint(10, 9999)), created_at, updated_at))

    # 5. LOGIC THANH TOÁN & XUẤT VÉ (80% thanh toán thành công)
    is_ticketed = random.random() < 0.8
    if is_ticketed:
        # Cập nhật trạng thái PNR thành TICKETED
        cursor.execute("UPDATE pnr_records SET booking_status = 'TICKETED', updated_at = ? WHERE pnr_id = ?", (updated_at, pnr_id))
        
        # Thêm sự kiện TICKETED
        cursor.execute("INSERT INTO booking_events (pnr_id, event_type, created_at) VALUES (?, 'TICKETED', ?)", (pnr_id, updated_at))
        
        # Tạo thanh toán
        payment_id = str(uuid.uuid4())
        pay_method = random.choice(PAYMENT_METHODS)
        fare_class = random.choices(['Y', 'W', 'J', 'F'], weights=[60, 20, 15, 5], k=1)[0]
        
        # Logic tính giá tiền base trên Fare Class đúng với báo cáo
        if fare_class == 'Y':
            base_amount = random.uniform(1500000, 5000000)
        elif fare_class == 'W':
            base_amount = random.uniform(5000000, 10000000)
        elif fare_class == 'J':
            base_amount = random.uniform(11800000, 20000000)
        else: # F
            base_amount = random.uniform(30000000, 50000000)
            
        total_amount = round(base_amount * num_passengers * num_segments, 2)
        
        cursor.execute("""
            INSERT INTO payments (payment_id, pnr_id, payment_method, amount, currency, payment_status, created_at, updated_at)
            VALUES (?, ?, ?, ?, 'VND', 'SUCCESS', ?, ?)
        """, (payment_id, pnr_id, pay_method, total_amount, updated_at, updated_at))

        # Phát hành vé cho từng khách
        for pid in passenger_ids:
            ticket_no = fake.numerify('738##########')
            cursor.execute("""
                INSERT INTO tickets (ticket_number, passenger_id, fare_class, ticket_status, created_at, updated_at)
                VALUES (?, ?, ?, 'ISSUED', ?, ?)
            """, (ticket_no, pid, fare_class, updated_at, updated_at))
            
    print(f"[{count}/100000] Đã sinh thành công PNR: {pnr_id} - Khách: {num_passengers} - Chặng: {num_segments} - Trạng thái: {'TICKETED' if is_ticketed else 'CREATED'}")

# ==========================================
# 4. CHẠY VÒNG LẶP LIÊN TỤC (CDC TRIGGER)
# ==========================================
if __name__ == "__main__":
    print("🚀 Khởi động luồng sinh dữ liệu Flight Booking CDC...")
    try:
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        
        total_records = 100000
        count = 0
        
        # Vòng lặp sinh 100,000 records
        while count < total_records:
            count += 1
            simulate_booking_transaction(cursor, count)
            conn.commit() # Lưu vào database
            
        print(f"Đã sinh thành công đầy đủ {total_records} records!")
            
    except Exception as e:
        print(f"❌ Lỗi: {e}")
    finally:
        if 'conn' in locals():
            conn.close()