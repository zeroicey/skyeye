"""SkyEye 视频检索系统 - 主入口"""
import asyncio
from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from db import get_db_connection, init_db
from api import videos_router, search_router
from services import VIDEOS_DIR, FRAMES_DIR, process_video


def ensure_directories():
    """Ensure required directories and database exist."""
    VIDEOS_DIR.mkdir(parents=True, exist_ok=True)
    FRAMES_DIR.mkdir(parents=True, exist_ok=True)
    init_db()


# Initialize directories and database before app starts
ensure_directories()

# 创建 FastAPI 应用
app = FastAPI(title="SkyEye Video Search")

# 注册路由
app.include_router(videos_router)
app.include_router(search_router)


@app.get("/", response_class=HTMLResponse)
async def index():
    """首页 - 返回前端页面"""
    with open(Path(__file__).parent / "templates" / "index.html", "r", encoding="utf-8") as f:
        return f.read()


async def process_video_async(video_id: str, video_path: Path):
    """异步处理视频"""
    try:
        process_video(video_id, video_path)
    except Exception as e:
        print(f"Error processing video: {e}")
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE videos SET status = 'error' WHERE id = ?", (video_id,))
        conn.commit()
        conn.close()


# 导出以便在其他模块中使用
app.state.process_video_async = process_video_async


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
