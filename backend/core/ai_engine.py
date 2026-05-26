import os
import pickle
import numpy as np
import pandas as pd
from dotenv import load_dotenv

try:
    import mlflow
except Exception:
    mlflow = None

try:
    from tensorflow.keras.models import load_model
    from tensorflow import keras
    from tensorflow.keras.layers import InputLayer as KerasInputLayer
except Exception:
    from keras.models import load_model
    import keras
    from keras.layers import InputLayer as KerasInputLayer


class CompatibleInputLayer(KerasInputLayer):
    def __init__(self, *args, batch_shape=None, batch_input_shape=None, **kwargs):
        resolved_batch_shape = batch_shape if batch_shape is not None else batch_input_shape
        if resolved_batch_shape is not None:
            resolved_batch_shape = tuple(resolved_batch_shape)
            if len(resolved_batch_shape) >= 1:
                kwargs.setdefault("batch_size", resolved_batch_shape[0])
            if len(resolved_batch_shape) > 1:
                kwargs.setdefault("shape", tuple(resolved_batch_shape[1:]))
        super().__init__(*args, **kwargs)

# Thư mục gốc của module core (hai cấp so với file này)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Nạp biến môi trường từ backend/.env nếu có
load_dotenv(os.path.join(BASE_DIR, '.env'))

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


def _env_flag(name: str, default: str = "false") -> bool:
    return os.getenv(name, default).strip().lower() in ("1", "true", "yes", "on")


def _configure_mlflow_tracking():
    """Thiết lập MLflow tracking URI và auth cho DagsHub."""
    tracking_uri = os.getenv("MLFLOW_TRACKING_URI", "").strip()
    username = os.getenv("MLFLOW_TRACKING_USERNAME", "").strip()
    password = os.getenv("MLFLOW_TRACKING_PASSWORD", "").strip()

    if not tracking_uri:
        raise ValueError("Thiếu MLFLOW_TRACKING_URI")

    os.environ["MLFLOW_TRACKING_URI"] = tracking_uri
    if username:
        os.environ["MLFLOW_TRACKING_USERNAME"] = username
    if password:
        os.environ["MLFLOW_TRACKING_PASSWORD"] = password

    mlflow.set_tracking_uri(tracking_uri)


def _load_model_from_registry_uri(model_uri: str):
    """
    Nạp model trực tiếp từ MLflow Model Registry URI (ví dụ: models:/name/latest).
    Trả về đối tượng model đã nằm trong RAM.
    """
    if mlflow is None:
        raise ImportError("Chưa cài mlflow. Hãy cài dependency hoặc tắt USE_MLFLOW.")

    if not model_uri:
        raise ValueError("Thiếu MLFLOW_MODEL_URI")

    _configure_mlflow_tracking()

    load_errors = []

    # Ưu tiên flavor Keras trước
    try:
        return mlflow.keras.load_model(model_uri)
    except Exception as e:
        load_errors.append(f"mlflow.keras.load_model lỗi: {e}")

    # Thử flavor TensorFlow
    try:
        return mlflow.tensorflow.load_model(model_uri)
    except Exception as e:
        load_errors.append(f"mlflow.tensorflow.load_model lỗi: {e}")

    # Fallback cuối: tải artifact về local rồi dùng Keras load_model như pipeline hiện tại
    cache_dir = os.path.join(BASE_DIR, "models", "_mlflow_registry_cache")
    os.makedirs(cache_dir, exist_ok=True)
    local_path = mlflow.artifacts.download_artifacts(artifact_uri=model_uri, dst_path=cache_dir)

    if os.path.isdir(local_path):
        h5_candidates = []
        for root, _, files in os.walk(local_path):
            for file_name in files:
                if file_name.lower().endswith((".h5", ".keras")):
                    h5_candidates.append(os.path.join(root, file_name))

        if h5_candidates:
            return load_model(
                h5_candidates[0],
                compile=False,
                custom_objects={"InputLayer": CompatibleInputLayer},
            )

        raise RuntimeError(
            "Không tìm thấy file .h5/.keras trong artifact model registry. "
            + " | ".join(load_errors)
        )

    return load_model(
        local_path,
        compile=False,
        custom_objects={"InputLayer": CompatibleInputLayer},
    )


