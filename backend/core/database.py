import sqlite3
import pandas as pd
from datetime import datetime, timezone

# Đường dẫn file SQLite dùng để lưu lịch sử cảnh báo
DB_PATH = 'history.db'


def init_db():
    """
    Khởi tạo cơ sở dữ liệu nếu chưa tồn tại.

    Tạo bảng `alerts` để lưu các bản ghi cảnh báo gồm thời gian, mã bệnh nhân
    và các chỉ số sinh tồn tại thời điểm cảnh báo.
    """
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
    """
    Ghi một bản ghi cảnh báo mới vào file SQLite.

    Tham số:
    - patient_id: mã bệnh nhân (chuỗi)
    - hr: giá trị nhịp tim (float)
    - spo2: giá trị SpO2 (%) (float)
    - risk: điểm rủi ro (float)
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Store timestamps in UTC ISO8601 to avoid timezone ambiguity
    now = datetime.now(timezone.utc).isoformat()
    cursor.execute('''
        INSERT INTO alerts (timestamp, patient_id, hr, spo2, risk_score)
        VALUES (?, ?, ?, ?, ?)
    ''', (now, patient_id, hr, spo2, risk))
    conn.commit()
    conn.close()


def get_recent_history(limit=10):
    """
    Trả về danh sách các bản ghi cảnh báo gần đây nhất.

    Giá trị trả về là danh sách dict phù hợp để frontend hiển thị.
    """
    conn = sqlite3.connect(DB_PATH)
    df_history = pd.read_sql_query(f"SELECT * FROM alerts ORDER BY id DESC LIMIT {limit}", conn)
    conn.close()
    return df_history.to_dict(orient="records")