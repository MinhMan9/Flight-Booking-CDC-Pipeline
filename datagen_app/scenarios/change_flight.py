import random
from datetime import datetime, timedelta

# ANSI color codes
CREATE_COLOR = "\033[42;37m"
UPDATE_COLOR = "\033[43;30m"
DELETE_COLOR = "\033[41;37m"
RESET_COLOR = "\033[0m"

def run(cursor, fake):
    """
    Execute flight change: shift flight date randomly by 1 to 3 days.
    """
    # Get a random PNR that is not cancelled or refunded
    cursor.execute("""
        SELECT TOP 1 pnr_id, updated_at 
        FROM pnr_records 
        WHERE booking_status NOT IN ('CANCELLED', 'REFUNDED') 
        ORDER BY NEWID()
    """)
    row = cursor.fetchone()
    
    if not row:
        print(f"{UPDATE_COLOR} UPDATE NOT FOUND {RESET_COLOR} No suitable PNR found to change flight.")
        return
        
    pnr_id, last_updated_at = row
    
    # Calculate new update time (1-5 days after the previous update)
    new_updated_at = last_updated_at + timedelta(days=random.randint(1, 5), minutes=random.randint(10, 300))
    
    # Shift flight date by 1 to 3 days
    days_to_shift = random.randint(1, 3)
    
    # Get list of flight segments for this PNR
    cursor.execute("SELECT segment_id, flight_date FROM flight_segments WHERE pnr_id = ?", (pnr_id,))
    segments = cursor.fetchall()
    
    for segment_id, flight_date in segments:
        # Handle data type of flight_date (string or date object)
        if isinstance(flight_date, str):
            current_date = datetime.strptime(flight_date, '%Y-%m-%d').date()
        else:
            current_date = flight_date
            
        new_flight_date = current_date + timedelta(days=days_to_shift)
        new_flight_date_str = new_flight_date.strftime('%Y-%m-%d')
        
        # Update flight segment
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
    
    # Record CHANGED event
    cursor.execute("""
        INSERT INTO booking_events (pnr_id, event_type, created_at) 
        VALUES (?, 'CHANGED', ?)
    """, (pnr_id, new_updated_at))
    
    print(f"{CREATE_COLOR} CHANGE FLIGHT {RESET_COLOR} Shifted flight schedule by {days_to_shift} days for PNR: {pnr_id} - New status: CHANGED")
