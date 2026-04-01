from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.schemas.room import RoomCreate, RoomOut, RoomPublic, RoomUpdate
from model.user import UserRole
from repository.room_repository import RoomRepository
from services.room_service import RoomService
from utils.deps import get_db, require_roles

router = APIRouter(prefix="/rooms", tags=["rooms"])


@router.get("", response_model=list[RoomOut], dependencies=[Depends(require_roles(UserRole.ADMIN, UserRole.STAFF))])
def list_rooms(db: Session = Depends(get_db)):
    service = RoomService(db)
    items = service.list_rooms_with_active_resident()
    response = []
    for item in items:
        room = item["room"]
        response.append(
            RoomOut(
                id=room.id,
                room_number=room.room_number,
                floor=room.floor,
                rent_rate=room.rent_rate,
                status=room.status,
                current_resident_name=item["resident_name"],
            )
        )
    return response


@router.get(
    "/public",
    response_model=list[RoomPublic],
    dependencies=[Depends(require_roles(UserRole.RESIDENT))],
)
def list_rooms_public(db: Session = Depends(get_db)):
    rooms = RoomRepository(db).list_all()
    return [RoomPublic(room_number=r.room_number, status=r.status) for r in rooms]


@router.post("", response_model=RoomOut, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_roles(UserRole.ADMIN))])
def create_room(payload: RoomCreate, db: Session = Depends(get_db)):
    repo = RoomRepository(db)
    if repo.get_by_number(payload.room_number):
        raise HTTPException(status_code=400, detail="Room number already exists")
    room = RoomService(db).create_room(
        room_number=payload.room_number,
        floor=payload.floor,
        rent_rate=payload.rent_rate,
        status=payload.status,
    )
    return RoomOut(
        id=room.id,
        room_number=room.room_number,
        floor=room.floor,
        rent_rate=room.rent_rate,
        status=room.status,
        current_resident_name=None,
    )


@router.patch("/{room_id}", response_model=RoomOut, dependencies=[Depends(require_roles(UserRole.ADMIN))])
def update_room(room_id: int, payload: RoomUpdate, db: Session = Depends(get_db)):
    repo = RoomRepository(db)
    room = repo.get_by_id(room_id)
    if room is None:
        raise HTTPException(status_code=404, detail="Room not found")
    room = RoomService(db).update_room(
        room=room,
        floor=payload.floor,
        rent_rate=payload.rent_rate,
        status=payload.status,
    )
    return RoomOut(
        id=room.id,
        room_number=room.room_number,
        floor=room.floor,
        rent_rate=room.rent_rate,
        status=room.status,
        current_resident_name=None,
    )
