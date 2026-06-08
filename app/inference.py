import numpy as np
from PIL import Image
from ultralytics import YOLO
from pathlib import Path# 导入依赖模块

DEFAULT_MODEL_PATH = Path(__file__).parent.parent / "runs" / "plant_det_v8s" / "weights" / "best.pt"# 定义模型默认路径

_model = None

def get_model(model_path: str = None) -> YOLO:
    global _model
    if _model is None:
        path = model_path or str(DEFAULT_MODEL_PATH)
        if not Path(path).exists():
            raise FileNotFoundError(
                f"模型文件不存在: {path}\n"
                f"请先在云GPU上训练模型并将 best.pt 放到此位置。"
            )
        _model = YOLO(path)
    return _model# 全局模型变量和懒加载模型函数


def predict(image: Image.Image, conf: float = 0.25) -> list[dict]:
    model = get_model()
    results = model(image, conf=conf)

    detections = []
    for r in results:
        boxes = r.boxes
        for i in range(len(boxes)):
            detections.append({
                "class": model.names[int(boxes.cls[i])],
                "confidence": round(float(boxes.conf[i]), 4),
                "bbox": [round(float(v), 1) for v in boxes.xyxy[i].tolist()],
            })
    return detections# 基础预测函数并返回检测结果


def predict_with_image(image: Image.Image, conf: float = 0.25) -> tuple[list[dict], Image.Image]:
    model = get_model()
    results = model(image, conf=conf)

    detections = []
    for r in results:
        boxes = r.boxes
        for i in range(len(boxes)):
            det = {
                "class": model.names[int(boxes.cls[i])],
                "confidence": round(float(boxes.conf[i]), 4),
                "bbox": [round(float(v), 1) for v in boxes.xyxy[i].tolist()],
            }
            detections.append(det)

    annotated = results[0].plot()
    annotated_img = Image.fromarray(annotated)

    return detections, annotated_img# 带绘图的预测函数，返回结果和标注图
