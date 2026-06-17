# 环境配置
import os
# 在导入ultralytics之前强制离线
os.environ["ULTRALYTICS_OFFLINE"] = "1"
os.environ["ULTRALYTICS_SKIP_VERSION_CHECK"] = "1"
os.environ["ULTRALYTICS_SKIP_DOWNLOAD"] = "1"
os.environ["YOLO_VERBOSE"] = "False"

from pathlib import Path
from PIL import Image
from ultralytics import YOLO

# 模型加载函数
def load_local_model():
    model_path = Path(r"D:\cv-test\cv_proj\runs\plant_det_v8s\weights\best.pt")
    if not model_path.exists():
        raise FileNotFoundError(f"模型文件不存在: {model_path}")

    # 直接加载本地模型文件
    model = YOLO(str(model_path))

    # 只保留有效的overrides设置，verbose=False可以关闭控制台输出，pretrained=False防止尝试下载预训练权重
    model.overrides["verbose"] = False
    model.overrides["pretrained"] = False

    return model

# 全局只加载一次
model = load_local_model()

# 推理核心函数
def predict_with_image(image: Image.Image, conf=0.25):
    # 纯本地推理，绝不访问网络
    results = model(image, conf=conf, verbose=False)
    
    detections = []
    for r in results:
        if r.boxes is None:
            continue
        for box in r.boxes:
            detections.append({
                "class": model.names[int(box.cls[0])],
                "confidence": round(float(box.conf[0]), 2),# 置信度
                "bbox": [round(float(x), 1) for x in box.xyxy[0]]# 检测框坐标
            })

    # 生成标注图
    annotated_frame = results[0].plot()
    annotated_img = Image.fromarray(annotated_frame[..., ::-1])
    return detections, annotated_img