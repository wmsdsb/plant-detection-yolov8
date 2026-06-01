导入numpy作为np
from PIL import Image
from ultralytics import YOLO
from pathlib import Path# 导入依赖模块

DEFAULT_MODEL_PATH = Path(__file__).parent.parent / "runs" / "plant_det_v8s" / "weights" / "best.pt"# 定义模型默认路径

_model = None

def get_model(model_path: str = None) -> YOLO:
    global _model
    如果_model为 None:
        path = model_path or str(DEFAULT_MODEL_PATH)
        如果路径(路径)不存在：
            raise FileNotFoundError(
                模型文件不存在:{路径} 
                f"请先在云GPU上训练模型并将 best.pt 放到此位置。"
            )
_model =YOLO(路径)
    return _model# 全局模型变量和懒加载模型函数


def predict(image: Image.Image, conf: float = 0.25) -> list[dict]:
模型 =获取模型()
结果 =模型(图像，置信度=置信度)

检测结果 =[]
    对于r在结果中：
框 = r.框
        对于i在 范围(len(框)):
            detections.append({
                “class”: 模型.
                “置信度”: round(float(boxes.conf[i]), 4),
                : [round(float(v), 1) for v in boxes.xyxy[i].tolist()],
            })
    return detections# 基础预测函数并返回检测结果


def predict_with_image(image: Image.Image, conf: float = 0.25) -> tuple[list[dict], Image.Image]:
模型 =获取模型()
结果 =模型(图像，置信度=置信度)

检测结果 =[]
    对于r在结果中：
框 = r.框
        对于i在 范围len(框)):
检测 ={
“类别”: 模型.名称[int(boxes.cls[i])],
“置信度”:round(float(boxes.conf[i]), 4),
                "bbox": [round(float(v), 1)  v in boxes.xyxy[i].tolist()],
            }
检测结果.追加(检测)

    annotated = results[0].plot()
    annotated_img = Image.fromarray(annotated)


