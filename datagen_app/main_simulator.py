import sys
import os
import time
import random
import pyodbc
from faker import Faker

# Add current directory containing script to sys.path to run from anywhere
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from db_connection import get_db_connection
from scenarios import book_new_flight, make_payment, change_flight, cancel_booking

# Map scenario name to execution module
SCENARIOS = {
    'book_new_flight': book_new_flight.run,
    'make_payment': make_payment.run,
    'change_flight': change_flight.run,
    'cancel_booking': cancel_booking.run
}

# Default weights for scenarios when running randomly
WEIGHTS = [0.50, 0.30, 0.10, 0.10]

# ANSI color codes
CREATE_COLOR = "\033[42;37m"
UPDATE_COLOR = "\033[43;30m"
DELETE_COLOR = "\033[41;37m"
CYAN_UNDERLINE = "\033[4;36m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
RESET_COLOR = "\033[0m"

def execute_scenario(scenario_name, cursor, fake):
    """
    Execute a scenario, catch primary key duplication (IntegrityError) and retry automatically.
    """
    scenario_func = SCENARIOS[scenario_name]
    conn = cursor.connection
    
    while True:
        try:
            scenario_func(cursor, fake)
            conn.commit()
            break
        except pyodbc.IntegrityError as e:
            # If primary key duplication occurs (accidentally generated duplicate ID), rollback and retry scenario
            print(f"{DELETE_COLOR} ERROR {RESET_COLOR} Duplicate ID detected (IntegrityError), retrying automatically... Details: {e}")
            conn.rollback()
        except Exception as e:
            # Other exceptions will rollback and raise to log
            conn.rollback()
            raise e

def main():
    fake = Faker('vi_VN')
    
    # Connect to database
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
    except Exception as e:
        print(f"Error connecting to database: {e}")
        sys.exit(1)
        
    print("Starting Flight Booking Transaction Simulator...")
    print(f"List of available scenarios: {list(SCENARIOS.keys())}")
    
    # 1. Parameterized scenario execution mode:
    # Syntax: python main_simulator.py <scenario_name> <num_runs>
    if len(sys.argv) >= 3:
        target_scenario = sys.argv[1]
        try:
            num_runs = int(sys.argv[2])
        except ValueError:
            print("Error: Execution count parameter must be an integer!")
            conn.close()
            sys.exit(1)
            
        if target_scenario not in SCENARIOS:
            print(f"Error: Invalid scenario '{target_scenario}'.")
            print(f"Valid list: {list(SCENARIOS.keys())}")
            conn.close()
            sys.exit(1)
            
        print(f"{CYAN_UNDERLINE}--- Executing scenario '{target_scenario}' {num_runs} times... ---{RESET_COLOR}")
        for i in range(1, num_runs + 1):
            print(f"\n[Run {i}/{num_runs}]")
            try:
                execute_scenario(target_scenario, cursor, fake)
            except Exception as e:
                print(f"Error executing scenario: {e}")
                
        print(f"\n{GREEN}[COMPLETED] Task finished.{RESET_COLOR}")
        conn.close()
        return

    # 2. Continuous random execution mode (default when no parameters provided)
    print(f"\n{CYAN_UNDERLINE}--- Running continuous random simulation... ---{RESET_COLOR}")
    
    try:
        while True:
            # Randomly select scenario based on weights
            scenario_name = random.choices(list(SCENARIOS.keys()), weights=WEIGHTS, k=1)[0]
            
            try:
                execute_scenario(scenario_name, cursor, fake)
            except KeyboardInterrupt:
                print(f"\n{YELLOW} Transaction simulator stopped. {RESET_COLOR}")
            except Exception as e:
                print(f"Error in simulator flow: {e}")
                
            # Sleep randomly from 1 to 3 seconds
            delay = random.uniform(1.0, 3.0)
            time.sleep(delay)
            
    except KeyboardInterrupt:
        print(f"\n{YELLOW} Transaction simulator stopped. {RESET_COLOR}")
    finally:
        conn.close()

if __name__ == "__main__":
    main()
