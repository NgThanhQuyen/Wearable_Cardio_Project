import os
import pickle
import numpy as np
import pandas as pd
from keras.models import load_model

# Lấy thư mục gốc dự án
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Các biến toàn cục cho model và dữ liệu
model = None
scaler = None
df = None
FEATURES = ['HR', 'SpO2', 'RESP', 'Age', 'Sex', 'HRV']

def load_resources():
    """Tải model đã huấn luyện, scaler và bộ dữ liệu kiểm tra vào bộ nhớ"""
    global model, scaler, df
    
    print("AI Engine: Đang tải model và scaler...")
    try:
        model = load_model(os.path.join(BASE_DIR, 'models', 'cardio_GRU_model.h5'), safe_mode=False)
    except Exception as e:
        print(f"Cảnh báo: Không thể tải model - {e}")
        print("Tạo model giả cho việc kiểm tra...")
        from tensorflow import keras
        inputs = keras.Input(shape=(60, 6))
        x = keras.layers.Flatten()(inputs)
        x = keras.layers.Dense(32, activation='relu')(x)
        outputs = keras.layers.Dense(1, activation='sigmoid')(x)
        model = keras.Model(inputs=inputs, outputs=outputs)
    
    with open(os.path.join(BASE_DIR, 'models', 'scaler.pkl'), 'rb') as f:
        scaler = pickle.load(f)
        
    print("AI Engine: Đang tải bộ dữ liệu..")
    df = pd.read_csv(os.path.join(BASE_DIR, 'data', 'patient_demo_stream.csv'))

def predict_risk(window_buffer):
    """Xử lý cửa sổ 60 giây các dấu hiệu sinh tồn và trả về phần trăm rủi ro"""
    window_data = np.array(window_buffer)
    window_scaled = scaler.transform(window_data)
    X_input = np.expand_dims(window_scaled, axis=0)
    
    pred = model.predict(X_input, verbose=0)[0][0]
    risk_score = round(float(pred) * 100, 1)
    return risk_score