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

    def assign_resident(
        self,
        room_id: int,
        resident_user_id: int | None,
        resident_name: str | None,
        tenant_phone: str | None,
        move_in: date,
    ) -> Tenancy:
        room = self.rooms.get_by_id(room_id)
        if room is None:
            raise ValueError("Room not found")

        if resident_user_id is None and not resident_name:
            raise ValueError("Resident name or resident user id is required")

        resident = None
        if resident_user_id is not None:
            resident = self.users.get_by_id(resident_user_id)
            if resident is None or resident.role != UserRole.RESIDENT.value:
                raise ValueError("Resident not found")

        if self.tenancies.get_active_by_room(room_id):
            raise ValueError("Room already occupied")

        if resident_user_id is not None and self.tenancies.get_active_by_resident(resident_user_id):
            raise ValueError("Resident already assigned to a room")

        tenancy = Tenancy(
            room_id=room_id,
            resident_user_id=resident_user_id,
            resident_name=resident_name,
            tenant_phone=tenant_phone,
            move_in_date=move_in,
            is_active=True,
        )
        tenancy = self.tenancies.create(tenancy)

        room.status = RoomStatus.OCCUPIED.value
        self.rooms.update(room)

        return tenancy

    def update_active_tenancy(
        self, room_id: int, resident_name: str | None, tenant_phone: str | None
    ) -> Tenancy:
        tenancy = self.tenancies.get_active_by_room(room_id)
        if tenancy is None:
            raise ValueError("Active tenancy not found")
        if resident_name is not None:
            tenancy.resident_name = resident_name
        if tenant_phone is not None:
            tenancy.tenant_phone = tenant_phone
        return self.tenancies.update(tenancy)

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
