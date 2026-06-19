import random
from datetime import datetime, timedelta

# Mã màu ANSI
CREATE_COLOR = "\033[42;37m"
UPDATE_COLOR = "\033[43;30m"
DELETE_COLOR = "\033[41;37m"
RESET_COLOR = "\033[0m"

def run(cursor, fake):
    """
    Thực hiện thay đổi chuyến bay: dời ngày bay ngẫu nhiên từ 1 đến 3 ngày.
    """
    # Lấy ngẫu nhiên một PNR chưa bị hủy hoặc hoàn tiền
    cursor.execute("""
        SELECT TOP 1 pnr_id, updated_at 
        FROM pnr_records 
        WHERE booking_status NOT IN ('CANCELLED', 'REFUNDED') 
        ORDER BY NEWID()
    """)
    row = cursor.fetchone()
    
    if not row:
        print(f"{UPDATE_COLOR} UPDATE NOT FOUND {RESET_COLOR} Không tìm thấy PNR nào phù hợp để thay đổi chuyến bay.")
        return
        
    pnr_id, last_updated_at = row
    
    # Tính thời điểm cập nhật mới (sau lần cập nhật trước đó từ 1-5 ngày)
    new_updated_at = last_updated_at + timedelta(days=random.randint(1, 5), minutes=random.randint(10, 300))
    
    # Dời ngày bay từ 1 đến 3 ngày
    days_to_shift = random.randint(1, 3)
    
    # Lấy danh sách các chặng bay của PNR này
    cursor.execute("SELECT segment_id, flight_date FROM flight_segments WHERE pnr_id = ?", (pnr_id,))
    segments = cursor.fetchall()
    
    for segment_id, flight_date in segments:
        # Xử lý kiểu dữ liệu của flight_date (chuỗi hoặc object date)
        if isinstance(flight_date, str):
            current_date = datetime.strptime(flight_date, '%Y-%m-%d').date()
        else:
            current_date = flight_date
            
        new_flight_date = current_date + timedelta(days=days_to_shift)
        new_flight_date_str = new_flight_date.strftime('%Y-%m-%d')
        
        # Cập nhật chặng bay
        cursor.execute("""
            UPDATE flight_segments 
            SET flight_date = ?, updated_at = ? 
            WHERE segment_id = ?
        """, (new_flight_date_str, new_updated_at, segment_id))
        
    # Cập nhật trạng thái PNR thành CHANGED
    cursor.execute("""
        UPDATE pnr_records 
        SET booking_status = 'CHANGED', updated_at = ? 
        WHERE pnr_id = ?
    """, (new_updated_at, pnr_id))
    
    # Ghi nhận sự kiện CHANGED
    cursor.execute("""
        INSERT INTO booking_events (pnr_id, event_type, created_at) 
        VALUES (?, 'CHANGED', ?)
    """, (pnr_id, new_updated_at))
    
    print(f"{CREATE_COLOR} CHANGE FLIGHT {RESET_COLOR} Đã dời lịch bay thêm {days_to_shift} ngày cho PNR: {pnr_id} - Trạng thái mới: CHANGED")
