# 目标追踪 (ByteTrack) 集成方案

## 当前项目问题

当前系统没有目标追踪机制，每帧独立检测：

1. **无法跨帧关联**：同一人物在不同帧无法关联
2. **重复结果**：搜索结果包含同一人的多个帧
3. **轨迹缺失**：无法分析人物移动轨迹

---

## ByteTrack 集成方案

### 1. 为什么选择 ByteTrack

- **ECCV 2022** 最新 SOTA 多目标追踪
- 与 YOLO 无缝集成
- 精度与速度平衡好
- 解决遮挡问题

### 2. 集成代码

```python
from ultralytics import YOLO
from bytetrack import ByteTracker
import numpy as np

# 初始化
yolo = YOLO('yolov8s.pt')
tracker = ByteTracker(
    track_thresh=0.5,
    track_buffer=30,
    match_thresh=0.8,
    frame_rate=30
)

def process_frame_with_tracking(frame):
    # YOLO 检测
    results = yolo(frame, verbose=False, classes=0)  # 只检测 person
    
    # 转换为 ByteTrack 格式
    dets = []
    for result in results:
        boxes = result.boxes
        for box in boxes:
            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
            conf = float(box.conf[0])
            dets.append([x1, y1, x2, y2, conf])
    
    if len(dets) == 0:
        return [], []
    
    dets = np.array(dets)
    
    # 追踪更新
    online_targets = tracker.update(dets, [frame.shape[:2]], [frame.shape[:2]])
    
    # 提取追踪结果
    tracks = []
    for target in online_targets:
        track_id = target.track_id
        bbox = target.tlbr  # [x1, y1, x2, y2]
        cls = target.cls
        conf = target.score
        
        tracks.append({
            'track_id': track_id,
            'bbox': bbox.tolist(),
            'class': int(cls),
            'confidence': float(conf)
        })
    
    return tracks, results
```

### 3. 处理视频流

```python
def process_video_tracking(video_path, output_path='tracks.json'):
    cap = cv2.VideoCapture(video_path)
    tracker = ByteTracker(track_thresh=0.5, track_buffer=30)
    
    all_tracks = []
    frame_id = 0
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # 检测
        results = yolo(frame, verbose=False, classes=0)
        
        # 转换为追踪格式
        dets = []
        for result in results:
            boxes = result.boxes
            for box in boxes:
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                conf = float(box.conf[0])
                dets.append([x1, y1, x2, y2, conf])
        
        # 更新追踪
        if len(dets) > 0:
            online_targets = tracker.update(
                np.array(dets), 
                [frame.shape[:2]], 
                [frame.shape[:2]]
            )
            
            for target in online_targets:
                all_tracks.append({
                    'frame': frame_id,
                    'track_id': target.track_id,
                    'bbox': target.tlbr.tolist(),
                    'timestamp': frame_id / fps
                })
        
        frame_id += 1
    
    cap.release()
    return all_tracks
```

### 4. 追踪结果可视化

```python
def draw_tracks(frame, tracks, colors=None):
    if colors is None:
        # 为每个 ID 生成固定颜色
        np.random.seed(42)
        colors = {i: tuple(np.random.randint(0, 255, 3).tolist()) 
                  for i in range(1000)}
    
    for track in tracks:
        track_id = track['track_id']
        bbox = track['bbox']
        
        color = colors.get(track_id, (255, 255, 255))
        
        x1, y1, x2, y2 = map(int, bbox)
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        cv2.putText(frame, f'ID:{track_id}', (x1, y1-10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
    
    return frame
```

### 5. 与搜索系统集成

```python
# 在 search_service.py 中添加追踪信息

def search_frames_with_tracking(video_ids: list, query: str) -> list:
    # ... 原有搜索逻辑 ...
    
    # 添加轨迹信息
    for result in results:
        track_id = get_track_id_for_frame(
            result['video_id'], 
            result['timestamp'],
            result['bbox']
        )
        result['track_id'] = track_id
    
    # 按 track_id 分组去重
    return deduplicate_by_track(results)
```

---

## 追踪增强功能

### 1. 轨迹分析

```python
def analyze_trajectory(tracks, track_id):
    """分析单个目标的轨迹"""
    track_points = [(t['bbox'][0], t['bbox'][1]) 
                   for t in tracks if t['track_id'] == track_id]
    
    # 计算移动方向
    # 计算速度
    # 检测停留区域
```

### 2. 跨帧服装一致性

```python
def link_clothing_across_frames(tracks, clip_features):
    """将同一人物的服装属性关联到轨迹"""
    # 同一 track_id 的所有帧使用相同的服装属性
    # 置信度加权平均
```

---

## 安装依赖

```bash
pip install bytetrack
# 或
pip install ultralytics  # 已包含追踪功能

# ultralytics 追踪用法
from ultralytics import YOLO

model = YOLO('yolov8s.pt')
results = model.track(source='video.mp4', persist=True)
```

---

## Ultralytics 内置追踪

Ultralytics YOLO 已内置 ByteTrack：

```python
from ultralytics import YOLO

model = YOLO('yolov8s.pt')

# 视频追踪
results = model.track(
    source='video.mp4',
    conf=0.4,
    iou=0.7,
    persist=True  # 跨帧保持追踪
)

# 处理结果
for r in results:
    if r.boxes and r.boxes.id is not None:
        boxes = r.boxes
        for i, (box, track_id) in enumerate(zip(boxes.xyxy, boxes.id)):
            print(f"Track ID: {int(track_id)}, Box: {box}")
```

---

## 推荐配置

```python
TRACKER_CONFIG = {
    'track_thresh': 0.5,      # 检测阈值
    'track_buffer': 30,       # 丢失后保留帧数
    'match_thresh': 0.8,      # 匹配阈值
    'frame_rate': 30,         # 视频帧率
    'min_box_area': 100,      # 最小检测框面积
    'aspect_ratio_thresh': 3  # 宽高比阈值
}
```

---

## 参考资料

- [ByteTrack 官方 GitHub](https://github.com/FoundationVision/ByteTrack)
- [Ultralytics 追踪文档](https://docs.ultralytics.com/modes/track/)
- [ByteTrack 论文](https://arxiv.org/abs/2110.06864)
