import random
import string
import unicodedata
from datetime import datetime, timedelta

CHANNELS = ['WEB', 'APP', 'AGENCY', 'TICKET_OFFICE', 'CALL_CENTER']
AIRPORTS = ['SGN', 'HAN', 'DAD', 'CXR', 'PQC', 'VCA', 'HUI', 'VDO']
AIRLINES = ['VN', 'VJ', 'QH', 'VU']

# Mã màu ANSI
CREATE_COLOR = "\033[42;37m"
UPDATE_COLOR = "\033[43;30m"
DELETE_COLOR = "\033[41;37m"
RESET_COLOR = "\033[0m"

def generate_unique_pnr(cursor):
    """
    Tạo pnr_id ngẫu nhiên 6 ký tự và kiểm tra trùng lặp trong cơ sở dữ liệu.
    """
    while True:
        pnr = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        cursor.execute("SELECT COUNT(*) FROM pnr_records WHERE pnr_id = ?", (pnr,))
        if cursor.fetchone()[0] == 0:
            return pnr

def run(cursor, fake):
    """
    Thực hiện logic tạo pnr, passenger, flight_segment, booking event.
    """
    # Thời gian giả lập
    created_at = fake.date_time_between(start_date='-30d', end_date='now')
    updated_at = created_at + timedelta(minutes=random.randint(5, 120))
    flight_date = (created_at + timedelta(days=random.randint(3, 90))).strftime('%Y-%m-%d')
    
    # 1. TẠO PNR
    pnr_id = generate_unique_pnr(cursor)
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
            f"{clean_fname}_{random.randint(1970, 2005)}",
            f"{clean_fname}{clean_lname[0]}{random.randint(10, 99)}" 
        ]
        email = f"{random.choice(email_formats)}@{fake.free_email_domain()}"
        
        passport = fake.bothify(text=random.choice(['C#######', '############']))
        
        cursor.execute("""
            INSERT INTO passengers (pnr_id, first_name, last_name, email, passport_number, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (pnr_id, fname, lname, email, passport, created_at, updated_at))

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

    print(f"{CREATE_COLOR} BOOKING {RESET_COLOR} Đã tạo thành công PNR: {pnr_id} - Khách: {num_passengers} - Chặng: {num_segments} - Trạng thái: CREATED")
    return pnr_id