def _download_mlflow_artifacts(download_model: bool = True):
    """
    Tải artifacts model/scaler từ MLflow Tracking Server (DagsHub).

    Trả về tuple (model_path, scaler_dyn_path, scaler_stat_path) nếu thành công.
    Ném exception nếu thiếu cấu hình hoặc tải thất bại.
    """
    if mlflow is None:
        raise ImportError("Chưa cài mlflow. Hãy cài dependency hoặc tắt USE_MLFLOW.")

    run_id = os.getenv("MLFLOW_RUN_ID", "").strip()

    scaler_dyn_artifact = os.getenv("MLFLOW_SCALER_DYN_ARTIFACT_PATH", "scaler_dyn.pkl").strip()
    scaler_stat_artifact = os.getenv("MLFLOW_SCALER_STAT_ARTIFACT_PATH", "scaler_stat.pkl").strip()

    if not run_id:
        raise ValueError("Thiếu MLFLOW_RUN_ID")

    _configure_mlflow_tracking()

    cache_dir = os.path.join(BASE_DIR, "models", "_mlflow_cache", run_id)
    os.makedirs(cache_dir, exist_ok=True)

    model_path = None
    if download_model:
        model_artifact = "cardio_CNNLSTM_model.h5"
        model_path = mlflow.artifacts.download_artifacts(
            run_id=run_id,
            artifact_path=model_artifact,
            dst_path=cache_dir,
        )
    scaler_dyn_path = mlflow.artifacts.download_artifacts(
        run_id=run_id,
        artifact_path=scaler_dyn_artifact,
        dst_path=cache_dir,
    )
    scaler_stat_path = mlflow.artifacts.download_artifacts(
        run_id=run_id,
        artifact_path=scaler_stat_artifact,
        dst_path=cache_dir,
    )

    return model_path, scaler_dyn_path, scaler_stat_path


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

    use_mlflow = _env_flag("USE_MLFLOW", "false")
    model_path = os.path.join(BASE_DIR, 'models', 'cardio_CNNLSTM_model.h5')
    scaler_dyn_path = os.path.join(BASE_DIR, 'models', 'scaler_dyn.pkl')
    scaler_stat_path = os.path.join(BASE_DIR, 'models', 'scaler_stat.pkl')

    if use_mlflow:
        model_uri = os.getenv("MLFLOW_MODEL_URI", "").strip()
        run_id = os.getenv("MLFLOW_RUN_ID", "").strip()

        if model_uri:
            try:
                print(f"AI Engine: USE_MLFLOW=true -> Đang nạp model từ Registry URI: {model_uri}")
                model = _load_model_from_registry_uri(model_uri)
                print("-> Tải model từ Registry thành công (đã nạp vào RAM)")
            except Exception as e:
                print(f"Cảnh báo: Không thể tải model từ Registry URI - {e}")
                print("-> Fallback sang MLflow run artifact/local model")

        if run_id:
            try:
                if model is None:
                    print("AI Engine: USE_MLFLOW=true -> Đang tải model + scalers từ DagsHub MLflow run...")
                else:
                    print("AI Engine: USE_MLFLOW=true -> Đang tải scalers từ DagsHub MLflow run...")

                downloaded_model_path, scaler_dyn_path, scaler_stat_path = _download_mlflow_artifacts(
                    download_model=(model is None)
                )

                if model is None and downloaded_model_path:
                    model_path = downloaded_model_path

                print(f"-> Tải artifacts MLflow thành công (run_id={run_id})")
            except Exception as e:
                print(f"Cảnh báo: Không tải được artifacts từ MLflow - {e}")
                print("-> Fallback sang file local trong thư mục models/")
        else:
            print("AI Engine: Không có MLFLOW_RUN_ID -> dùng scaler local trong thư mục models/")

    if model is None:
        try:
            # Load model với compile=False để tránh các khác biệt optimizer/version
            model = load_model(
                model_path,
                compile=False,
                custom_objects={"InputLayer": CompatibleInputLayer},
            )
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
        with open(scaler_dyn_path, 'rb') as f:
            scaler_dyn = pickle.load(f)
        with open(scaler_stat_path, 'rb') as f:
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