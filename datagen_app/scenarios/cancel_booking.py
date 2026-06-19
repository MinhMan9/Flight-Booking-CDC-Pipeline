import random
from datetime import datetime, timedelta

# Mã màu ANSI
CREATE_COLOR = "\033[42;37m"
UPDATE_COLOR = "\033[43;30m"
DELETE_COLOR = "\033[41;37m"
RESET_COLOR = "\033[0m"

def run(cursor, fake):
    """
    Thực hiện hủy booking:
    - Lấy ngẫu nhiên một PNR hoạt động (chưa CANCELLED/REFUNDED).
    - Nếu đã thanh toán (TICKETED/hoặc có payment SUCCESS), cập nhật trạng thái hoàn tiền (REFUNDED)
      cho PNR, vé máy bay và giao dịch thanh toán.
    - Nếu chưa thanh toán (CREATED), cập nhật trạng thái hủy (CANCELLED).
    """
    # Lấy ngẫu nhiên một PNR chưa bị hủy hoặc hoàn tiền
    cursor.execute("""
        SELECT TOP 1 pnr_id, updated_at, booking_status 
        FROM pnr_records 
        WHERE booking_status NOT IN ('CANCELLED', 'REFUNDED') 
        ORDER BY NEWID()
    """)
    row = cursor.fetchone()
    
    if not row:
        print(f"{UPDATE_COLOR} CANCEL NOT FOUND {RESET_COLOR} Không tìm thấy PNR nào phù hợp để hủy booking.")
        return
        
    pnr_id, last_updated_at, booking_status = row
    
    # Tính thời điểm cập nhật mới (sau lần cập nhật trước đó từ 1-5 ngày)
    new_updated_at = last_updated_at + timedelta(days=random.randint(1, 5), minutes=random.randint(10, 300))
    
    # Kiểm tra xem PNR này đã có thanh toán thành công chưa
    cursor.execute("""
        SELECT COUNT(*) 
        FROM payments 
        WHERE pnr_id = ? AND payment_status = 'SUCCESS'
    """, (pnr_id,))
    is_paid = cursor.fetchone()[0] > 0
    
    if is_paid:
        # Đã thanh toán -> Hoàn tiền (REFUNDED)
        
        # 1. Cập nhật trạng thái thanh toán thành REFUNDED
        cursor.execute("""
            UPDATE payments 
            SET payment_status = 'REFUNDED', updated_at = ? 
            WHERE pnr_id = ? AND payment_status = 'SUCCESS'
        """, (new_updated_at, pnr_id))
        
        # 2. Cập nhật trạng thái vé máy bay của các khách hàng thuộc PNR thành REFUNDED
        cursor.execute("SELECT passenger_id FROM passengers WHERE pnr_id = ?", (pnr_id,))
        passenger_ids = [r[0] for r in cursor.fetchall()]
        
        if passenger_ids:
            # Chuyển list ID thành tuple hoặc lặp từng phần tử để cập nhật
            for pid in passenger_ids:
                cursor.execute("""
                    UPDATE tickets 
                    SET ticket_status = 'REFUNDED', updated_at = ? 
                    WHERE passenger_id = ?
                """, (new_updated_at, pid))
                
        # 3. Cập nhật trạng thái PNR thành REFUNDED
        cursor.execute("""
            UPDATE pnr_records 
            SET booking_status = 'REFUNDED', updated_at = ? 
            WHERE pnr_id = ?
        """, (new_updated_at, pnr_id))
        
        # 4. Ghi nhận cả sự kiện CANCELLED và REFUNDED để theo dõi lịch sử đầy đủ
        cursor.execute("""
            INSERT INTO booking_events (pnr_id, event_type, created_at) 
            VALUES (?, 'CANCELLED', ?)
        """, (pnr_id, new_updated_at))
        
        cursor.execute("""
            INSERT INTO booking_events (pnr_id, event_type, created_at) 
            VALUES (?, 'REFUNDED', ?)
        """, (pnr_id, new_updated_at))
        
        print(f"{CREATE_COLOR} CANCEL BOOKING {RESET_COLOR} Đã hủy và HOÀN TIỀN thành công cho PNR: {pnr_id} - Trạng thái mới: REFUNDED")
    else:
        # Chưa thanh toán -> Hủy trực tiếp (CANCELLED)
        
        # 1. Cập nhật trạng thái PNR thành CANCELLED
        cursor.execute("""
            UPDATE pnr_records 
            SET booking_status = 'CANCELLED', updated_at = ? 
            WHERE pnr_id = ?
        """, (new_updated_at, pnr_id))
        
        # 2. Ghi nhận sự kiện CANCELLED
        cursor.execute("""
            INSERT INTO booking_events (pnr_id, event_type, created_at) 
            VALUES (?, 'CANCELLED', ?)
        """, (pnr_id, new_updated_at))
        
        print(f"{CREATE_COLOR} CANCEL BOOKING {RESET_COLOR} Đã hủy booking chưa thanh toán cho PNR: {pnr_id} - Trạng thái mới: CANCELLED")
