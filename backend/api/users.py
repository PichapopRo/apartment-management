from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from model.user import UserRole
from repository.user_repository import UserRepository
from services.user_service import UserService
from utils.deps import get_db, require_roles
from utils.storage import save_citizen_id_image

router = APIRouter(prefix="/users", tags=["users"])


@router.post(
    "/{user_id}/citizen-id",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles(UserRole.ADMIN, UserRole.STAFF))],
)
def upload_citizen_id(user_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    repo = UserRepository(db)
    user = repo.get_by_id(user_id)
    if user is None or user.role != UserRole.RESIDENT.value:
        raise HTTPException(status_code=404, detail="Resident not found")

    path = save_citizen_id_image(file)
    UserService(db).set_citizen_id_image(user, path)
    return {"detail": "Citizen ID uploaded"}


@router.get(
    "/{user_id}/citizen-id",
    dependencies=[Depends(require_roles(UserRole.ADMIN, UserRole.STAFF))],
)
def get_citizen_id(user_id: int, db: Session = Depends(get_db)):
    user = UserRepository(db).get_by_id(user_id)
    if user is None or user.role != UserRole.RESIDENT.value:
        raise HTTPException(status_code=404, detail="Resident not found")
    if not user.citizen_id_image_path:
        raise HTTPException(status_code=404, detail="Citizen ID not uploaded")

    path = Path(user.citizen_id_image_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(path)
