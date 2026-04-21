"""视频相关API路由"""
import uuid
import shutil
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, Form

from skyeye.db import get_db_connection
from skyeye.services import process_video, VIDEOS_DIR


router = APIRouter(prefix="/api/videos", tags=["videos"])


@router.get("")
async def list_videos():
    """获取视频列表"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, status, frame_count FROM videos ORDER BY created_at DESC")
    videos = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return videos


@router.post("/upload")
async def upload_video(file: UploadFile = File(...), name: str = Form("")):
    """上传视频"""
    video_id = str(uuid.uuid4())
    video_name = name or file.filename

    video_path = VIDEOS_DIR / f"{video_id}_{file.filename}"
    with open(video_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO videos (id, name, status) VALUES (?, ?, 'processing')", (video_id, video_name))
    conn.commit()
    conn.close()

    # 异步处理视频 - 使用延迟导入避免循环依赖
    from skyeye.main import process_video_async
    import asyncio
    asyncio.create_task(process_video_async(video_id, video_path))

    return {"video_id": video_id, "status": "processing"}
