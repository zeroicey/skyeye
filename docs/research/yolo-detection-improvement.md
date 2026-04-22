# YOLO 人物检测改进方案

## 当前项目问题分析

当前使用 `yolo26n.pt` (YOLOv8n) 进行人物检测，存在以下问题：

1. **模型精度有限**：nano 版本为了轻量牺牲了精度
2. **小目标检测弱**：无人机视角下人物可能较小
3. **无追踪机制**：每帧独立检测，无法跨帧追踪同一人

---

## 改进方案

### 1. 升级 YOLO 模型版本

| 模型 | mAP@0.5 | 参数量 | 推理速度 | 推荐场景 |
|------|---------|--------|----------|----------|
| YOLOv8n (当前) | 52.5% | 3.2M | 最快 | - |
| **YOLOv8s** | 56.4% | 11.2M | 快 | **推荐** |
| YOLOv8m | 63.3% | 26.0M | 中 | 精度优先 |
| YOLOv12n | 58.1% | 2.6M | 最快 | 新版本 nano |
| **YOLOv12s** | 61.8% | 9.3M | 快 | **推荐** |

**建议**：从 `yolo26n.pt` 升级到 `yolov8s.pt` 或 `yolov12s.pt`，精度提升约 9%，速度可接受。

### 2. 使用专用人物检测模型

- **YOLO-Person**：专门针对人物检测优化的模型
- **YOLOX-Person**：使用 SimOTA 匹配，更适合密集场景

### 3. 模型微调 (Fine-tuning)

使用专门的人物数据集微调：
- **COCO-Person**：COCO 数据集中的人物标注
- **CrowdHuman**：人群密集场景数据集
- **Penn-Fudan**：行人检测数据集

```python
# 微调示例
from ultralytics import YOLO

model = YOLO('yolov8s.pt')
model.train(
    data='person.yaml',
    epochs=100,
    imgsz=640,
    batch=16,
    device=0,
    pretrained=True
)
```

### 4. 数据增强策略

针对无人机视角，增加以下增强：
- 随机缩放 (scale 0.5-1.5)
- 随机模糊
- 随机噪声
- 不同光照条件

### 5. 检测阈值优化

当前阈值 `conf > 0.5`，可调整为：
- 场景密集 → 降低到 0.3-0.4
- 场景稀疏 → 提高到 0.6-0.7
- 多帧确认：同一位置连续 2-3 帧检测到才确认

### 6. 多尺度检测

```python
# 使用多尺度推理
results_640 = model(frame, imgsz=640)
results_1280 = model(frame, imgsz=1280)

# 合并结果，过滤重复
# 小目标用 1280，大目标用 640
```

### 7. 软硬件优化

- **FP16 推理**：速度提升 30-50%，精度几乎不变
- **TensorRT 部署**：生产环境推荐

```python
model = YOLO('yolov8s.pt')
model.export(format='onnx', half=True)  # FP16
```

---

## 推荐实施方案

| 优先级 | 方案 | 预期提升 | 复杂度 |
|--------|------|----------|--------|
| P0 | 升级到 yolov8s.pt | +9% mAP | 低 |
| P1 | 添加 ByteTrack 追踪 | 连续检测 | 中 |
| P2 | 模型微调 (CrowdHuman) | +5-10% | 高 |
| P3 | TensorRT 部署 | 速度+30% | 中 |

---

## 参考资料

- [YOLOv12 vs YOLOv8 性能对比](https://arxiv.org/html/2407.12040v7)
- [Ultralytics 官方文档](https://docs.ultralytics.com/modes/track/)
- [COCO 数据集](https://cocodataset.org/)
- [CrowdHuman 数据集](https://www.crowdhuman.org/)
