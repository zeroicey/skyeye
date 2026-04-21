# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

SkyEye is a video surveillance search system that uses YOLO for object detection and CLIP for clothing/person attribute recognition. Users can upload videos and search for specific content using natural language queries (supports Chinese and English).

## Commands

```bash
# Run the FastAPI application
python -m skyeye.main

# Install dependencies with uv
uv sync
```

The server runs on `http://localhost:8000` by default.

## Architecture

The project follows a layered architecture:

```
main.py           # FastAPI entry point, registers routes
db.py             # SQLite database initialization and connection
video_processor.py # Legacy video processing (moved to services/)
search.py         # Legacy search logic (moved to services/)

api/              # FastAPI route handlers
├── videos.py     # Video upload/processing endpoints
└── search.py     # Search endpoints

services/         # Business logic layer
├── video_service.py   # Video frame extraction + YOLO detection + CLIP clothing analysis
├── search_service.py   # Query parsing + database search
└── image_service.py   # Frame annotation for display
```

## Database Schema

- **videos**: id, name, status (processing/ready/error), frame_count, created_at
- **frames**: id, video_id, frame_index, timestamp, image_path, detections_json (stores YOLO + CLIP results)

## Key Features

1. **Video Processing**: Extracts frames every 10 frames, runs YOLO detection, uses CLIP for clothing attribute detection (color + clothing type)
2. **Search**: Supports natural language queries in Chinese/English (e.g., "穿红衣服的人", "person wearing red shirt")
3. **Web UI**: Frontend at `templates/index.html`

## Dependencies

- FastAPI + uvicorn
- Ultralytics YOLO (yolo26n.pt model)
- Transformers CLIP (openai/clip-vit-base-patch32)
- OpenCV
- PyTorch (CUDA)
- SQLite (built-in)

## Notes

- Network proxy: If network errors occur, set `$env:HTTP_PROXY="http://127.0.0.1:7897"; $env:HTTPS_PROXY="http://127.0.0.1:7897"`
- Models are loaded lazily on first use (YOLO: `yolo26n.pt`, CLIP: `openai/clip-vit-base-patch32`)
- Video and frame data stored in `data/videos/` and `data/frames/`
- Use xcrawl skills to search
