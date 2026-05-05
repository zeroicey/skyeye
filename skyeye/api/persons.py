from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from skyeye.paths import get_data_dir
from skyeye.repositories import PersonRepository
from skyeye.storage import LocalObjectStore


router = APIRouter(prefix="/api/persons", tags=["persons"])


@router.get("/image")
async def get_person_image(uri: str):
    try:
        image_path = LocalObjectStore(get_data_dir()).resolve_uri(uri)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if not image_path.exists():
        raise HTTPException(status_code=404, detail="Image not found")
    return FileResponse(image_path)


@router.get("/{person_track_id}")
async def get_person_detail(person_track_id: str):
    detail = PersonRepository().get_person_detail(person_track_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Person track not found")
    detail["gallery"] = PersonRepository().get_person_gallery(person_track_id)
    return detail


@router.get("/{person_track_id}/gallery")
async def get_person_gallery(person_track_id: str):
    detail = PersonRepository().get_person_detail(person_track_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Person track not found")
    return PersonRepository().get_person_gallery(person_track_id)

