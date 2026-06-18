import os
import pyodbc
from dotenv import load_dotenv

# Load biến môi trường từ file .env
load_dotenv()

def get_db_connection():
    """
    Thiết lập kết nối tới cơ sở dữ liệu SQL Server.
    """
    SERVER = os.getenv('DB_SERVER')
    DATABASE = os.getenv('DB_NAME')
    USERNAME = os.getenv('DB_USERNAME')
    PASSWORD = os.getenv('DB_PASSWORD')

    # Chuỗi kết nối (Dùng ODBC Driver 17 hoặc 18 tùy máy)
    conn_str = f'DRIVER={{ODBC Driver 18 for SQL Server}};SERVER={SERVER};DATABASE={DATABASE};UID={USERNAME};PWD={PASSWORD};TrustServerCertificate=yes'
    
    return pyodbc.connect(conn_str)
