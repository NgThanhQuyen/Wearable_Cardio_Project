from groq import Groq
import os
from dotenv import load_dotenv

# Nạp biến môi trường chứa khóa Groq
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, '.env'))

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

# Khởi tạo client Groq để gọi model chat khi có khóa hợp lệ.
client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None


def get_medical_advice(question: str, current_hr: float, current_spo2: float) -> str:
    """
    Gửi prompt đến LLM (Groq) để nhận lời khuyên y tế ngắn gọn.

    Hàm xây dựng prompt có ngữ cảnh kèm theo các chỉ số sinh tồn hiện tại,
    đặt giới hạn về độ dài phản hồi và ghi chú kết thúc để nhắc người đọc
    rằng đây chỉ là hỗ trợ AI.
    """
    if client is None:
        return (
            "Tính năng tư vấn AI hiện chưa được cấu hình vì thiếu GROQ_API_KEY. "
            "Hãy bổ sung biến môi trường này để bật chatbot."
        )

    prompt = (
        "Bạn là một trợ lý y tế ảo chuyên về tim mạch.\n"
        f"Bệnh nhân hiện có các chỉ số sống:\n- Nhịp tim: {current_hr} BPM\n- SpO2: {current_spo2}%\n\n"
        f"Trả lời câu hỏi: \"{question}\"\n\n"
        "Yêu cầu: 1) Trả lời ngắn gọn (tối đa 3 câu). 2) Nếu có dấu hiệu nguy hiểm, nêu rõ chỉ số nào. "
        "3) Kết thúc bằng: 'Đây chỉ là hướng dẫn AI. Cần đánh giá lâm sàng chuyên gia.'"
    )

    print(f"[ChatBot] Gửi request tới Groq API: {question}")
    print(f"[ChatBot] Model: {GROQ_MODEL}")
    print(f"[ChatBot] Vital Signs - HR: {current_hr} BPM, SpO2: {current_spo2}%")

    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
    )
    print(f"[ChatBot] Nhận response thành công từ Groq API")
    return response.choices[0].message.content
