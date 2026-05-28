const dropZone = document.getElementById('dropZone');
const fileInput = document.getElementById('fileInput');
const confSlider = document.getElementById('confSlider');
const confValue = document.getElementById('confValue');
const resultSection = document.getElementById('resultSection');
const originalImage = document.getElementById('originalImage');
const annotatedImage = document.getElementById('annotatedImage');
const resultsList = document.getElementById('resultsList');

// ========== Tab 切换 ==========
document.querySelectorAll('.nav-tabs .tab').forEach(tab => {
    tab.addEventListener('click', (e) => {
        e.preventDefault();
        document.querySelectorAll('.nav-tabs .tab').forEach(t => t.classList.remove('active'));
        tab.classList.add('active');

        document.querySelectorAll('.tab-content').forEach(c => c.style.display = 'none');
        const target = tab.dataset.tab;
        document.getElementById(target + 'Tab').style.display = 'block';

        if (target === 'history') loadHistory(1);
    });
});

// ========== 置信度滑块 ==========
confSlider.addEventListener('input', () => {
    confValue.textContent = confSlider.value;
});

// ========== 点击上传 ==========
dropZone.addEventListener('click', () => fileInput.click());
fileInput.addEventListener('change', (e) => {
    if (e.target.files[0]) handleFile(e.target.files[0]);
});

// ========== 拖拽上传 ==========
dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZone.classList.add('dragover');
});
dropZone.addEventListener('dragleave', () => {
    dropZone.classList.remove('dragover');
});
dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.classList.remove('dragover');
    if (e.dataTransfer.files[0]) handleFile(e.dataTransfer.files[0]);
});

// ========== 上传识别 ==========
async function handleFile(file) {
    if (!file.type.startsWith('image/')) {
        alert('请选择图片文件');
        return;
    }

    const reader = new FileReader();
    reader.onload = (e) => { originalImage.src = e.target.result; };
    reader.readAsDataURL(file);

    resultSection.style.display = 'block';
    resultsList.innerHTML = '<div class="loading">识别中...</div>';
    annotatedImage.src = '';

    const formData = new FormData();
    formData.append('file', file);

    try {
        const resp = await fetch(`/api/predict/image?conf=${confSlider.value}`, {
            method: 'POST',
            body: formData,
        });

        if (!resp.ok) {
            const err = await resp.json();
            throw new Error(err.detail || '请求失败');
        }

        const data = await resp.json();
        annotatedImage.src = data.annotated_image;

        if (data.detections.length === 0) {
            resultsList.innerHTML = '<p style="text-align:center;color:#999;padding:1rem;">未检测到植物</p>';
        } else {
            let html = '<h3>检测结果</h3>';
            data.detections.forEach((det, i) => {
                const pct = Math.round(det.confidence * 100);
                const color = pct >= 70 ? '#4caf50' : pct >= 40 ? '#ff9800' : '#f44336';
                html += `
                    <div class="result-item">
                        <span class="result-class">${i + 1}. ${det.class}</span>
                        <div class="confidence-bar">
                            <div class="bar">
                                <div class="bar-fill" style="width:${pct}%;background:${color}"></div>
                            </div>
                            <span class="value">${pct}%</span>
                        </div>
                    </div>`;
            });
            resultsList.innerHTML = html;
        }
    } catch (err) {
        resultsList.innerHTML = `<div class="error">错误: ${err.message}</div>`;
    }
}

