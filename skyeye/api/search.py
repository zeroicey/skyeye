"""搜索相关API路由"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
import json

from skyeye.db import get_db_connection
from skyeye.services import search_frames, annotate_frame, parse_detection_indices


router = APIRouter(prefix="/api", tags=["search"])


@router.post("/search")
async def search(query: dict):
    """搜索帧"""
    video_ids = query.get("video_ids", [])
    search_query = query.get("query", "")
    results = search_frames(video_ids, search_query)
    return results


@router.get("/frames/{frame_id}/annotated")
async def get_annotated_frame(frame_id: str, detection_indices: str = ""):
    """获取带标注的帧图片"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT image_path, detections_json FROM frames WHERE id = ?", (frame_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Frame not found")

    image_path = row["image_path"]
    detections = json.loads(row["detections_json"]) if row["detections_json"] else []

    highlight_indices = parse_detection_indices(detection_indices)

    annotated_path = annotate_frame(image_path, detections, highlight_indices)
    return FileResponse(annotated_path)


@router.get("/frames/{frame_id}")
async def get_frame(frame_id: str):
    """获取原始帧图片"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT image_path FROM frames WHERE id = ?", (frame_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Frame not found")

    return FileResponse(row["image_path"])
