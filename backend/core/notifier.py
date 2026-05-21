import requests
import os
from dotenv import load_dotenv

# Tải biến môi trường từ tệp .env
load_dotenv()

# Lấy thông tin xác thực Telegram từ biến môi trường
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_telegram_alert(patient_id, hr, spo2, risk, alert_type="alert"):
    """Gửi thông báo cảnh báo y tế qua Telegram"""
    if not TELEGRAM_TOKEN or TELEGRAM_TOKEN == "your_telegram_bot_token_here":
        print("Telegram: Token chưa được cấu hình, bỏ qua cảnh báo")
        return
    
    # Tạo message khác nhau cho từng loại cảnh báo
    if alert_type == "warning":
        msg = f"⚠️ CẢNH BÁO Y TẾ\n\nBệnh nhân: {patient_id}\nNhịp tim: {hr} BPM\nOxy máu: {spo2}%\nRủi ro tim mạch: {risk}%\n\n⚠️ Mức độ: CẢNH BÁO - Cần theo dõi"
    else:  # alert_type == "alert"
        msg = f"🚨 BÁO ĐỘNG Y TẾ\n\nBệnh nhân: {patient_id}\nNhịp tim: {hr} BPM\nOxy máu: {spo2}%\nRủi ro tim mạch: {risk}%\n\n🚨 Mức độ: BÁO ĐỘNG - CẦN CAN THIỆP NGAY!"
    
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": msg}
    try:
        requests.post(url, json=payload, timeout=5)
        print(f"Telegram: {alert_type.upper()} đã được gửi thành công")
    except Exception as e:
        print(f"Lỗi Telegram: {e}")