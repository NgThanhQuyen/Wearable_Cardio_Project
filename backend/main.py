from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import asyncio
import time
import threading
import os
from pydantic import BaseModel

from core import database, notifier, ai_engine, ai_chatbot

app = FastAPI(title="Wearable AI Cardio API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080", "http://localhost:3000"],  # Chỉ cho phép localhost
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

# Khởi tạo hệ thống khi startup
database.init_db()
ai_engine.load_resources()


def print_prediction_metrics(hr, spo2, risk_score, status_msg):
    """In ra metrics dự đoán ra terminal với định dạng đẹp"""
    # Xác định giai đoạn
    if risk_score < 30:
        stage = "🟢 NORMAL"
        color_code = "\033[92m"  # Green
    elif risk_score < 85:
        stage = "🟡 WARNING"
        color_code = "\033[93m"  # Yellow
    else:
        stage = "🔴 ALERT"
        color_code = "\033[91m"  # Red
    
    reset_code = "\033[0m"
    
    # In ra terminal
    print(f"\n{color_code}" + "="*70 + reset_code)
    print(f"{color_code} [PREDICTION] {status_msg}{reset_code}")
    print(f"{color_code}─" + "─"*68 + reset_code)
    print(f"{color_code} Vital Signs:  HR = {hr:.1f} bpm  |  SpO2 = {spo2:.1f}%{reset_code}")
    print(f"{color_code} Risk Score:   {risk_score:.1f}%{reset_code}")
    print(f"{color_code} Status:       {stage}{reset_code}")
    print(f"{color_code}" + "="*70 + reset_code)


def fire_and_forget_alert(hr_val, spo2_val, risk_val, alert_type="alert"):
    """Xử lý cảnh báo trong background thread để tránh block WebSocket"""
    try:
        patient_id = os.getenv("PATIENT_ID", "PT-2024-089")
        database.save_alert(patient_id, hr_val, spo2_val, risk_val)
        notifier.send_telegram_alert(patient_id, hr_val, spo2_val, risk_val, alert_type)
    except Exception as e:
        print(f"Error in background thread: {e}")


@app.get("/api/history")
def get_history():
    """Lấy lịch sử cảnh báo gần đây từ database"""
    return database.get_recent_history()


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    stream_mode = "IDLE"
    buffer = []
    last_alert_time = 0
    
    try:
        while True:
            # Ở chế độ IDLE, chỉ lắng nghe tín hiệu từ client mà không gửi dữ liệu
            if stream_mode == "IDLE":
                try:
                    data_rcv = await websocket.receive_text()
                    if data_rcv in ("TRIGGER_DANGER", "START_STREAM"):
                        stream_mode = "STREAMING"
                        print("System: Bắt đầu phát trực tiếp dữ liệu")
                        buffer = []  # Reset buffer
                    continue
                except WebSocketDisconnect:
                    raise
            
            # Chế độ STREAMING: phát dữ liệu từ file CSV
            for index, row in ai_engine.df.iterrows():
                # Kiểm tra tín hiệu dừng từ client
                try:
                    data_rcv = await asyncio.wait_for(websocket.receive_text(), timeout=0.01)
                    if data_rcv == "STOP_STREAM":
                        stream_mode = "IDLE"
                        print("System: Dừng phát trực tiếp")
                        break
                except asyncio.TimeoutError:
                    pass
                
                # Thêm điểm dữ liệu vào sliding window buffer
                data_point = row[ai_engine.FEATURES].values.tolist()
                buffer.append(data_point)
                
                risk_score = 0
                status_msg = "Đang thu thập dữ liệu..."
                
                # Khi buffer đạt 60 giây, chạy dự đoán rủi ro
                if len(buffer) == 60:
                    risk_score = ai_engine.predict_risk(buffer)
                    hr_val = float(round(row['HR'], 1))
                    spo2_val = float(round(row['SpO2'], 1))
                    risk_val = float(risk_score)
                    
                    # Phân loại 3 giai đoạn: bình thường, cảnh báo, báo động
                    if risk_score < 30:
                        status_msg = "BÌNH THƯỜNG - NORMAL"
                    elif risk_score < 85:
                        status_msg = "CẢNH BÁO - WARNING"
                        current_time = time.time()
                        
                        # Giới hạn cảnh báo 1 lần mỗi 10 giây để tránh spam
                        if current_time - last_alert_time > 10:
                            # Thực thi cảnh báo cảnh báo trong background thread
                            threading.Thread(target=fire_and_forget_alert, args=(hr_val, spo2_val, risk_val, "warning")).start()
                            last_alert_time = current_time
                    else:
                        status_msg = "BÁO ĐỘNG - ALERT"
                        current_time = time.time()
                        
                        # Giới hạn cảnh báo 1 lần mỗi 10 giây để tránh spam
                        if current_time - last_alert_time > 10:
                            # Thực thi cảnh báo báo động trong background thread
                            threading.Thread(target=fire_and_forget_alert, args=(hr_val, spo2_val, risk_val, "alert")).start()
                            last_alert_time = current_time
                    
                    # In metrics ra terminal
                    print_prediction_metrics(hr_val, spo2_val, risk_score, status_msg)
                    buffer.pop(0)  # Duy trì sliding window
                
                # Gửi dữ liệu đến frontend
                payload = {
                    "hr": row['HR'],
                    "spo2": row['SpO2'],
                    "risk_score": risk_score,
                    "status": status_msg
                }
                await websocket.send_json(payload)
                await asyncio.sleep(1)
                
    except WebSocketDisconnect:
        print("WebSocket: Client đã ngắt kết nối")
    except Exception as e:
        print(f"Lỗi WebSocket: {e}")


class ChatRequest(BaseModel):
    """Model yêu cầu cho endpoint tư vấn y tế"""
    question: str
    hr: float
    spo2: float


@app.post("/api/chat")
def chat_with_ai(request: ChatRequest):
    """Nhận tư vấn y tế từ AI chatbot dựa trên các dấu hiệu sinh tồn"""
    answer = ai_chatbot.get_medical_advice(request.question, request.hr, request.spo2)
    return {"answer": answer}

frontend_dir = os.path.join(os.path.dirname(__file__), '..', 'frontend')
if os.path.exists(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)