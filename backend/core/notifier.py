import requests
import os
from dotenv import load_dotenv

# Nạp biến môi trường từ file .env (nếu có)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, '.env'))

# Biến cấu hình Telegram (nếu chưa cấu hình, notifier sẽ bỏ qua)
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


def send_telegram_alert(patient_id, hr, spo2, risk, alert_type="alert"):
    """
    Gửi thông báo tới kênh Telegram chỉ định.

    Nếu `TELEGRAM_TOKEN` hoặc `TELEGRAM_CHAT_ID` chưa được cấu hình, hàm
    sẽ in cảnh báo và không cố gắng gửi để tránh lỗi runtime.

    - alert_type: 'warning' hoặc 'alert' để điều chỉnh nội dung thông điệp.
    """
    if not TELEGRAM_TOKEN or TELEGRAM_TOKEN == "your_telegram_bot_token_here":
        print("Telegram: Token chưa được cấu hình, bỏ qua cảnh báo")
        return

    # Tùy chỉnh nội dung thông điệp theo mức độ cảnh báo
    if alert_type == "warning":
        msg = (
            f"⚠️ CẢNH BÁO Y TẾ\n\n"
            f"Bệnh nhân: {patient_id}\n"
            f"Nhịp tim: {hr} BPM\n"
            f"Oxy máu: {spo2}%\n"
            f"Rủi ro tim mạch: {risk}%\n\n"
            "⚠️ Mức độ: CẢNH BÁO - Cần theo dõi"
        )
    else:  # alert_type == "alert"
        msg = (
            f"🚨 BÁO ĐỘNG Y TẾ\n\n"
            f"Bệnh nhân: {patient_id}\n"
            f"Nhịp tim: {hr} BPM\n"
            f"Oxy máu: {spo2}%\n"
            f"Rủi ro tim mạch: {risk}%\n\n"
            "🚨 Mức độ: BÁO ĐỘNG - CẦN CAN THIỆP NGAY!"
        )

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": msg}
    try:
        requests.post(url, json=payload, timeout=5)
        print(f"Telegram: {alert_type.upper()} đã được gửi thành công")
    except Exception as e:
        print(f"Lỗi Telegram: {e}")