from groq import Groq
import os
from dotenv import load_dotenv

# Tải biến môi trường từ tệp .env
load_dotenv()

# Lấy khóa API từ biến môi trường
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY không tìm thấy trong tệp .env")

# Cấu hình Groq client
client = Groq(api_key=GROQ_API_KEY)

def get_medical_advice(question: str, current_hr: float, current_spo2: float) -> str:
    """Tạo tư vấn y tế từ AI dựa trên các chỉ số sống của bệnh nhân và câu hỏi"""
    
    # Tạo prompt nhận thức ngữ cảnh với các dấu hiệu sinh tồn hiện tại
    prompt = f"""Bạn là một trợ lý y tế ảo chuyên về tim mạch.
Bệnh nhân hiện có các chỉ số sống:
- Nhịp tim: {current_hr} BPM
- SpO2: {current_spo2}%

Trả lời câu hỏi này: "{question}"

Yêu cầu:
1. Phản hồi ngắn gọn (tối đa 3 câu).
2. Nêu rõ các chỉ số nguy hiểm nếu có.
3. Kết thúc: "Đây chỉ là hướng dẫn AI. Cần đánh giá lâm sàng chuyên gia."
4. KHÔNG gọi người hỏi là "bác sĩ"."""
    
    print(f"[ChatBot] Gửi request tới Groq API: {question}")
    print(f"[ChatBot] Model: {GROQ_MODEL}")
    print(f"[ChatBot] Vital Signs - HR: {current_hr} BPM, SpO2: {current_spo2}%")
    
    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
    )
    print(f"[ChatBot] Nhận response thành công từ Groq API")
    return response.choices[0].message.content
