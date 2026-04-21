# SkyEye 视频特征检索系统

## 功能概述
基于 YOLO 目标检测的视频特征检索系统，支持：
1. 视频上传与异步处理
2. 多视频选择检索
3. 自然语言描述搜索

## 技术栈
- 后端: FastAPI
- 目标检测: YOLOv8 (ultralytics)
- 数据库: SQLite
- 前端: 简单 HTML/JS

## API 设计

### 1. 上传视频
- `POST /api/videos/upload`
- 请求: multipart/form-data (file, name)
- 返回: { "video_id": "xxx", "status": "processing" }

### 2. 获取视频列表
- `GET /api/videos`
- 返回: [{ "id": "xxx", "name": "xxx", "status": "ready", "frame_count": 100 }]

### 3. 搜索
- `POST /api/search`
- 请求: { "video_ids": ["xxx"], "query": "person wearing white" }
- 返回: [{ "frame_path": "xxx", "timestamp": 1.5, "detections": [...] }]

### 4. 获取帧图片
- `GET /api/frames/{frame_id}`
- 返回: 图像文件

## 数据模型

### videos 表
- id: TEXT PRIMARY KEY
- name: TEXT
- status: TEXT (processing/ready/error)
- frame_count: INTEGER
- created_at: TIMESTAMP

### frames 表
- id: TEXT PRIMARY KEY
- video_id: TEXT FOREIGN KEY
- frame_index: INTEGER
- timestamp: REAL
- image_path: TEXT
- detections_json: TEXT

## 目录结构
```
.
├── main.py              # FastAPI 应用
├── db.py                # 数据库初始化
├── video_processor.py   # 视频处理逻辑
├── search.py            # 搜索逻辑
├── templates/
│   └── index.html       # 前端页面
├── data/
│   ├── videos/          # 存储上传的视频
│   └── frames/          # 存储提取的帧
└── skyeye.db            # SQLite 数据库
```
