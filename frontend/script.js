// --- KHỞI TẠO CÁC PHẦN TỬ UI ---
const btnConnect = document.getElementById('btn-connect');
const btnHistory = document.getElementById('btn-history');
const btnCloseModal = document.getElementById('close-modal');
const historyModal = document.getElementById('history-modal');
const tableBody = document.getElementById('history-table-body');

const alertBox = document.getElementById('alert-box');
const riskScoreEl = document.getElementById('risk-score');
const statusTextEl = document.getElementById('status-text');
const botAlert = document.getElementById('bot-alert');

const chatInput = document.getElementById('chat-input');
const chatSendBtn = document.getElementById('chat-send-btn');
const chatWindow = document.getElementById('chat-window');
const systemTimeEl = document.getElementById('system-time');

// Các panel để thay đổi màu viền neon đồng bộ theo trạng thái cảnh báo
const panels = [
    document.getElementById('alert-box'),
    document.getElementById('panel-patient'),
    document.getElementById('panel-charts'),
    document.getElementById('panel-chatbot')
];

// Trạng thái hệ thống
let isStreaming = false;
let idleIntervalId = null;
let idleTick = 0;
const maxDataPoints = 60; // Hiển thị 60 giây trên màn hình

// --- CẬP NHẬT ĐỒNG HỒ HỆ THỐNG ---
function updateClock() {
    const now = new Date();
    const timeString = now.toLocaleTimeString('vi-VN', { hour12: false });
    if (systemTimeEl) {
        systemTimeEl.innerText = `${timeString} | ONLINE`;
    }
}
setInterval(updateClock, 1000);
updateClock();

// --- CẤU HÌNH CHART.JS CHO DARK THEME ---
const hrCtx = document.getElementById('hrChart').getContext('2d');
const spo2Ctx = document.getElementById('spo2Chart').getContext('2d');

const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    animation: false, // Tắt animation để vẽ real-time mượt mà, không giật lag
    plugins: {
        legend: {
            labels: {
                color: '#e2e8f0', // Chữ trắng sáng cho legend
                font: {
                    family: "'Inter', sans-serif",
                    size: 11,
                    weight: 'bold'
                }
            }
        }
    },
    scales: {
        x: {
            display: false // Ẩn trục X thời gian
        },
        y: {
            grid: {
                color: 'rgba(255, 255, 255, 0.05)', // Grid line mờ nhẹ
                drawBorder: false
            },
            ticks: {
                color: '#94a3b8', // Màu chữ trục Y xám xanh dễ nhìn
                font: {
                    family: "'Orbitron', monospace",
                    size: 11
                }
            }
        }
    }
};

// Khởi tạo biểu đồ Nhịp tim (Heart Rate)
const hrChart = new Chart(hrCtx, {
    type: 'line',
    data: {
        labels: Array(maxDataPoints).fill(''),
        datasets: [{
            label: 'Heart Rate (BPM)',
            borderColor: '#ef4444', // Màu đỏ neon
            backgroundColor: 'rgba(239, 68, 68, 0.06)',
            data: Array(maxDataPoints).fill(null),
            fill: true,
            tension: 0.35,
            borderWidth: 2,
            pointRadius: 0 // Ẩn các điểm chấm tròn để đường mượt
        }]
    },
    options: {
        ...chartOptions,
        scales: {
            ...chartOptions.scales,
            y: {
                ...chartOptions.scales.y,
                min: 40,
                max: 180
            }
        }
    }
});

// Khởi tạo biểu đồ nồng độ oxy trong máu (SpO2)
const spo2Chart = new Chart(spo2Ctx, {
    type: 'line',
    data: {
        labels: Array(maxDataPoints).fill(''),
        datasets: [{
            label: 'SpO2 (%)',
            borderColor: '#06b6d4', // Màu cyan neon
            backgroundColor: 'rgba(6, 182, 212, 0.06)',
            data: Array(maxDataPoints).fill(null),
            fill: true,
            tension: 0.35,
            borderWidth: 2,
            pointRadius: 0
        }]
    },
    options: {
        ...chartOptions,
        scales: {
            ...chartOptions.scales,
            y: {
                ...chartOptions.scales.y,
                min: 75,
                max: 100
            }
        }
    }
});

