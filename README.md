# SkyEye

<p align="center">
  <strong>基于 YOLO 和 CLIP 的智能视频监控检索系统</strong><br>
  <a href="https://github.com/anthropics/claude-code">
    <img src="https://img.shields.io/badge/build-passing-brightgreen" alt="Build">
  </a>
  <a href="https://github.com/anthropics/claude-code">
    <img src="https://img.shields.io/badge/python-3.14+-blue" alt="Python">
  </a>
  <a href="https://github.com/anthropics/claude-code">
    <img src="https://img.shields.io/badge/license-MIT-green" alt="License">
  </a>
</p>

---

## 概述

SkyEye 是一个开源的视频监控智能检索系统，利用先进的深度学习模型实现对监控视频的智能分析和自然语言搜索。用户可以上传监控视频，通过自然语言描述（如"穿红衣服的人"或"person wearing red shirt"）快速定位目标对象。

## 特性

- **智能目标检测**：基于 YOLOv8n 实现实时目标检测
- **衣物属性识别**：基于 CLIP 模型识别衣物颜色和类型
- **自然语言搜索**：支持中英文双语搜索，语义理解精准
- **高效视频处理**：异步处理机制，支持大视频批量导入
- **简洁 Web UI**：现代化前端界面，操作直观便捷

## 技术架构

```
┌─────────────────────────────────────────────────────────────────┐
│                         Web UI (React + Vite)                    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      FastAPI Backend (Python)                    │
├──────────────────────┬──────────────────────┬───────────────────┤
│   /api/videos        │    /api/search       │    /api/frames    │
│   视频上传与处理       │    语义搜索           │    结果展示        │
└──────────────────────┴──────────────────────┴───────────────────┘
                              │
          ┌───────────────────┼───────────────────┐
          ▼                   ▼                   ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│   Video Service │  │  Search Service  │  │  Image Service  │
│  - 视频解码      │  │  - 查询解析      │  │  - 帧标注       │
│  - YOLO 检测    │  │  - 语义匹配      │  │  - 结果渲染     │
│  - CLIP 识别   │  │  - 数据库检索    │  │                 │
└─────────────────┘  └─────────────────┘  └─────────────────┘
          │                   │                   │
          └───────────────────┴───────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    AI Models (GPU Acceleration)                  │
├─────────────────────────────┬───────────────────────────────────┤
│   YOLOv8n (Ultralytics)    │   CLIP (openai/clip-vit-base)     │
│   目标检测                  │   衣物属性识别                      │
└─────────────────────────────┴───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                         SQLite Database                          │
├──────────────────────┬──────────────────────────────────────────┤
│   videos             │   frames                                 │
│   视频元信息          │   检测结果与属性数据                     │
└──────────────────────┴──────────────────────────────────────────┘
```

## 技术栈

### 后端

| 技术 | 版本 | 用途 |
|------|------|------|
| FastAPI | ≥0.136.0 | Web 框架 |
| Python | ≥3.14 | 运行环境 |
| PyTorch | ≥2.9.1 | 深度学习框架 |
| Ultralytics YOLO | ≥8.4.24 | 目标检测 |
| Transformers CLIP | ≥5.5.4 | 衣物属性识别 |
| OpenCV | ≥4.13.0 | 视频处理 |
| SQLite | 内置 | 数据存储 |

### 前端

| 技术 | 用途 |
|------|------|
| React | UI 框架 |
| TypeScript | 类型安全 |
| Vite | 构建工具 |
| Bun | 包管理器 |

## 快速开始

### 前置要求

- Python 3.14+
- CUDA 可选的 GPU 加速

### 安装

```bash
# 1. 克隆仓库
git clone https://github.com/zeroicey/skyeye.git
cd skyeye

# 2. 安装 Python 依赖
uv sync

# 3. 安装前端依赖
cd web && bun install && cd ..
```

### 运行

```bash
# 启动后端服务
python -m skyeye.main

# 启动前端开发服务器 (可选)
cd web && bun run dev
```

服务启动后访问：
- **Web UI**: http://localhost:5173
- **API 文档**: http://localhost:8000/docs

## API 接口

### 视频管理

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | `/api/videos/upload` | 上传视频 |
| GET | `/api/videos` | 获取视频列表 |
| GET | `/api/videos/{id}` | 获取视频详情 |
| DELETE | `/api/videos/{id}` | 删除视频 |

### 搜索

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | `/api/search` | 语义搜索 |
| GET | `/api/search/suggestions` | 获取搜索建议 |

### 帧数据

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/frames/{id}` | 获取帧详情 |
| GET | `/api/frames/{id}/image` | 获取帧图像 |

## 搜索示例

```bash
# 搜索穿红衣服的人
curl -X POST "http://localhost:8000/api/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "穿红衣服的人"}'

# Search for person wearing red shirt
curl -X POST "http://localhost:8000/api/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "person wearing red shirt"}'
```

## 项目结构

```
skyeye/
├── skyeye/                 # 主应用包
│   ├── api/               # API 路由
│   │   ├── videos.py      # 视频接口
│   │   └── search.py      # 搜索接口
│   ├── services/          # 业务逻辑
│   │   ├── video_service.py
│   │   ├── search_service.py
│   │   └── image_service.py
│   ├── templates/          # 模板
│   ├── utils/             # 工具函数
│   ├── db.py              # 数据库
│   ├── main.py            # 入口
│   └── cli.py             # CLI
├── web/                   # 前端项目
│   ├── src/              # 源代码
│   └── dist/             # 构建产物
├── data/                  # 数据目录
│   ├── videos/           # 视频存储
│   └── frames/           # 帧图像存储
├── docs/                  # 文档
└── pyproject.toml         # 项目配置
```

## 数据模型

### videos 表

| 字段 | 类型 | 描述 |
|------|------|------|
| id | TEXT | 视频 ID |
| name | TEXT | 视频名称 |
| status | TEXT | 处理状态 (processing/ready/error) |
| frame_count | INTEGER | 帧数量 |
| created_at | TEXT | 创建时间 |

### frames 表

| 字段 | 类型 | 描述 |
|------|------|------|
| id | INTEGER | 帧 ID |
| video_id | TEXT | 关联视频 ID |
| frame_index | INTEGER | 帧索引 |
| timestamp | REAL | 时间戳 |
| image_path | TEXT | 图像路径 |
| detections_json | TEXT | 检测结果 (JSON) |

## 环境变量

如需配置代理访问模型下载：

```powershell
# Windows
$env:HTTP_PROXY="http://127.0.0.1:7897"
$env:HTTPS_PROXY="http://127.0.0.1:7897"
```

```bash
# Linux/Mac
export HTTP_PROXY="http://127.0.0.1:7897"
export HTTPS_PROXY="http://127.0.0.1:7897"
```

## 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

---

<p align="center">
  Made with ❤️ by SkyEye Team
</p>
