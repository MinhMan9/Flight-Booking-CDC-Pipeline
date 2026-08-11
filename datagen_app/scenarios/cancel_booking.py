import random
from datetime import datetime, timedelta

# ANSI color codes
CREATE_COLOR = "\033[42;37m"
UPDATE_COLOR = "\033[43;30m"
DELETE_COLOR = "\033[41;37m"
RESET_COLOR = "\033[0m"

def run(cursor, fake):
    """
    Execute booking cancellation:
    - Get a random active PNR (not CANCELLED/REFUNDED).
    - If paid (TICKETED/or has SUCCESS payment), update status to REFUNDED
      for PNR, tickets, and payment transaction.
    - If unpaid (CREATED), update status to CANCELLED.
    """
    # Get a random PNR that is not cancelled or refunded
    cursor.execute("""
        SELECT TOP 1 pnr_id, updated_at, booking_status 
        FROM pnr_records 
        WHERE booking_status NOT IN ('CANCELLED', 'REFUNDED') 
        ORDER BY NEWID()
    """)
    row = cursor.fetchone()
    
    if not row:
        print(f"{UPDATE_COLOR} CANCEL NOT FOUND {RESET_COLOR} No suitable PNR found to cancel booking.")
        return
        
    pnr_id, last_updated_at, booking_status = row
    
    # Calculate new update time (1-5 days after the previous update)
    new_updated_at = last_updated_at + timedelta(days=random.randint(1, 5), minutes=random.randint(10, 300))
    
    # Check if this PNR has a successful payment
    cursor.execute("""
        SELECT COUNT(*) 
        FROM payments 
        WHERE pnr_id = ? AND payment_status = 'SUCCESS'
    """, (pnr_id,))
    is_paid = cursor.fetchone()[0] > 0
    
    if is_paid:
        # Paid -> Refunded (REFUNDED)
        
        # 1. Update payment status to REFUNDED
        cursor.execute("""
            UPDATE payments 
            SET payment_status = 'REFUNDED', updated_at = ? 
            WHERE pnr_id = ? AND payment_status = 'SUCCESS'
        """, (new_updated_at, pnr_id))
        
        # 2. Update status of tickets belonging to this PNR to REFUNDED
        cursor.execute("SELECT passenger_id FROM passengers WHERE pnr_id = ?", (pnr_id,))
        passenger_ids = [r[0] for r in cursor.fetchall()]
        
        if passenger_ids:
            # Convert ID list to tuple or loop through elements to update
            for pid in passenger_ids:
                cursor.execute("""
                    UPDATE tickets 
                    SET ticket_status = 'REFUNDED', updated_at = ? 
                    WHERE passenger_id = ?
                """, (new_updated_at, pid))
                
        # 3. Update PNR status to REFUNDED
        cursor.execute("""
            UPDATE pnr_records 
            SET booking_status = 'REFUNDED', updated_at = ? 
            WHERE pnr_id = ?
        """, (new_updated_at, pnr_id))
        
        # 4. Record both CANCELLED and REFUNDED events for complete history tracking
        cursor.execute("""
            INSERT INTO booking_events (pnr_id, event_type, created_at) 
            VALUES (?, 'CANCELLED', ?)
        """, (pnr_id, new_updated_at))
        
        cursor.execute("""
            INSERT INTO booking_events (pnr_id, event_type, created_at) 
            VALUES (?, 'REFUNDED', ?)
        """, (pnr_id, new_updated_at))
        
        print(f"{CREATE_COLOR} CANCEL BOOKING {RESET_COLOR} Successfully cancelled and REFUNDED PNR: {pnr_id} - New status: REFUNDED")
    else:
        # Unpaid -> Cancel directly (CANCELLED)
        
        # 1. Update PNR status to CANCELLED
        cursor.execute("""
            UPDATE pnr_records 
            SET booking_status = 'CANCELLED', updated_at = ? 
            WHERE pnr_id = ?
        """, (new_updated_at, pnr_id))
        
        # 2. Record CANCELLED event
        cursor.execute("""
            INSERT INTO booking_events (pnr_id, event_type, created_at) 
            VALUES (?, 'CANCELLED', ?)
        """, (pnr_id, new_updated_at))
        
        print(f"{CREATE_COLOR} CANCEL BOOKING {RESET_COLOR} Cancelled unpaid booking for PNR: {pnr_id} - New status: CANCELLED")
