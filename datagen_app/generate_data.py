import random
import string
import uuid
import time
import unicodedata
from datetime import datetime, timedelta
from faker import Faker
from db_connection import get_db_connection

# Initialize Vietnamese Faker
fake = Faker('vi_VN')

# ==========================================
# 1. DOMAIN VALUES DECLARATION
# ==========================================
CHANNELS = ['WEB', 'APP', 'AGENCY', 'TICKET_OFFICE', 'CALL_CENTER']
AIRPORTS = ['SGN', 'HAN', 'DAD', 'CXR', 'PQC', 'VCA', 'HUI', 'VDO']
AIRLINES = ['VN', 'VJ', 'QH', 'VU']
PAYMENT_METHODS = ['CREDIT_CARD', 'ATM_CARD', 'E_WALLET', 'CASH']

generated_pnrs = set()
generated_payment_ids = set()
generated_ticket_numbers = set()

def generate_pnr():
    while True:
        pnr = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        if pnr not in generated_pnrs:
            generated_pnrs.add(pnr)
            return pnr

def generate_payment_id():
    while True:
        payment_id = str(uuid.uuid4())
        if payment_id not in generated_payment_ids:
            generated_payment_ids.add(payment_id)
            return payment_id

def generate_ticket_number():
    while True:
        ticket_no = fake.numerify('738##########')
        if ticket_no not in generated_ticket_numbers:
            generated_ticket_numbers.add(ticket_no)
            return ticket_no