// --- QUẢN LÝ TRẠNG THÁI MÀU NEON ---
function setClinicalVisualState(state) {
    // state: 'normal' (xanh), 'warning' (vàng), 'alarm' (đỏ)
    panels.forEach(p => {
        if (!p) return;
        p.classList.remove('state-normal', 'state-warning', 'state-alarm');
        p.classList.add(`state-${state}`);
    });
}

// Khởi tạo trạng thái ban đầu (Normal - Xanh nhẹ)
setClinicalVisualState('normal');
riskScoreEl.innerText = '--';
statusTextEl.innerText = 'Chờ kết nối thiết bị wearable...';

// --- MÔ PHỎNG SÓNG SINH TỒN (IDLE STATE ANIMATION) ---
// Mẫu sóng ECG nhịp tim giả lập (nhấp nhô nhịp tim rà soát)
const ecgTemplate = [72, 72, 71, 70, 105, 52, 76, 78, 72, 72];

function initIdleAnimation() {
    // Điền trước 60 điểm dữ liệu giả lập ban đầu
    const hrData = hrChart.data.datasets[0].data;
    const spo2Data = spo2Chart.data.datasets[0].data;
    
    for (let i = 0; i < maxDataPoints; i++) {
        hrData[i] = ecgTemplate[i % ecgTemplate.length] + Math.random() * 0.4;
        spo2Data[i] = 98.4 + Math.sin(i * 0.15) * 0.25 + Math.random() * 0.1;
    }
    hrChart.update();
    spo2Chart.update();

    // Cập nhật sóng trượt từ phải qua trái liên tục
    idleIntervalId = setInterval(() => {
        idleTick++;
        
        // Tạo điểm tiếp theo
        const nextHR = ecgTemplate[idleTick % ecgTemplate.length] + Math.random() * 0.4;
        const nextSpO2 = 98.4 + Math.sin(idleTick * 0.15) * 0.25 + Math.random() * 0.1;
        
        // Đẩy vào cuối và trượt phần tử đầu
        hrData.push(nextHR);
        hrData.shift();
        
        spo2Data.push(nextSpO2);
        spo2Data.shift();
        
        // Vẽ lại đồ thị
        hrChart.update();
        spo2Chart.update();
    }, 150); // Mỗi 150ms trượt 1 điểm để tạo chuyển động nhịp nhàng
}

// Bắt đầu chạy sóng giả lập ngay khi load web
initIdleAnimation();

// --- XỬ LÝ LƯỢNG DỮ LIỆU WEBSOCKET (REAL-TIME STREAM) ---
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onmessage = function(event) {
    if (!isStreaming) return; // Chỉ xử lý khi đã click kết nối
    
    const data = JSON.parse(event.data);
    
    // Đẩy dữ liệu Heart Rate thật
    let hrData = hrChart.data.datasets[0].data;
    hrData.push(data.hr);
    hrData.shift();
    hrChart.update();

    // Đẩy dữ liệu SpO2 thật
    let spo2Data = spo2Chart.data.datasets[0].data;
    spo2Data.push(data.spo2);
    spo2Data.shift();
    spo2Chart.update();

    // Cập nhật điểm số rủi ro AI & màu viền neon
    if (data.risk_score !== undefined) {
        // Chỉ số rủi ro tích lũy khi đủ 60 giây dữ liệu
        if (data.risk_score > 0) {
            riskScoreEl.innerText = Math.round(data.risk_score) + '%';
        } else {
            riskScoreEl.innerText = '0%';
        }
        statusTextEl.innerText = data.status;

        // Phân loại 3 mức độ và đổi màu viền neon toàn bộ hệ thống
        if (data.risk_score < 30) {
            // Trạng thái bình thường - Xanh neon ổn định
            setClinicalVisualState('normal');
            botAlert.style.display = "none";
        } else if (data.risk_score < 85) {
            // Trạng thái cảnh báo - Vàng hổ phách nhấp nháy chậm
            setClinicalVisualState('warning');
            botAlert.style.display = "block";
            botAlert.className = "chat-message bot alert-message";
            // Đổi text cảnh báo bot phù hợp mức Warning
            botAlert.querySelector('p').innerText = "CẢNH BÁO: Phát hiện chỉ số tim mạch có biến động bất thường. Đang theo dõi sát sao.";
        } else {
            // Trạng thái báo động nguy hiểm - Đỏ neon nhấp nháy nhanh
            setClinicalVisualState('alarm');
            botAlert.style.display = "block";
            botAlert.className = "chat-message bot alert-message";
            // Đổi text cảnh báo bot phù hợp mức Alarm
            botAlert.querySelector('p').innerText = "BÁO ĐỘNG KHẨN CẤP: Nhịp tim tăng vọt và SpO2 giảm đột ngột! Đề nghị bác sĩ can thiệp ngay lập tức!";
        }
    }
};

