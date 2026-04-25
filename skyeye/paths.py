from pathlib import Path


def get_project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def get_db_path() -> Path:
    return get_project_root() / "skyeye.db"


def get_data_dir() -> Path:
    return get_project_root() / "data"


def get_videos_dir() -> Path:
    return get_data_dir() / "videos"


def get_frames_dir() -> Path:
    return get_data_dir() / "frames"
