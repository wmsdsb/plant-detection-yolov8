# 🌿 植物类别识别系统 (Plant Recognition System)

基于 [YOLOv8](https://github.com/ultralytics/ultralytics) + [FastAPI](https://fastapi.tiangolo.com/) 的植物识别 Web 应用，支持 **图片上传识别**、**摄像头实时识别**、**AI 植物科普**、**用户系统** 与 **历史记录** 等功能，可识别 **100 种** 常见植物。

## ✨ 功能特性

- 🖼️ **图片识别**：拖拽 / 点击上传植物图片，返回标注框 + 置信度，可调节置信度阈值
- 📷 **摄像头实时识别**：调用浏览器摄像头，定时捕获画面并实时绘制检测框
- 🤖 **AI 植物百科**：识别后自动调用大模型（DeepSeek-V3 / SiliconFlow）生成该植物的科普介绍
- 👤 **用户系统**：注册、登录、退出，基于 JWT 鉴权，密码 bcrypt 加密
- 📜 **历史记录**：分页查看每次识别的原图 / 标注图 / 检测结果，数据持久化到 SQLite
- 🎯 **纯本地推理**：强制离线加载本地权重，推理过程不访问网络

## 🧠 模型与数据集

- **检测模型**：YOLOv8s，在云 GPU 上训练 100 个 epoch
- **数据集**：[LeafLogic Object Detection](https://universe.roboflow.com/lasso-pacific-qyid3/leaflogic-object-detection-b33dm/dataset/5)（100 类，CC BY 4.0）
- **验证集指标**（见 `runs/plant_det_v8s/results.csv`）：

| 指标 | 数值 |
|------|------|
| mAP@0.5 | **0.8705** |
| mAP@0.5:0.95 | **0.7253** |
| Precision | 0.8630 |
| Recall | 0.8221 |

训练过程曲线、混淆矩阵、F1/PR 曲线等可视化图见 `runs/plant_det_v8s/`。

## 🏗️ 项目结构

```
plant-detection-yolov8/
├── app/                            # 后端 Web 应用 (FastAPI)
│   ├── __init__.py
│   ├── main.py                     # FastAPI 路由：认证 / 识别 / 历史 / AI 科普
│   ├── inference.py                # YOLOv8 加载与推理核心
│   └── database.py                 # SQLite 数据库 (users / records 表)
├── static/                         # 前端页面 (原生 HTML/CSS/JS)
│   ├── index.html                  # 主界面（识别 / 摄像头 / 历史）
│   ├── login.html                  # 登录 / 注册页
│   ├── script.js                   # 前端交互逻辑
│   ├── style.css
│   ├── background.png
│   └── images/
├── scripts/                        # 训练相关脚本
│   ├── train.py                    # 云 GPU 训练脚本
│   ├── prepare_data_yaml.py        # 修复 data.yaml 相对路径
│   └── CLOUD_TRAIN.md              # 云 GPU 训练指南
├── runs/plant_det_v8s/             # 训练产出
│   ├── weights/best.pt             # ✅ 训练好的最佳权重
│   ├── results.csv                 # 训练指标记录
│   └── *.png                       # 训练可视化图表
├── requirements.txt                # Python 依赖
└── README.md
```

## 🔧 环境要求

- Python 3.8+
- PyTorch（建议含 CUDA，CPU 也可运行）
- 见 `requirements.txt`

## 📦 安装

```bash
# 1. 克隆仓库
git clone https://github.com/wmsdsb/plant-detection-yolov8.git
cd plant-detection-yolov8

# 2. 创建虚拟环境（推荐）
python -m venv .venv
source .venv/bin/activate        # Linux / Mac
# .venv\Scripts\activate         # Windows

# 3. 安装依赖
pip install -r requirements.txt
```

> ⚠️ 权重文件已随仓库提供（`runs/plant_det_v8s/weights/best.pt`），无需另外下载。

## ⚙️ 配置

### 1. 模型路径

推理时在 `app/inference.py` 中通过 `load_local_model()` 加载本地权重。默认路径为：

```python
model_path = Path(r"D:\cv-test\cv_proj\runs\plant_det_v8s\weights\best.pt")
```

请将其修改为你本地的实际路径，或指向仓库内的 `runs/plant_det_v8s/weights/best.pt`。

### 2. AI 科普接口（可选）

`app/main.py` 默认使用 SiliconFlow 的 DeepSeek-V3 模型。可通过环境变量覆盖：

```bash
export DEFAULT_API_KEY="你的API_KEY"
export DEFAULT_API_BASE="https://api.siliconflow.cn/v1"
export DEFAULT_MODEL="Pro/deepseek-ai/DeepSeek-V3"
```

未配置时使用代码内置默认值；即使 AI 接口不可用，识别功能仍正常工作。

## 🚀 运行

在项目根目录（`app` 的上一级，确保 `app` 是可导入的包）启动服务：

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

浏览器访问 👉 **http://localhost:8000**

- 首次访问会跳转到 **/login** 注册 / 登录
- 登录成功后进入主界面，即可上传图片或开启摄像头识别

## 📡 接口一览

| 方法 | 路径 | 说明 | 鉴权 |
|------|------|------|------|
| POST | `/api/register` | 用户注册 | ❌ |
| POST | `/api/login` | 用户登录，返回 JWT | ❌ |
| POST | `/api/predict` | 图片识别（返回检测框 + 标注图） | ✅ |
| POST | `/api/predict/image` | 识别接口别名 | ✅ |
| GET  | `/api/history` | 分页查询历史记录 | ✅ |
| POST | `/api/ai-explain` | AI 植物科普 | ✅ |
| POST | `/api/user/logout` | 退出登录 | ✅ |

## 🎓 重新训练模型

如需用自己的数据集重新训练，请参考 [`scripts/CLOUD_TRAIN.md`](scripts/CLOUD_TRAIN.md)，核心步骤：

```bash
# 1. 修复 data.yaml 中的相对路径
python scripts/prepare_data_yaml.py --input data.yaml --output data_fixed.yaml

# 2. 在云 GPU 上训练
python scripts/train.py --data data_fixed.yaml --epochs 100 --batch 16 --device 0
```

训练参数（`--epochs` / `--batch` / `--imgsz` / `--device` 等）见 `scripts/train.py`。

## 🖼️ 效果展示

> 识别主界面、摄像头实时检测、AI 科普卡片、历史记录等效果建议补充截图。

## 📄 许可证

[MIT](LICENSE)

## 🙏 致谢

- 检测框架：[Ultralytics YOLOv8](https://github.com/ultralytics/ultralytics)
- 数据集：[LeafLogic Object Detection (Roboflow)](https://universe.roboflow.com/lasso-pacific-qyid3/leaflogic-object-detection-b33dm/dataset/5)
- AI 科普：[SiliconFlow](https://siliconflow.cn) / DeepSeek-V3
