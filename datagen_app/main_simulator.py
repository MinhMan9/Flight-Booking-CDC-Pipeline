import sys
import os
import time
import random
import pyodbc
from faker import Faker

# Thêm thư mục hiện tại chứa script vào sys.path để chạy từ bất kỳ đâu
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from db_connection import get_db_connection
from scenarios import book_new_flight, make_payment, change_flight, cancel_booking

# Ánh xạ tên kịch bản với module thực thi
SCENARIOS = {
    'book_new_flight': book_new_flight.run,
    'make_payment': make_payment.run,
    'change_flight': change_flight.run,
    'cancel_booking': cancel_booking.run
}

# Trọng số mặc định cho các kịch bản khi chạy ngẫu nhiên
WEIGHTS = [0.50, 0.30, 0.10, 0.10]

# Mã màu ANSI
CREATE_COLOR = "\033[42;37m"
UPDATE_COLOR = "\033[43;30m"
DELETE_COLOR = "\033[41;37m"
CYAN_UNDERLINE = "\033[4;36m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
RESET_COLOR = "\033[0m"

def execute_scenario(scenario_name, cursor, fake):
    """
    Thực thi một kịch bản, tự động bắt lỗi trùng lặp khoá (IntegrityError) và thử lại.
    """
    scenario_func = SCENARIOS[scenario_name]
    conn = cursor.connection
    
    while True:
        try:
            scenario_func(cursor, fake)
            conn.commit()
            break
        except pyodbc.IntegrityError as e:
            # Nếu xảy ra lỗi trùng khóa chính (lỡ sinh trùng ID), thực hiện rollback và chạy lại kịch bản
            print(f"{DELETE_COLOR} ERROR {RESET_COLOR} Phát hiện trùng lặp ID (IntegrityError), đang tự động thử lại... Chi tiết: {e}")
            conn.rollback()
        except Exception as e:
            # Các ngoại lệ khác sẽ rollback và ném ra ngoài để ghi nhận log
            conn.rollback()
            raise e

def main():
    fake = Faker('vi_VN')
    
    # Kết nối cơ sở dữ liệu
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
    except Exception as e:
        print(f"❌ Không thể kết nối cơ sở dữ liệu: {e}")
        sys.exit(1)
        
    print("Khởi động Trình Giả Lập Giao Dịch Flight Booking...")
    print(f"Danh sách kịch bản hiện có: {list(SCENARIOS.keys())}")
    
    # 1. Chế độ chỉ định kịch bản bằng tham số khi chạy file:
    # Cú pháp: python main_simulator.py <tên_kịch_bản> <số_lần_chạy>
    if len(sys.argv) >= 3:
        target_scenario = sys.argv[1]
        try:
            num_runs = int(sys.argv[2])
        except ValueError:
            print("❌ Lỗi: Tham số số lần thực thi phải là số nguyên!")
            conn.close()
            sys.exit(1)
            
        if target_scenario not in SCENARIOS:
            print(f"❌ Lỗi: Kịch bản '{target_scenario}' không hợp lệ.")
            print(f"Danh sách hợp lệ: {list(SCENARIOS.keys())}")
            conn.close()
            sys.exit(1)
            
        print(f"{CYAN_UNDERLINE}--- Đang thực thi kịch bản '{target_scenario}' trong {num_runs} lần... ---{RESET_COLOR}")
        for i in range(1, num_runs + 1):
            print(f"\n[Lần chạy {i}/{num_runs}]")
            try:
                execute_scenario(target_scenario, cursor, fake)
            except Exception as e:
                print(f"❌ Lỗi khi thực thi kịch bản: {e}")
                
        print(f"\n{GREEN}[HOÀN THÀNH] Tác vụ hoàn tất.{RESET_COLOR}")
        conn.close()
        return

    # 2. Chế độ chạy ngẫu nhiên liên tục (Mặc định khi không có tham số)
    print(f"\n{CYAN_UNDERLINE}--- Đang chạy mô phỏng ngẫu nhiên liên tục... ---{RESET_COLOR}")
    
    try:
        while True:
            # Lựa chọn ngẫu nhiên kịch bản dựa trên trọng số
            scenario_name = random.choices(list(SCENARIOS.keys()), weights=WEIGHTS, k=1)[0]
            
            try:
                execute_scenario(scenario_name, cursor, fake)
            except KeyboardInterrupt:
                print(f"\n{YELLOW} Đã dừng trình giả lập giao dịch. {RESET_COLOR}")
            except Exception as e:
                print(f"❌ Lỗi trong luồng giả lập: {e}")
                
            # Nghỉ ngẫu nhiên từ 1 đến 3 giây
            delay = random.uniform(1.0, 3.0)
            time.sleep(delay)
            
    except KeyboardInterrupt:
        print(f"\n{YELLOW} Đã dừng trình giả lập giao dịch. {RESET_COLOR}")
    finally:
        conn.close()

if __name__ == "__main__":
    main()
