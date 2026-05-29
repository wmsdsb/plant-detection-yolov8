import numpy as np
from PIL import Image
from ultralytics import YOLO
from pathlib import Path

# 模型路径（相对于项目根目录）
DEFAULT_MODEL_PATH = Path(__file__).parent.parent / "runs" / "plant_det_v8s" / "weights" / "best.pt"

_model = None

def get_model(model_path: str = None) -> YOLO:
    """懒加载模型，避免启动时未训练好模型导致崩溃。"""
    global _model
    if _model is None:
        path = model_path or str(DEFAULT_MODEL_PATH)
        if not Path(path).exists():
            raise FileNotFoundError(
                f"模型文件不存在: {path}\n"
                f"请先在云GPU上训练模型并将 best.pt 放到此位置。"
            )
        _model = YOLO(path)
    return _model


def predict(image: Image.Image, conf: float = 0.25) -> list[dict]:
    """对图片进行植物检测。

    Args:
        image: PIL Image 对象
        conf: 置信度阈值，低于此值的结果将被过滤

    Returns:
        检测结果列表，每项包含 class, confidence, bbox
    """
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
    return detections


def predict_with_image(image: Image.Image, conf: float = 0.25) -> tuple[list[dict], Image.Image]:
    """预测并在图片上绘制检测框，返回结果和标注后的图片。"""
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

    # 用 results 自带的绘图方法
    annotated = results[0].plot()
    annotated_img = Image.fromarray(annotated)

    return detections, annotated_img