ws.onerror = function(err) {
    console.error("Lỗi WebSocket: ", err);
    statusTextEl.innerText = "Lỗi kết nối máy chủ sinh tồn.";
};

// --- SỰ KIỆN CLICK NÚT KẾT NỐI (btn-connect) ---
btnConnect.addEventListener('click', () => {
    if (!isStreaming) {
        // Dừng animation giả lập
        if (idleIntervalId) {
            clearInterval(idleIntervalId);
            idleIntervalId = null;
        }

        // Gửi lệnh kích hoạt luồng dữ liệu y tế thật
        if (ws.readyState === WebSocket.OPEN) {
            ws.send("START_STREAM");
        } else {
            // Nếu socket chưa kịp mở, đợi mở rồi gửi
            ws.onopen = () => {
                ws.send("START_STREAM");
            };
        }

        isStreaming = true;
        
        // Hiện thông tin bệnh nhân, ẩn placeholder chờ kết nối
        const patientPlaceholder = document.getElementById('patient-card-placeholder');
        const patientCard = document.getElementById('patient-card');
        if (patientPlaceholder) patientPlaceholder.style.display = 'none';
        if (patientCard) patientCard.style.display = 'flex';
        
        // Reset dữ liệu đồ thị về trống để hứng dữ liệu thật
        hrChart.data.datasets[0].data = Array(maxDataPoints).fill(null);
        spo2Chart.data.datasets[0].data = Array(maxDataPoints).fill(null);
        hrChart.update();
        spo2Chart.update();

        // Thay đổi trạng thái nút bấm sang màu xám và disabled
        btnConnect.disabled = true;
        btnConnect.innerText = "Đang thu thập dữ liệu sinh tồn...";
        btnConnect.style.background = "rgba(255, 255, 255, 0.08)";
        btnConnect.style.color = "var(--text-muted)";
        btnConnect.style.borderColor = "rgba(255, 255, 255, 0.04)";
        btnConnect.style.boxShadow = "none";
        
        statusTextEl.innerText = "Đang đồng bộ tín hiệu sinh tồn thực tế...";
        riskScoreEl.innerText = "0%";
    }
});

// --- POPUP LỊCH SỬ CẢNH BÁO (MODAL) ---
btnHistory.addEventListener('click', async () => {
    try {
        const response = await fetch('http://127.0.0.1:8000/api/history');
        const data = await response.json();
        
        tableBody.innerHTML = '';
        if (data.length === 0) {
            tableBody.innerHTML = '<tr><td colspan="5" style="text-align:center; color: var(--text-muted);">Không tìm thấy bản ghi cảnh báo nào.</td></tr>';
        } else {
            data.forEach(row => {
                const tr = document.createElement('tr');
                
                let riskBadgeClass = 'risk-normal';
                let riskLevel = 'Bình thường';
                
                if (row.risk_score < 30) {
                    riskBadgeClass = 'risk-normal';
                    riskLevel = 'Bình thường';
                } else if (row.risk_score < 85) {
                    riskBadgeClass = 'risk-warning';
                    riskLevel = 'Cảnh báo';
                } else {
                    riskBadgeClass = 'risk-alert';
                    riskLevel = 'Báo động';
                }
                
                tr.innerHTML = `
                    <td style="font-family: var(--font-clinical);">${row.timestamp}</td>
                    <td>${row.patient_id}</td>
                    <td class="risk-high">${row.hr} bpm</td>
                    <td style="color: var(--color-cyan); font-weight: 600;">${row.spo2}%</td>
                    <td><span class="${riskBadgeClass}">${Math.round(row.risk_score)}% - ${riskLevel}</span></td>
                `;
                tableBody.appendChild(tr);
            });
        }
        
        historyModal.style.display = 'flex';
    } catch (error) {
        console.error(error);
        alert("Không thể kết nối đến cơ sở dữ liệu để lấy lịch sử: " + error.message);
    }
});

