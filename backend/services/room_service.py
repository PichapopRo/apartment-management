from sqlalchemy.orm import Session
from sqlalchemy import select

from model.room import Room, RoomStatus
from model.tenancy import Tenancy
from model.user import User
from repository.room_repository import RoomRepository


class RoomService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = RoomRepository(db)

    def create_room(self, room_number: str, floor: int | None, rent_rate, status: RoomStatus) -> Room:
        room = Room(
            room_number=room_number,
            floor=floor,
            rent_rate=rent_rate,
            status=status.value,
        )
        return self.repo.create(room)

    def update_room(
        self,
        room: Room,
        floor: int | None = None,
        rent_rate=None,
        status: RoomStatus | None = None,
    ) -> Room:
        if floor is not None:
            room.floor = floor
        if rent_rate is not None:
            room.rent_rate = rent_rate
        if status is not None:
            room.status = status.value
        return self.repo.update(room)

    def list_rooms_with_active_resident(self) -> list[dict]:
        stmt = (
            select(Room, Tenancy.resident_name, User.full_name)
            .select_from(Room)
            .join(Tenancy, (Tenancy.room_id == Room.id) & (Tenancy.is_active.is_(True)), isouter=True)
            .join(User, User.id == Tenancy.resident_user_id, isouter=True)
            .order_by(Room.room_number.asc())
        )
        rows = self.db.execute(stmt).all()
        result = []
        for room, tenancy_name, user_name in rows:
            resident_name = tenancy_name or user_name
            result.append({"room": room, "resident_name": resident_name})
        return result
