# CardioGuard: Hệ Thống Giám Sát Tim Mạch AI & Cảnh Báo Real-Time 🫀

CardioGuard là một giải pháp Web Dashboard Giám sát Y khoa trực tuyến (Real-time), được thiết kế để theo dõi liên tục các chỉ số sinh tồn của bệnh nhân từ thiết bị đeo (Wearable Device). Hệ thống tích hợp mô hình học máy GRU (Deep Learning) để dự báo điểm số rủi ro tim mạch ngay lập tức và tự động gửi cảnh báo khẩn cấp qua Telegram, đi kèm một trợ lý AI lâm sàng hỗ trợ bác sĩ ra quyết định.

---

## 🌟 Tính Năng Nổi Bật

### 1. Giao Diện Dark Mode Y Khoa Premium
- Bố cục lưới **CSS Grid & Flexbox** hiện đại, tự động tương thích và co giãn hoàn hảo khi zoom trình duyệt (80%, 100%, 120%) hoặc truy cập bằng thiết bị di động/máy tính bảng.
- Phong cách **Glassmorphism** kính mờ xanh đen sâu thẳm mô phỏng màn hình siêu âm chuyên dụng trong bệnh viện.
- Hiệu ứng **Viền Neon Phát Sáng Nhấp Nháy (Pulsing Neon Borders)** tự động chuyển đổi đồng bộ theo 3 trạng thái lâm sàng:
  - **🟢 Bình thường (Normal - Xanh ngọc)**: Các chỉ số sinh tồn ổn định.
  - **🟡 Cảnh báo (Warning - Vàng hổ phách)**: Phát hiện chỉ số tim mạch biến động, nhấp nháy chậm.
  - **🔴 Báo động (Alarm - Đỏ neon)**: Rủi ro tim mạch vượt ngưỡng an toàn, nhấp nháy chu kỳ nhanh thu hút sự chú ý tức thì.

### 2. Quản Lý Luồng Dữ Liệu Sinh Động (State Management)
- **Trạng thái Chờ (Idle State)**: Tự động chạy biểu đồ giả lập dạng sóng điện tâm đồ (ECG) và nồng độ oxy trong máu (SpO2) trượt liên tục để giữ dashboard luôn sống động trước khi kết nối thiết bị thật. Hồ sơ bệnh nhân tạm ẩn để bảo mật.
- **Trạng thái Kết nối (Connected State)**: Khi bấm nút **KẾT NỐI THIẾT BỊ WEARABLE**, hệ thống dừng giả lập, chuyển sang nhận luồng dữ liệu thời gian thực từ WebSocket, giải phóng hồ sơ bệnh nhân thật và khóa nút bấm sang chế độ thu thập.

### 3. Trí Tuệ Nhân Tạo & Dự Báo Rủi Ro Tim Mạch
- Sử dụng mô hình mạng nơ-ron hồi quy **GRU (TensorFlow/Keras)** xử lý cửa sổ trượt (sliding window) 60 giây các dấu hiệu sinh tồn gồm: *Heart Rate (BPM), SpO2 (%), Respiratory Rate (RESP), Age, Sex, HRV* để tính toán phần trăm rủi ro đột quỵ/suy tim.
- **Trợ lý AI tư vấn y khoa (Cardio-AI)**: Tích hợp Groq API (`llama-3.3-70b-versatile`) cho phép bác sĩ trò chuyện, tham vấn ý kiến lâm sàng trực tiếp dựa trên dữ liệu sinh tồn thực tế của bệnh nhân.

### 4. Lưu Trữ & Thông Báo Khẩn Cấp
- Cơ sở dữ liệu **SQLite** lưu trữ tự động mọi bản ghi cảnh báo sinh tồn phục vụ tra cứu lịch sử.
- Tự động tích hợp gửi cảnh báo khẩn cấp (Warning / Alert) đến Telegram của bác sĩ trực hoặc phòng ban y tế ngay khi phát hiện rủi ro tim mạch cao.

---

## 🛠️ Công Nghệ Sử Dụng