// Đóng modal
btnCloseModal.addEventListener('click', () => {
    historyModal.style.display = 'none';
});

// Đóng modal khi nhấn ngoài vùng content
window.addEventListener('click', (event) => {
    if (event.target === historyModal) {
        historyModal.style.display = 'none';
    }
});

// --- TÍCH HỢP AI CHATBOT (GEMINI) ---
async function submitChat() {
    const question = chatInput.value.trim();
    if (question === '') return;
    
    // ✓ Kiểm tra xem đã kết nối wearable chưa
    if (!isStreaming) {
        appendMessage('bot', '⚠️ Vui lòng kết nối thiết bị wearable trước khi hỏi AI. Bấm "KẾT NỐI THIẾT BỊ WEARABLE" để bắt đầu.', 'CARDIO-AI');
        return;
    }
    
    chatInput.value = ''; // Xóa sạch khung nhập

    // Hiển thị tin nhắn người dùng
    appendMessage('user', question, '');

    // Lấy chỉ số sinh tồn hiện tại từ biểu đồ để gửi kèm ngữ cảnh y tế
    const hrDataArray = hrChart.data.datasets[0].data;
    const spo2DataArray = spo2Chart.data.datasets[0].data;
    const currentHR = hrDataArray[hrDataArray.length - 1] || 75; 
    const currentSpO2 = spo2DataArray[spo2DataArray.length - 1] || 98.5;

    // Hiển thị tin nhắn chờ phân tích của AI
    const loadingId = appendMessage('bot', 'AI đang phân tích các chỉ số bệnh nhân và soạn câu trả lời...', 'CARDIO-AI');

    try {
        const response = await fetch('http://127.0.0.1:8000/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                question: question,
                hr: currentHR,
                spo2: currentSpO2
            })
        });
        
        const data = await response.json();
        
        // Điền câu trả lời thực tế từ backend AI vào tin nhắn chờ
        const botMsgEl = document.getElementById(loadingId);
        if (botMsgEl) {
            botMsgEl.querySelector('p').innerText = data.answer;
        }
        chatWindow.scrollTop = chatWindow.scrollHeight;
    } catch (error) {
        const botMsgEl = document.getElementById(loadingId);
        if (botMsgEl) {
            botMsgEl.querySelector('p').innerText = "Lỗi kết nối: Không thể gửi câu hỏi đến Trợ lý AI.";
        }
    }
}

// Lắng nghe phím Enter
chatInput.addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
        submitChat();
    }
});

// Lắng nghe nút Gửi
chatSendBtn.addEventListener('click', submitChat);

// Hàm vẽ tin nhắn phụ trợ
function appendMessage(sender, text, senderTitle) {
    const msgDiv = document.createElement('div');
    msgDiv.className = `chat-message ${sender}`;
    
    const senderSpan = document.createElement('span');
    senderSpan.className = 'message-sender';
    senderSpan.innerText = senderTitle;
    
    const textP = document.createElement('p');
    textP.innerText = text;
    
    msgDiv.appendChild(senderSpan);
    msgDiv.appendChild(textP);
    
    const id = 'msg-' + Math.random().toString(36).substr(2, 9);
    msgDiv.id = id;
    
    chatWindow.appendChild(msgDiv);
    chatWindow.scrollTop = chatWindow.scrollHeight;
    return id;
}