# ==========================================
# 2. MAIN DATA GENERATION LOGIC
# ==========================================
def simulate_booking_transaction(cursor, count):
    # Simulated time
    created_at = fake.date_time_between(start_date='-30d', end_date='now')
    updated_at = created_at + timedelta(minutes=random.randint(5, 120))
    flight_date = (created_at + timedelta(days=random.randint(3, 90))).strftime('%Y-%m-%d')
    
    # 1. CREATE PNR
    pnr_id = generate_pnr()
    channel = random.choices(CHANNELS, weights=[40, 30, 20, 5, 5], k=1)[0]
    
    cursor.execute("""
        INSERT INTO pnr_records (pnr_id, booking_channel, booking_status, created_at, updated_at)
        VALUES (?, ?, 'CREATED', ?, ?)
    """, (pnr_id, channel, created_at, created_at))

    # 2. RECORD EVENT: CREATED
    cursor.execute("""
        INSERT INTO booking_events (pnr_id, event_type, created_at)
        VALUES (?, 'CREATED', ?)
    """, (pnr_id, created_at))

    # 3. CREATE PASSENGERS (1 to 3 people)
    num_passengers = random.randint(1, 3)
    passenger_ids = []
    
    for _ in range(num_passengers):
        # Use random gender to get correct Vietnamese name
        gender = random.choice(['male', 'female'])
        fname = fake.first_name_male() if gender == 'male' else fake.first_name_female()
        lname = fake.last_name()
        
        # Remove Vietnamese accents and create email from name
        clean_fname = unicodedata.normalize('NFKD', fname).encode('ASCII', 'ignore').decode('utf-8').lower().replace(' ', '')
        clean_lname = unicodedata.normalize('NFKD', lname).encode('ASCII', 'ignore').decode('utf-8').lower().replace(' ', '')
        
        # Diversify email formats of real users
        email_formats = [
            f"{clean_fname}.{clean_lname}{random.randint(1, 999)}",
            f"{clean_lname}{clean_fname}{random.randint(1, 99)}",
            f"{clean_fname}_{random.randint(1970, 2005)}", # similar to birth year format
            f"{clean_fname}{clean_lname[0]}{random.randint(10, 99)}" 
        ]
        email = f"{random.choice(email_formats)}@{fake.free_email_domain()}"
        
        passport = fake.bothify(text=random.choice(['C#######', '############']))
        
        # Use OUTPUT INSERTED to get newly created identity ID
        cursor.execute("""
            INSERT INTO passengers (pnr_id, first_name, last_name, email, passport_number, created_at, updated_at)
            OUTPUT INSERTED.passenger_id
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (pnr_id, fname, lname, email, passport, created_at, created_at))
        
        passenger_id = cursor.fetchone()[0]
        passenger_ids.append(passenger_id)

    # 4. CREATE FLIGHT SEGMENTS (one-way or round-trip)
    num_segments = random.choices([1, 2], weights=[70, 30], k=1)[0]
    route = random.sample(AIRPORTS, 2)
    airline = random.choice(AIRLINES)
    
    # Outbound flight
    cursor.execute("""
        INSERT INTO flight_segments (pnr_id, origin_airport, dest_airport, flight_date, airline_code, flight_number, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (pnr_id, route[0], route[1], flight_date, airline, str(random.randint(10, 9999)), created_at, created_at))
    
    if num_segments == 2: # Inbound flight
        return_date = (datetime.strptime(flight_date, '%Y-%m-%d') + timedelta(days=random.randint(2, 10))).strftime('%Y-%m-%d')
        cursor.execute("""
            INSERT INTO flight_segments (pnr_id, origin_airport, dest_airport, flight_date, airline_code, flight_number, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (pnr_id, route[1], route[0], return_date, airline, str(random.randint(10, 9999)), created_at, created_at))

    # 5. PAYMENT & TICKETING LOGIC (80% success rate)
    is_ticketed = random.random() < 0.8
    
    payment_id = generate_payment_id()
    pay_method = random.choice(PAYMENT_METHODS)
    fare_class = random.choices(['Y', 'W', 'J', 'F'], weights=[60, 20, 15, 5], k=1)[0]
    
    # Fare Class price logic matching reporting
    if fare_class == 'Y':
        base_amount = random.uniform(1500000, 5000000)
    elif fare_class == 'W':
        base_amount = random.uniform(5000000, 10000000)
    elif fare_class == 'J':
        base_amount = random.uniform(11800000, 20000000)
    else: # F
        base_amount = random.uniform(30000000, 50000000)
        
    total_amount = round(base_amount * num_passengers * num_segments, 2)

    if is_ticketed:
        # Update PNR status to TICKETED
        cursor.execute("UPDATE pnr_records SET booking_status = 'TICKETED', updated_at = ? WHERE pnr_id = ?", (updated_at, pnr_id))
        
        # Add TICKETED event
        cursor.execute("INSERT INTO booking_events (pnr_id, event_type, created_at) VALUES (?, 'TICKETED', ?)", (pnr_id, updated_at))
        
        # Create successful payment
        cursor.execute("""
            INSERT INTO payments (payment_id, pnr_id, payment_method, amount, currency, payment_status, created_at, updated_at)
            VALUES (?, ?, ?, ?, 'VND', 'SUCCESS', ?, ?)
        """, (payment_id, pnr_id, pay_method, total_amount, updated_at, updated_at))

        # Issue ticket for each passenger
        for pid in passenger_ids:
            ticket_no = generate_ticket_number()
            cursor.execute("""
                INSERT INTO tickets (ticket_number, passenger_id, fare_class, ticket_status, created_at, updated_at)
                VALUES (?, ?, ?, 'ISSUED', ?, ?)
            """, (ticket_no, pid, fare_class, updated_at, updated_at))
            
    else:
        # Update PNR status to CANCELLED
        cursor.execute("UPDATE pnr_records SET booking_status = 'CANCELLED', updated_at = ? WHERE pnr_id = ?", (updated_at, pnr_id))
        
        # Add CANCELLED event
        cursor.execute("INSERT INTO booking_events (pnr_id, event_type, created_at) VALUES (?, 'CANCELLED', ?)", (pnr_id, updated_at))
        
        # Create failed payment
        cursor.execute("""
            INSERT INTO payments (payment_id, pnr_id, payment_method, amount, currency, payment_status, created_at, updated_at)
            VALUES (?, ?, ?, ?, 'VND', 'FAILED', ?, ?)
        """, (payment_id, pnr_id, pay_method, total_amount, updated_at, updated_at))
            
    print(f"[{count}/100000] Successfully generated PNR: {pnr_id} - Passengers: {num_passengers} - Segments: {num_segments} - Status: {'TICKETED' if is_ticketed else 'CANCELLED'}")

# ==========================================
# 3. RUN CONTINUOUS LOOP (CDC TRIGGER)
# ==========================================
if __name__ == "__main__":
    print("Starting Flight Booking CDC data generation flow...")
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        total_records = 100000
        count = 0
        
        # Loop to generate 100,000 records
        while count < total_records:
            count += 1
            simulate_booking_transaction(cursor, count)
            conn.commit() # Commit to database
            
        print(f"Successfully generated all {total_records} records!")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'conn' in locals():
            conn.close()