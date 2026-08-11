import random
import uuid
from datetime import datetime, timedelta

PAYMENT_METHODS = ['CREDIT_CARD', 'ATM_CARD', 'E_WALLET', 'CASH']

# ANSI color codes
CREATE_COLOR = "\033[42;37m"
UPDATE_COLOR = "\033[43;30m"
DELETE_COLOR = "\033[41;37m"
RESET_COLOR = "\033[0m"

def generate_unique_payment_id(cursor):
    """
    Generate a unique payment_id and check for duplicates in the database.
    """
    while True:
        pay_id = str(uuid.uuid4())
        cursor.execute("SELECT COUNT(*) FROM payments WHERE payment_id = ?", (pay_id,))
        if cursor.fetchone()[0] == 0:
            return pay_id

def generate_unique_ticket_number(cursor, fake):
    """
    Generate a unique ticket number and check for duplicates in the database.
    """
    while True:
        ticket_no = fake.numerify('738##########')
        cursor.execute("SELECT COUNT(*) FROM tickets WHERE ticket_number = ?", (ticket_no,))
        if cursor.fetchone()[0] == 0:
            return ticket_no

def run(cursor, fake):
    """
    Execute payment for a random PNR with status CREATED.
    """
    # Get a random PNR that has status CREATED
    cursor.execute("""
        SELECT TOP 1 pnr_id, created_at 
        FROM pnr_records 
        WHERE booking_status = 'CREATED' 
        ORDER BY NEWID()
    """)
    row = cursor.fetchone()
    
    if not row:
        print(f"{UPDATE_COLOR} PAYMENT NOT FOUND {RESET_COLOR} No suitable PNR found for payment.")
        return
        
    pnr_id, created_at = row
    
    # Calculate update time (5 to 120 minutes after PNR creation)
    updated_at = created_at + timedelta(minutes=random.randint(5, 120))
    
    # Get number of passengers and flight segments to calculate amount
    cursor.execute("SELECT COUNT(*) FROM passengers WHERE pnr_id = ?", (pnr_id,))
    num_passengers = max(1, cursor.fetchone()[0])
    
    cursor.execute("SELECT COUNT(*) FROM flight_segments WHERE pnr_id = ?", (pnr_id,))
    num_segments = max(1, cursor.fetchone()[0])
    
    # Determine ticket price based on Fare Class
    fare_class = random.choices(['Y', 'W', 'J', 'F'], weights=[60, 20, 15, 5], k=1)[0]
    if fare_class == 'Y':
        base_amount = random.uniform(1500000, 5000000)
    elif fare_class == 'W':
        base_amount = random.uniform(5000000, 10000000)
    elif fare_class == 'J':
        base_amount = random.uniform(11800000, 20000000)
    else: # F
        base_amount = random.uniform(30000000, 50000000)
        
    total_amount = round(base_amount * num_passengers * num_segments, 2)
    
    # Random payment status (80% SUCCESS, 20% FAILED)
    is_success = random.random() < 0.8
    pay_method = random.choice(PAYMENT_METHODS)
    payment_id = generate_unique_payment_id(cursor)
    payment_status = 'SUCCESS' if is_success else 'FAILED'
    
    # 1. Insert payment record
    cursor.execute("""
        INSERT INTO payments (payment_id, pnr_id, payment_method, amount, currency, payment_status, created_at, updated_at)
        VALUES (?, ?, ?, ?, 'VND', ?, ?, ?)
    """, (payment_id, pnr_id, pay_method, total_amount, payment_status, updated_at, updated_at))
    
    if is_success:
        # 2. Update PNR status to TICKETED
        cursor.execute("""
            UPDATE pnr_records 
            SET booking_status = 'TICKETED', updated_at = ? 
            WHERE pnr_id = ?
        """, (updated_at, pnr_id))
        
        # 3. Record TICKETED event
        cursor.execute("""
            INSERT INTO booking_events (pnr_id, event_type, created_at) 
            VALUES (?, 'TICKETED', ?)
        """, (pnr_id, updated_at))
        
        # 4. Issue tickets for each passenger belonging to this PNR
        cursor.execute("SELECT passenger_id FROM passengers WHERE pnr_id = ?", (pnr_id,))
        passenger_ids = [r[0] for r in cursor.fetchall()]
        
        for pid in passenger_ids:
            ticket_no = generate_unique_ticket_number(cursor, fake)
            cursor.execute("""
                INSERT INTO tickets (ticket_number, passenger_id, fare_class, ticket_status, created_at, updated_at)
                VALUES (?, ?, ?, 'ISSUED', ?, ?)
            """, (ticket_no, pid, fare_class, updated_at, updated_at))
            
        print(f"{CREATE_COLOR} PAYMENT {RESET_COLOR} Successful payment for PNR: {pnr_id} - Amount: {total_amount:,.2f} VND - New status: TICKETED")
    else:
        # Failed payment -> Update PNR to CANCELLED
        cursor.execute("""
            UPDATE pnr_records 
            SET booking_status = 'CANCELLED', updated_at = ? 
            WHERE pnr_id = ?
        """, (updated_at, pnr_id))
        
        # Record CANCELLED event
        cursor.execute("""
            INSERT INTO booking_events (pnr_id, event_type, created_at) 
            VALUES (?, 'CANCELLED', ?)
        """, (pnr_id, updated_at))
        
        print(f"{DELETE_COLOR} PAYMENT {RESET_COLOR} Failed payment for PNR: {pnr_id} - New status: CANCELLED")
