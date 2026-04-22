# 服装与人物特征识别改进方案

## 当前项目问题分析

当前使用 `CLIP (openai/clip-vit-base-patch32)` 进行服装识别，存在以下问题：

1. **Prompt 固定**：只有 20 个预定义 prompt，无法识别其他类型
2. **阈值过低**：0.1 的阈值导致误检多
3. **无法处理小目标**：CLIP 对裁剪后的小人效果差
4. **缺乏颜色提取**：只能匹配预定义颜色
5. **无细粒度属性**：无法识别花纹、款式等

---

## 改进方案

### 方案一：CLIP 增强 (推荐)

#### 1. 扩展 Prompt 库

```python
CLOTHING_PROMPTS = [
    # 颜色扩展
    "a person wearing a white shirt", "a person wearing a black shirt",
    "a person wearing a red shirt", "a person wearing a blue shirt",
    "a person wearing a green shirt", "a person wearing a yellow shirt",
    "a person wearing an orange shirt", "a person wearing a purple shirt",
    "a person wearing a pink shirt", "a person wearing a brown shirt",
    "a person wearing a gray shirt", "a person wearing a beige shirt",
    "a person wearing navy blue pants", "a person wearing khaki pants",
    # 款式扩展
    "a person wearing a polo shirt", "a person wearing a dress shirt",
    "a person wearing a hoodie", "a person wearing a suit",
    "a person wearing a uniform", "a person wearing work clothes",
    "a person wearing a safety vest", "a person wearing a hard hat",
    # 配饰
    "a person wearing glasses", "a person wearing a hat",
    "a person wearing a cap", "a person wearing a mask",
]

# 使用 CLIP 零样本分类
# 优势：无需训练，支持任意类别
```

#### 2. 多阈值策略

```python
# 颜色阈值 0.2，服装类型阈值 0.15
COLOR_THRESHOLD = 0.2
CLOTHING_TYPE_THRESHOLD = 0.15
```

#### 3. 图像预处理增强

```python
import cv2
import numpy as np

def enhance_for_clip(crop):
    # 直方图均衡化
    lab = cv2.cvtColor(crop, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    l = cv2.equalizeHist(l)
    enhanced = cv2.merge([l, a, b])
    enhanced = cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)
    
    # 增加对比度
    enhanced = cv2.convertScaleAbs(enhanced, alpha=1.2, beta=10)
    return enhanced
```

### 方案二：专用行人属性识别模型 (推荐)

使用专门的行人属性识别模型，精度更高：

| 模型 | 属性数量 | 数据集 | mAP |
|------|----------|--------|-----|
| **OpenPAR** | 26+ | PA-100K | 80%+ |
| **ViT-Attribute** | 15 | RAP | 75%+ |
| **JLAC** | 26 | Market-1501 | 78%+ |

#### OpenPAR 使用示例

```python
# OpenPAR - 开放行人属性识别
from transformers import AutoModel

model = AutoModel.from_pretrained("openpar/model")
# 支持属性：性别、年龄、服装颜色、服装类型、配饰等
```

### 方案三：多模型组合

```python
# 组合方案
1. YOLOv8s → 检测人物 (高召回)
2. 服装分类器 → 识别上装/下装
3. 颜色提取器 → 从图像提取主色调
4. 属性回归 → 年龄、性别等

# 颜色提取 (使用 K-Means)
import cv2
from sklearn.cluster import KMeans

def extract_dominant_colors(crop, k=3):
    img = cv2.cvtColor(crop, cv2.COLOR_BGR2RGB)
    img = img.reshape(-1, 3)
    
    kmeans = KMeans(n_clusters=k)
    kmeans.fit(img)
    
    colors = kmeans.cluster_centers_
    # 转换为颜色名称
    return [rgb_to_color_name(c) for c in colors]
```

### 方案四：视觉语言模型 (VLM)

使用更强的 VLM 进行详细描述：

| 模型 | 能力 | 速度 | 推荐 |
|------|------|------|------|
| **GPT-4o** | 最强 | 慢 | 离线/高精度 |
| **Qwen2-VL** | 强 | 中 | **推荐** |
| **LLaVA** | 中 | 快 | 本地部署 |
| **Phi-3.5-Vision** | 中 | 快 | 微软生态 |

```python
# 使用 Qwen2-VL 进行细粒度识别
from qwen_vl_utils import process_vision_info

messages = [{
    "role": "user",
    "content": [
        {"type": "image", "image": person_crop},
        {"type": "text", "text": "Describe this person's clothing in detail: colors, type, accessories"}
    ]
}]

# 返回详细描述
# "A person wearing a blue long-sleeve shirt, black pants, and white shoes"
```

---

## 推荐实施路径

### 阶段一：快速改进 (1-2天)

1. 扩展 CLIP prompt 到 50+ 个
2. 调整阈值到 0.15-0.2
3. 添加图像增强预处理

### 阶段二：模型升级 (3-5天)

1. 集成 OpenPAR 或专用属性识别模型
2. 添加颜色提取模块 (K-Means)
3. 实现多模型组合

### 阶段三：VLM 增强 (1周+)

1. 集成 Qwen2-VL 或 LLaVA
2. 实现自然语言描述生成
3. 支持复杂查询

---

## 参考资料

- [Pedestrian Attribute Recognition with CLIP](https://arxiv.org/html/2312.10692v1)
- [OpenPAR 开源项目](https://github.com/Event-AHU/OpenPAR)
- [行人属性识别论文列表](https://github.com/wangxiao5791509/Pedestrian-Attribute-Recognition-Paper-List)
- [CLIP 官方](https://openai.com/index/clip/)
