# CardioGuard — Hệ thống giám sát tim mạch thời gian thực

CardioGuard là một prototype dashboard web cho giám sát các chỉ số sinh tồn (như nhịp tim, SpO2, nhịp thở) từ dữ liệu mô phỏng hoặc thiết bị đeo. Hệ thống gồm:

- Backend: API REST + WebSocket (FastAPI) cung cấp luồng dữ liệu real-time và endpoint tư vấn AI.
- Frontend: giao diện dashboard (HTML/CSS/JS) hiển thị đồ thị, trạng thái cảnh báo và chat với trợ lý AI.

Mục tiêu: minh họa pipeline từ dữ liệu thời gian thực → mô hình dự báo → cảnh báo và hỗ trợ ra quyết định.

---

## Tính năng chính

- Hiển thị đồ thị nhịp tim & SpO2 thời gian thực (Chart.js).
- Mô hình ML (Keras/TensorFlow) dự đoán "risk score" theo cửa sổ 60s.
- WebSocket stream dữ liệu mẫu từ CSV (demo) hoặc từ thiết bị thực.
- Lưu lịch sử cảnh báo vào SQLite và gửi thông báo qua Telegram.
- Trợ lý AI (Groq) phản hồi tư vấn y tế ngắn gọn.

---

## Yêu cầu

- Python 3.8+
- Thư viện trong `backend/requirements.txt` (cài bằng `pip install -r backend/requirements.txt`).
- (Tùy chọn) Khóa Groq API và Telegram trong file `.env` để kích hoạt chatbot và notifier.

---

## Cài đặt & chạy nhanh

1. Tại thư mục gốc của project, tạo và kích hoạt môi trường ảo:

```powershell
python -m venv .venv
.venv\Scripts\activate
```

2. Cài dependencies:

```powershell
pip install -r backend/requirements.txt
```

3. (Tùy chọn) Tạo file `backend/.env` với các biến:

```ini
GROQ_API_KEY=sk_...
TELEGRAM_TOKEN=...
TELEGRAM_CHAT_ID=...
```

4. Chạy backend:

```powershell
cd backend
python main.py
# hoặc: uvicorn main:app --reload --port 8000
```

5. Mở `http://127.0.0.1:8000/` để truy cập dashboard.

---

## API chính

- `GET /` — trang dashboard (index.html)
- `GET /api/history` — lấy lịch sử cảnh báo (mặc định trả 10 bản ghi gần nhất)
- `POST /api/chat` — gửi câu hỏi tới trợ lý AI (xem schema trong `backend/main.py`)
- `ws://<host>/ws` — WebSocket stream dữ liệu real-time

---

## Vấn đề thường gặp & hướng giải quyết

- Nếu vào `http://127.0.0.1:8000/` mà vẫn thấy `404`: dừng tiến trình server cũ và khởi lại `python main.py` trong thư mục `backend`.
- Cảnh báo khi load Scaler (InconsistentVersionWarning): do scaler được sinh ra bằng một phiên bản scikit-learn khác; để an toàn nên rebuild scaler bằng cùng phiên bản scikit-learn đang dùng.
- Nếu Groq API key hoặc Telegram chưa cấu hình, các tính năng tương ứng sẽ bị bỏ qua nhưng server vẫn hoạt động.

---

## Tham khảo & phát triển tiếp

- Tổ chức code đơn giản để tiện phát triển: model/scaler nằm trong `backend/models/`, dữ liệu demo trong `backend/data/`.
- Muốn tích hợp thiết bị thật, thay nguồn dữ liệu WebSocket bằng input từ thiết bị/sensor.

---

## Tuyên bố

Ứng dụng minh họa này không phải là công cụ chẩn đoán y khoa. Mọi kết luận hoặc hành động lâm sàng phải do chuyên gia có thẩm quyền quyết định.
