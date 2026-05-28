# 云GPU训练指南

## 在云GPU平台（AutoDL/恒源云/矩池云）上训练

### 1. 上传文件到云平台
将整个项目上传到云平台的 `/root/autodl-tmp/` 目录：
- `leaflogic object detection.v5i.yolov5pytorch/` (数据集)
- `scripts/train.py`
- `scripts/prepare_data_yaml.py`

### 2. 安装依赖
```bash
pip install ultralytics opencv-python pillow
```

### 3. 修复数据路径
```bash
cd /root/autodl-tmp
python scripts/prepare_data_yaml.py \
    --input "leaflogic object detection.v5i.yolov5pytorch/data.yaml" \
    --output data_fixed.yaml
```

### 4. 开始训练
```bash
python scripts/train.py \
    --data data_fixed.yaml \
    --epochs 100 \
    --batch 16 \
    --device 0 \
    --project /root/autodl-tmp/runs \
    --name plant_det_v8s
```

### 5. 下载模型权重
训练完成后，从 `runs/plant_det_v8s/weights/best.pt` 下载到本地：
```
本地路径: D:/later/cv_proj/runs/plant_det_v8s/weights/best.pt
```

### 显存参考
| GPU 显存 | 建议 batch |
|----------|-----------|
| 8GB (RTX 3070) | 8 |
| 12GB (RTX 3060 12G) | 16 |
| 24GB (RTX 4090) | 32 |
