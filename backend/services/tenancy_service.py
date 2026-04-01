from datetime import date

from sqlalchemy.orm import Session

from model.room import RoomStatus
from model.tenancy import Tenancy
from model.user import UserRole
from repository.room_repository import RoomRepository
from repository.tenancy_repository import TenancyRepository
from repository.user_repository import UserRepository


class TenancyService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.rooms = RoomRepository(db)
        self.tenancies = TenancyRepository(db)
        self.users = UserRepository(db)

    def assign_resident(self, room_id: int, resident_user_id: int, move_in: date) -> Tenancy:
        room = self.rooms.get_by_id(room_id)
        if room is None:
            raise ValueError("Room not found")

        resident = self.users.get_by_id(resident_user_id)
        if resident is None or resident.role != UserRole.RESIDENT.value:
            raise ValueError("Resident not found")

        if self.tenancies.get_active_by_room(room_id):
            raise ValueError("Room already occupied")

        if self.tenancies.get_active_by_resident(resident_user_id):
            raise ValueError("Resident already assigned to a room")

        tenancy = Tenancy(
            room_id=room_id,
            resident_user_id=resident_user_id,
            move_in_date=move_in,
            is_active=True,
        )
        tenancy = self.tenancies.create(tenancy)

        room.status = RoomStatus.OCCUPIED.value
        self.rooms.update(room)

        return tenancy

    def move_out(self, tenancy_id: int, move_out: date) -> Tenancy:
        tenancy = self.tenancies.get_by_id(tenancy_id)
        if tenancy is None or not tenancy.is_active:
            raise ValueError("Active tenancy not found")

        tenancy.move_out_date = move_out
        tenancy.is_active = False
        tenancy = self.tenancies.update(tenancy)

        room = self.rooms.get_by_id(tenancy.room_id)
        if room:
            room.status = RoomStatus.VACANT.value
            self.rooms.update(room)

        return tenancy