### Frontend
- **Ngôn ngữ**: HTML5 (Semantic elements), CSS3 (Vanilla CSS Grid/Flexbox), Javascript (ES6+).
- **Thư viện**: [Chart.js](https://www.chartjs.org/) vẽ đồ thị sinh tồn, [Google Fonts](https://fonts.google.com/) (Orbitron & Inter).

### Backend
- **Framework**: [FastAPI](https://fastapi.tiangolo.com/) (Python) hỗ trợ REST API và luồng WebSocket real-time.
- **Server**: [Uvicorn](https://www.uvicorn.org/).
- **AI/ML**: TensorFlow, Keras, Scikit-learn, Pandas, Numpy.
- **LLM API**: Groq Cloud SDK.
- **Database**: SQLite3.

---

## 📂 Cấu Trúc Thư Mục Dự Án

```text
Wearable_Cardio_Project/
├── backend/
│   ├── core/
│   │   ├── __init__.py
│   │   ├── ai_chatbot.py      # Xử lý chatbot tư vấn (Groq LLaMA)
│   │   ├── ai_engine.py       # Tải model GRU, xử lý dữ liệu và dự đoán rủi ro
│   │   ├── database.py        # Khởi tạo và truy vấn SQLite (history.db)
│   │   └── notifier.py        # Gửi cảnh báo khẩn cấp đến Telegram Bot
│   ├── data/
│   │   └── patient_demo_stream.csv  # Dữ liệu mô phỏng luồng sinh tồn thực tế
│   ├── models/
│   │   ├── cardio_GRU_model.h5      # Model GRU dự báo rủi ro tim mạch
│   │   └── scaler.pkl               # Scaler chuẩn hóa dữ liệu sinh tồn
│   ├── main.py                # Điểm khởi chạy API FastAPI & WebSocket
│   ├── requirements.txt       # Danh sách thư viện Python cần thiết
│   ├── .env                   # Khóa API & cấu hình bảo mật
│   └── history.db             # File cơ sở dữ liệu SQLite nội bộ
├── frontend/
│   ├── index.html             # Bố cục giao diện Dashboard y tế
│   ├── style.css              # Thiết kế giao diện Dark Mode, Grid, và hiệu ứng Neon
│   └── script.js              # Logic kết nối WebSocket, vẽ đồ thị, điều khiển UI
└── README.md                  # Hướng dẫn sử dụng hệ thống
```

---

## 🚀 Hướng Dẫn Cài Đặt & Chạy Hệ Thống

> [!IMPORTANT]
> Hãy chắc chắn máy tính của bạn đã cài đặt **Python 3.8+** và trình duyệt web hiện đại (Chrome, Edge, Firefox).

### Bước 1: Thiết Lập Cấu Hình Backend `.env`
Di chuyển vào thư mục `backend/`, copy file `.env.example` thành `.env` và điền đầy đủ các khóa API:
```ini
# Khóa API Groq để chạy trợ lý AI Chatbot
GROQ_API_KEY=gsk_your_groq_api_key_here

# Thông tin Telegram (Tùy chọn để nhận tin nhắn cảnh báo)
TELEGRAM_TOKEN=your_telegram_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
```

### Bước 2: Cài Đặt Môi Trường & Thư Viện Python
Mở terminal tại thư mục gốc dự án và thực hiện các lệnh sau:

1. **Khởi tạo môi trường ảo Python**:
   ```bash
   python -m venv .venv
   ```
2. **Kích hoạt môi trường ảo**:
   - **Windows**:
     ```powershell
     .venv\Scripts\activate
     ```
   - **macOS/Linux**:
     ```bash
     source .venv/bin/activate
     ```
3. **Cài đặt các gói thư viện**:
   ```bash
   pip install -r backend/requirements.txt
   ```

### Bước 3: Khởi Chạy Server Backend
Chạy lệnh sau tại thư mục `backend/` để khởi động máy chủ Uvicorn:
```bash
python main.py
```
Hoặc khởi động bằng Uvicorn reload:
```bash
uvicorn main:app --reload --port 8000
```
Khi chạy thành công, terminal sẽ hiển thị:
```text
INFO:     Uvicorn running on http://127.0.0.1:8000
Database: Sẵn sàng
AI Engine: Đang tải model và scaler...
AI Engine: Đang tải bộ dữ liệu..
```

### Bước 4: Chạy Giao Diện Frontend
Copy link: http://127.0.0.1:8000 và dán vào google để trãi nghiệm hệ thống

---

## 🏥 Hướng Dẫn Sử Dụng & Chu Kỳ Vận Hành

1. **Trạng thái Chờ**: Dashboard hiển thị hai đồ thị nhịp tim/SpO2 mô phỏng liên tục nhấp nhô nhẹ. Phần hồ sơ bệnh nhân hiển thị bảng chờ tải thông tin.
2. **Kết nối Wearable**: Nhấn nút **KẾT NỐI THIẾT BỊ WEARABLE**.
   - Biểu đồ sẽ được xóa sạch và nạp lại luồng dữ liệu thời gian thực được stream từ file CSV thông qua WebSocket.
   - Thẻ hồ sơ bệnh nhân **PT-2024-089** xuất hiện.
   - Nút bấm chuyển trạng thái vô hiệu hóa.
3. **Phân tích lâm sàng & Đổi màu neon**:
   - Trong 60 giây đầu tiên, hệ thống sẽ tích lũy dữ liệu cửa sổ trượt. Trạng thái hiển thị viền neon màu xanh ngọc (Bình thường).
   - Từ giây thứ 60 trở đi, mô hình GRU bắt đầu trả về điểm số rủi ro tim mạch mỗi giây. Màu sắc viền của 4 bảng điều khiển chính trên dashboard sẽ tự động đồng bộ thay đổi theo ngưỡng rủi ro thực tế của bệnh nhân (Xanh lá / Vàng nhấp nháy / Đỏ chớp nhanh).
4. **Tương tác Chatbot AI**: Bác sĩ có thể nhập câu hỏi (ví dụ: *"Bệnh nhân nhịp tim cao kèm tiền sử huyết áp cao nên dùng thuốc gì?"*) rồi nhấn **Gửi** hoặc phím **Enter**. Trợ lý AI sẽ thu thập chỉ số hiện tại trên đồ thị và phản hồi lời khuyên lâm sàng.
5. **Xem lịch sử**: Nhấn nút **Xem Lịch Sử Cảnh Báo** để hiển thị bảng lịch sử các lần cảnh báo nguy cơ cao được lưu trữ trong SQLite.

---

## 🔒 Tuyên Bố Miễn Trừ Trách Nhiệm (Disclaimer)
> [!WARNING]
> Ứng dụng này chỉ là một mô hình giả lập nghiên cứu và hỗ trợ y tế tích hợp AI. Mọi phân tích và lời khuyên của AI chatbot chỉ mang tính chất tham khảo định hướng. Quyết định điều trị lâm sàng cuối cùng bắt buộc phải được thực hiện và chịu trách nhiệm hoàn toàn bởi bác sĩ chuyên môn có chứng chỉ hành nghề.
