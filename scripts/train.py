"""在云GPU平台运行此脚本训练YOLOv8s模型。

用法：
    python train.py --data /path/to/data.yaml --epochs 100 --batch 16
"""

import argparse
from ultralytics import YOLO

def main():
    parser = argparse.ArgumentParser(description="训练植物检测模型")
    parser.add_argument("--data", type=str, required=True, help="data.yaml 的绝对路径")
    parser.add_argument("--model", type=str, default="yolov8s.pt", help="预训练模型 (默认 yolov8s.pt)")
    parser.add_argument("--epochs", type=int, default=100, help="训练轮数")
    parser.add_argument("--batch", type=int, default=16, help="batch size，显存不够改小")
    parser.add_argument("--imgsz", type=int, default=640, help="输入图片尺寸")
    parser.add_argument("--device", type=str, default="0", help="GPU 设备号")
    parser.add_argument("--patience", type=int, default=20, help="早停耐心值")
    parser.add_argument("--project", type=str, default="runs", help="输出目录")
    parser.add_argument("--name", type=str, default="plant_det_v8s", help="实验名称")
    args = parser.parse_args()

    model = YOLO(args.model)
    results = model.train(
        data=args.data,
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        device=args.device,
        patience=args.patience,
        save=True,
        project=args.project,
        name=args.name,
        amp=True,
    )

    # 训练结束后在测试集上评估
    metrics = model.val(data=args.data, split="test")
    print(f"\n===== 测试集评估结果 =====")
    print(f"mAP50:   {metrics.box.map50:.4f}")
    print(f"mAP50-95: {metrics.box.map:.4f}")

if __name__ == "__main__":
    main()
