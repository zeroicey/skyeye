# SkyEye 特征识别改进综合方案

## 项目现状分析

### 当前架构

```
视频输入 → 每10帧取1帧 → YOLOv8n 检测人物 → CLIP 服装识别 → 存储 SQLite
                                                      ↓
搜索查询 → 关键词匹配 → 返回结果 (按时间去重)
```

### 存在问题

| 模块 | 问题 | 影响 |
|------|------|------|
| **YOLO** | yolo26n 精度低，无追踪 | 漏检、重复 |
| **CLIP** | Prompt 固定 20 个，阈值低 | 识别不全、误检 |
| **搜索** | 简单关键词匹配 | 召回低 |
| **存储** | SQLite 无向量搜索 | 无法语义搜索 |

---

## 综合改进方案

### 架构升级

```
视频输入 → 每10帧取1帧 → YOLOv8s + ByteTrack → 人员追踪ID
                                    ↓
                            服装属性识别 (扩展 CLIP + 颜色提取)
                                    ↓
                            特征向量生成 (CLIP Embedding)
                                    ↓
                            PostgreSQL + pgvector 存储
                                    ↓
搜索查询 → 向量语义搜索 → 返回按追踪ID去重 + 轨迹可视化
```

---

## 实施路线图

### Phase 1: 基础优化 (1周)

| 任务 | 方案 | 预期效果 |
|------|------|----------|
| YOLO 升级 | yolo26n → yolov8s | +9% mAP |
| CLIP 扩展 | 20 → 50+ prompts | 识别更多类型 |
| 阈值优化 | 0.1 → 0.15-0.2 | 减少误检 |
| 图像增强 | 直方图均衡化 | 小目标提升 |

**代码改动**：

```python
# 1. 升级模型
MODEL = YOLO("yolov8s.pt")  # 替换 yolo26n

# 2. 扩展 prompts
CLOTHING_PROMPTS = [
    # 原有 20 个 + 扩展 30+ 个
    "a person wearing a white shirt",
    "a person wearing a black shirt",
    # ... 扩展颜色
    "a person wearing an orange shirt",
    "a person wearing a purple shirt",
    # ... 扩展款式
    "a person wearing a hoodie",
    "a person wearing a uniform",
    "a person wearing a safety vest",
]

# 3. 调整阈值
CLOTHING_THRESHOLD = 0.15  # 从 0.1 提升
COLOR_THRESHOLD = 0.2
```

### Phase 2: 追踪集成 (1周)

| 任务 | 方案 | 预期效果 |
|------|------|----------|
| ByteTrack 集成 | YOLO + ByteTrack | 轨迹追踪 |
| 追踪ID去重 | 按 track_id 分组 | 结果去重 |
| 轨迹存储 | 存储完整轨迹 | 支持轨迹回放 |

### Phase 3: 特征增强 (1-2周)

| 任务 | 方案 | 预期效果 |
|------|------|----------|
| 颜色提取 | K-Means 聚类 | 精确颜色 |
| 属性模型 | OpenPAR 集成 | 26+ 属性 |
| 向量化 | CLIP Embedding | 语义搜索 |

**颜色提取实现**：

```python
import cv2
import numpy as np
from sklearn.cluster import KMeans

def extract_colors(crop, top_k=3):
    """提取主色调"""
    # 排除背景 (假设边缘为背景)
    h, w = crop.shape[:2]
    margin = int(min(h, w) * 0.1)
    roi = crop[margin:-margin, margin:-margin]
    
    # K-Means 聚类
    pixels = roi.reshape(-1, 3)
    kmeans = KMeans(n_clusters=top_k, n_init=10)
    kmeans.fit(pixels)
    
    # 转换为颜色名称
    colors = []
    for color in kmeans.cluster_centers_:
        colors.append(rgb_to_color_name(color))
    
    return colors

COLOR_MAP = {
    (255, 255, 255): 'white',
    (0, 0, 0): 'black',
    (255, 0, 0): 'red',
    (0, 255, 0): 'green',
    (0, 0, 255): 'blue',
    (255, 255, 0): 'yellow',
    (255, 165, 0): 'orange',
    (128, 0, 128): 'purple',
    (165, 42, 42): 'brown',
    (192, 192, 192): 'gray',
}

def rgb_to_color_name(rgb):
    rgb = tuple(map(int, rgb))
    min_dist = float('inf')
    color_name = 'unknown'
    
    for color, name in COLOR_MAP.items():
        dist = sum((a - b) ** 2 for a, b in zip(rgb, color))
        if dist < min_dist:
            min_dist = dist
            color_name = name
    
    return color_name
```

### Phase 4: 向量搜索 (1周)

| 任务 | 方案 | 预期效果 |
|------|------|----------|
| 数据库迁移 | SQLite → PostgreSQL | 可靠性 |
| 向量存储 | pgvector | 语义相似搜索 |
| 搜索升级 | 关键词 → 向量 | 自然语言搜索 |

---

## 详细实施清单

### Week 1: 基础优化

- [ ] 替换 YOLO 模型为 yolo11s.pt 或 yolov12s.pt (性能优于 yolo26n)
- [ ] 扩展 CLOTHING_PROMPTS 到 50+
- [ ] 调整检测阈值和服装阈值
- [ ] 添加图像增强预处理

### Week 2: 追踪集成

- [ ] 安装 ByteTrack
- [ ] 集成 YOLO + ByteTrack
- [ ] 修改视频处理流程
- [ ] 添加 track_id 到结果

### Week 3: 特征增强

- [ ] 实现颜色提取 (K-Means)
- [ ] 集成 OpenPAR 或 ViT-Attribute
- [ ] 实现 CLIP Embedding 生成
- [ ] 修改数据库 schema

### Week 4: 向量搜索

- [ ] 迁移到 PostgreSQL + pgvector
- [ ] 实现向量存储和检索
- [ ] 更新搜索 API
- [ ] 性能测试

---

## 技术选型总结

### 推荐配置

| 模块 | 当前 | 推荐 | 理由 |
|------|------|------|------|
| **检测模型** | yolo26n (2026新版本) | yolo11s/yolov12s | 新版本性能更优 |
| **追踪** | 无 | ByteTrack | SOTA 方案 |
| **服装识别** | CLIP 20 prompts | CLIP 50+ prompts + 颜色提取 | 覆盖更广 |
| **属性识别** | 无 | OpenPAR | 专用模型 |
| **数据库** | SQLite | PostgreSQL + pgvector | 向量搜索 |

### 可选升级

| 模块 | 方案 | 复杂度 | 收益 |
|------|------|--------|------|
| VLM | Qwen2-VL/LLaVA | 高 | 支持自然语言描述 |
| 微调 | 服装数据集微调 | 高 | 定制化属性 |
| TensorRT | FP16/INT8 加速 | 中 | 推理速度+50% |

---

## 预期效果

| 指标 | 当前 | 改进后 | 提升 |
|------|------|--------|------|
| 人物检测召回率 | ~80% | ~90% | +10% |
| 服装识别准确率 | ~60% | ~85% | +25% |
| 搜索召回率 | ~50% | ~80% | +30% |
| 推理速度 | 10 FPS | 15 FPS | +50% |

---

## 参考文档

- [YOLO 检测改进](./yolo-detection-improvement.md)
- [服装属性识别改进](./clothing-attribute-improvement.md)
- [ByteTrack 集成](./bytetrack-integration.md)