// ========== 历史记录 ==========
async function loadHistory(page) {
    const historyList = document.getElementById('historyList');
    const pagination = document.getElementById('pagination');
    historyList.innerHTML = '<div class="loading">加载中...</div>';
    pagination.innerHTML = '';

    try {
        const resp = await fetch(`/api/history?page=${page}&limit=10`);
        const data = await resp.json();

        if (data.records.length === 0) {
            historyList.innerHTML = '<p style="text-align:center;color:#999;padding:2rem;">暂无记录</p>';
            return;
        }

        let html = '';
        data.records.forEach(r => {
            const tags = r.detections.map(d =>
                `<span class="detection-tag">${d.class}<span class="tag-conf">${Math.round(d.confidence * 100)}%</span></span>`
            ).join('');

            html += `
                <div class="history-card">
                    <div class="history-header">
                        <span>#${r.id}</span>
                        <span>${r.created_at}</span>
                        <span>检测到 ${r.detection_count} 个目标</span>
                    </div>
                    <div class="history-images">
                        <img src="/uploads/${r.original_image}" alt="原图" loading="lazy">
                        ${r.annotated_image ? `<img src="/uploads/${r.annotated_image}" alt="标注" loading="lazy">` : ''}
                    </div>
                    <div class="history-detections">${tags}</div>
                </div>`;
        });
        historyList.innerHTML = html;

        // 分页
        const totalPages = Math.ceil(data.total / data.limit);
        if (totalPages > 1) {
            let pHtml = `<button ${page <= 1 ? 'disabled' : ''} onclick="loadHistory(${page - 1})">上一页</button>`;
            for (let i = 1; i <= totalPages; i++) {
                pHtml += `<button class="${i === page ? 'active' : ''}" onclick="loadHistory(${i})">${i}</button>`;
            }
            pHtml += `<button ${page >= totalPages ? 'disabled' : ''} onclick="loadHistory(${page + 1})">下一页</button>`;
            pagination.innerHTML = pHtml;
        }
    } catch (err) {
        historyList.innerHTML = `<div class="error">加载失败: ${err.message}</div>`;
    }
}

// ========== 摄像头实时识别 ==========
const cameraVideo = document.getElementById('cameraVideo');
const cameraCanvas = document.getElementById('cameraCanvas');
const cameraOverlay = document.getElementById('cameraOverlay');
const cameraToggle = document.getElementById('cameraToggle');
const cameraIntervalSelect = document.getElementById('cameraInterval');
const cameraResults = document.getElementById('cameraResults');

let cameraStream = null;
let cameraTimer = null;
let isDetecting = false;

cameraToggle.addEventListener('click', async () => {
    if (cameraStream) {
        stopCamera();
    } else {
        await startCamera();
    }
});

// 切换到摄像头 Tab 时自动提示
const origTabClick = document.querySelector('[data-tab="camera"]');
if (origTabClick) {
    origTabClick.addEventListener('click', () => {
        if (!cameraStream) {
            cameraResults.innerHTML = '<div class="camera-status">点击上方按钮开启摄像头</div>';
        }
    });
}

// 离开摄像头 Tab 时停止识别
const cameraTab = document.getElementById('cameraTab');

async function startCamera() {
    try {
        cameraStream = await navigator.mediaDevices.getUserMedia({
            video: { facingMode: 'environment', width: { ideal: 640 }, height: { ideal: 480 } }
        });
        cameraVideo.srcObject = cameraStream;
        await cameraVideo.play();

        cameraToggle.textContent = '关闭摄像头';
        cameraToggle.classList.add('active');

        // 等视频就绪后设置 canvas 尺寸
        cameraVideo.addEventListener('loadedmetadata', () => {
            cameraCanvas.width = cameraVideo.videoWidth;
            cameraCanvas.height = cameraVideo.videoHeight;
        }, { once: true });

        // 开始定时识别
        startDetection();
    } catch (err) {
        cameraResults.innerHTML = `<div class="error">无法访问摄像头: ${err.message}</div>`;
    }
}

function stopCamera() {
    if (cameraStream) {
        cameraStream.getTracks().forEach(t => t.stop());
        cameraStream = null;
    }
    if (cameraTimer) {
        clearInterval(cameraTimer);
        cameraTimer = null;
    }
    isDetecting = false;
    cameraVideo.srcObject = null;
    cameraToggle.textContent = '开启摄像头';
    cameraToggle.classList.remove('active');

    const ctx = cameraCanvas.getContext('2d');
    ctx.clearRect(0, 0, cameraCanvas.width, cameraCanvas.height);
    cameraOverlay.innerHTML = '';
    cameraResults.innerHTML = '<div class="camera-status">摄像头已关闭</div>';
}

