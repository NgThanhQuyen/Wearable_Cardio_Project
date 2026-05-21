import sqlite3
import pandas as pd
from datetime import datetime

DB_PATH = 'history.db'

def init_db():
    """Tạo bảng alerts nếu nó không tồn tại"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            patient_id TEXT,
            hr REAL,
            spo2 REAL,
            risk_score REAL
        )
    ''')
    conn.commit()
    conn.close()
    print("Database: Sẵn sàng")

def save_alert(patient_id, hr, spo2, risk):
    """Lưu bản ghi cảnh báo vào database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute('''
        INSERT INTO alerts (timestamp, patient_id, hr, spo2, risk_score)
        VALUES (?, ?, ?, ?, ?)
    ''', (now, patient_id, hr, spo2, risk))
    conn.commit()
    conn.close()

def get_recent_history(limit=10):
    """Lấy lịch sử cảnh báo gần đây để hiển thị trên frontend"""
    conn = sqlite3.connect(DB_PATH)
    df_history = pd.read_sql_query(f"SELECT * FROM alerts ORDER BY id DESC LIMIT {limit}", conn)
    conn.close()
    return df_history.to_dict(orient="records")