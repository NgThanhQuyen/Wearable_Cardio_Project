import os
# Đặt trước tương thích Keras (nếu cần với một số build nhất định)
os.environ["TF_USE_LEGACY_KERAS"] = "1"

import pickle
import numpy as np
import pandas as pd
from tensorflow.keras.models import load_model
from tensorflow import keras

# Thư mục gốc của module core (hai cấp so với file này)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Biến toàn cục chứa model, scalers và bộ dữ liệu stream mẫu
model = None
scaler_dyn = None  # Scaler cho dữ liệu động (các chỉ số theo thời gian)
scaler_stat = None # Scaler cho dữ liệu tĩnh (tuổi, giới tính...)
df = None

# Định nghĩa tên các feature tương ứng với model Multi-Input
DYN_FEATURES = ['HR', 'SpO2', 'RESP', 'HRV']
STAT_FEATURES = ['Age', 'Sex']

# Dữ liệu tĩnh giả lập (demo) - nếu muốn tích hợp hồ sơ thực tế hãy thay đổi
PATIENT_AGE = 55
PATIENT_SEX = 1  # 1 = Nam, 0 = Nữ


def load_resources():
    """
    Tải model, scalers và bộ dữ liệu mô phỏng vào bộ nhớ khi khởi động.

    - Nếu model thực tế không thể tải (ví dụ file thiếu hoặc phiên bản khác),
      hàm sẽ tạo một mô hình giả (dummy) để tránh crash toàn bộ server.
    - Lưu ý: khi unpickle scaler từ phiên bản scikit-learn khác có thể phát sinh
      cảnh báo `InconsistentVersionWarning` — điều này là cảnh báo an toàn,
      tuy nhiên nên rebuild/serialize lại scaler với cùng phiên bản scikit-learn
      để đảm bảo tính nhất quán lâu dài.
    """
    global model, scaler_dyn, scaler_stat, df

    print("AI Engine: Đang tải model Multi-Input và Scalers...")
    try:
        # Load model với compile=False để tránh các khác biệt optimizer/version
        model_path = os.path.join(BASE_DIR, 'models', 'cardio_CNNLSTM_model.h5')
        model = load_model(model_path, compile=False)
        print("-> Tải Model thành công!")
    except Exception as e:
        # Không dừng server nếu model thực tế bị thiếu/không tương thích
        print(f"Cảnh báo: Không thể tải model - {e}")
        print("-> Tạo mô hình giả (fallback) để tránh crash khi đang phát triển")
        input_dyn = keras.Input(shape=(60, 4))
        input_stat = keras.Input(shape=(2,))
        x = keras.layers.Flatten()(input_dyn)
        merged = keras.layers.Concatenate()([x, input_stat])
        x = keras.layers.Dense(16, activation='relu')(merged)
        outputs = keras.layers.Dense(1, activation='sigmoid')(x)
        model = keras.Model(inputs=[input_dyn, input_stat], outputs=outputs)

    # Tải 2 bộ scaler dùng để chuẩn hóa input trước khi vào model
    try:
        with open(os.path.join(BASE_DIR, 'models', 'scaler_dyn.pkl'), 'rb') as f:
            scaler_dyn = pickle.load(f)
        with open(os.path.join(BASE_DIR, 'models', 'scaler_stat.pkl'), 'rb') as f:
            scaler_stat = pickle.load(f)
        print("-> Tải 2 Scalers thành công!")
    except Exception as e:
        print(f"Lỗi tải Scaler: {e}. Vui lòng kiểm tra lại thư mục models/")

    # Tải dữ liệu mô phỏng luồng stream (CSV)
    print("AI Engine: Đang tải bộ dữ liệu Stream..")
    df = pd.read_csv(os.path.join(BASE_DIR, 'data', 'patient_demo_stream.csv'))


def predict_risk(window_buffer):
    """
    Dự đoán điểm rủi ro dựa trên cửa sổ dữ liệu động truyền vào.

    - `window_buffer` là một list chứa N dòng dữ liệu (mỗi dòng tương ứng 1 giây),
      mỗi dòng có các giá trị theo thứ tự `DYN_FEATURES`.
    - Hàm chuẩn hóa dữ liệu bằng `scaler_dyn`/`scaler_stat` rồi đưa vào model.
    - Trả về điểm rủi ro dạng phần trăm (float, có 1 chữ số thập phân).
    """
    # Chuyển list -> DataFrame để scaler hoạt động ổn định và tránh một số warning
    window_df = pd.DataFrame(window_buffer, columns=DYN_FEATURES)
    window_scaled = scaler_dyn.transform(window_df)
    X_input_dyn = np.expand_dims(window_scaled, axis=0)

    # Chuẩn hóa các feature tĩnh (demo) trước khi đưa vào model
    static_df = pd.DataFrame([[PATIENT_AGE, PATIENT_SEX]], columns=STAT_FEATURES)
    X_input_stat = scaler_stat.transform(static_df)

    # Dự đoán
    pred = model.predict([X_input_dyn, X_input_stat], verbose=0)[0][0]
    risk_score = round(float(pred) * 100, 1)
    return risk_score