function startDetection() {
    if (cameraTimer) clearInterval(cameraTimer);
    const interval = parseInt(cameraIntervalSelect.value);
    isDetecting = true;
    cameraTimer = setInterval(captureAndDetect, interval);
    captureAndDetect(); // 立即执行一次
}

// 切换间隔时重启定时器
cameraIntervalSelect.addEventListener('change', () => {
    if (isDetecting) startDetection();
});

async function captureAndDetect() {
    if (!cameraStream || !isDetecting) return;

    // 截取当前帧
    const tmpCanvas = document.createElement('canvas');
    tmpCanvas.width = cameraVideo.videoWidth || 640;
    tmpCanvas.height = cameraVideo.videoHeight || 480;
    const tmpCtx = tmpCanvas.getContext('2d');
    tmpCtx.drawImage(cameraVideo, 0, 0, tmpCanvas.width, tmpCanvas.height);

    tmpCanvas.toBlob(async (blob) => {
        if (!blob || !isDetecting) return;

        const formData = new FormData();
        formData.append('file', blob, 'camera.jpg');

        try {
            const resp = await fetch(`/api/predict?conf=${confSlider.value}`, {
                method: 'POST',
                body: formData,
            });

            if (!resp.ok) return;
            const data = await resp.json();

            // 在 canvas 上绘制检测框
            drawDetections(data.detections, tmpCanvas.width, tmpCanvas.height);

            // 更新底部标签
            cameraOverlay.innerHTML = data.detections.map(d =>
                `<span class="cam-tag">${d.class} ${Math.round(d.confidence * 100)}%</span>`
            ).join('');

            // 更新结果面板
            if (data.detections.length === 0) {
                cameraResults.innerHTML = '<div class="camera-status">未检测到植物</div>';
            } else {
                let html = '<h3>实时检测结果</h3>';
                data.detections.forEach((det, i) => {
                    const pct = Math.round(det.confidence * 100);
                    const color = pct >= 70 ? '#4caf50' : pct >= 40 ? '#ff9800' : '#f44336';
                    html += `
                        <div class="result-item">
                            <span class="result-class">${i + 1}. ${det.class}</span>
                            <div class="confidence-bar">
                                <div class="bar">
                                    <div class="bar-fill" style="width:${pct}%;background:${color}"></div>
                                </div>
                                <span class="value">${pct}%</span>
                            </div>
                        </div>`;
                });
                cameraResults.innerHTML = html;
            }
        } catch (err) {
            // 静默失败，不刷屏报错
        }
    }, 'image/jpeg', 0.9);
}

function drawDetections(detections, imgW, imgH) {
    const ctx = cameraCanvas.getContext('2d');
    ctx.clearRect(0, 0, cameraCanvas.width, cameraCanvas.height);

    // 计算 canvas 实际显示尺寸与视频尺寸的比例
    const scaleX = cameraCanvas.width / imgW;
    const scaleY = cameraCanvas.height / imgH;

    const colors = ['#4caf50', '#ff9800', '#2196f3', '#e91e63', '#9c27b0',
                     '#00bcd4', '#ff5722', '#607d8b', '#795548', '#3f51b5'];

    detections.forEach((det, i) => {
        const [x1, y1, x2, y2] = det.bbox;
        const color = colors[i % colors.length];

        // 缩放坐标
        const sx1 = x1 * scaleX, sy1 = y1 * scaleY;
        const sx2 = x2 * scaleX, sy2 = y2 * scaleY;

        // 绘制框
        ctx.strokeStyle = color;
        ctx.lineWidth = 2;
        ctx.strokeRect(sx1, sy1, sx2 - sx1, sy2 - sy1);

        // 绘制标签背景
        const label = `${det.class} ${Math.round(det.confidence * 100)}%`;
        ctx.font = '14px sans-serif';
        const textW = ctx.measureText(label).width;
        ctx.fillStyle = color;
        ctx.fillRect(sx1, sy1 - 20, textW + 8, 20);

        // 绘制标签文字
        ctx.fillStyle = '#fff';
        ctx.fillText(label, sx1 + 4, sy1 - 5);
    });
}
