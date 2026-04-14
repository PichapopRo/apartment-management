from sqlalchemy.orm import Session
from sqlalchemy import select

from model.bill import Bill
from model.meter_reading import MeterReading
from model.room import Room, RoomStatus
from model.room_document import RoomDocument
from model.tenancy import Tenancy
from model.user import User
from repository.room_repository import RoomRepository
from utils.errors import ConflictError


class RoomService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = RoomRepository(db)

    def create_room(
        self,
        room_number: str,
        floor: int | None,
        rent_rate,
        status: RoomStatus,
    ) -> Room:
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
        tenancy_ids = {
            row[0] for row in self.db.query(Tenancy.room_id).distinct().all()
        }
        document_ids = {
            row[0] for row in self.db.query(RoomDocument.room_id).distinct().all()
        }
        reading_ids = {
            row[0] for row in self.db.query(MeterReading.room_id).distinct().all()
        }
        bill_ids = {
            row[0] for row in self.db.query(Bill.room_id).distinct().all()
        }
        related_ids = tenancy_ids | document_ids | reading_ids | bill_ids

        stmt = (
            select(Room, Tenancy.resident_name, Tenancy.tenant_phone, User.full_name)
            .select_from(Room)
            .join(Tenancy, (Tenancy.room_id == Room.id) & (Tenancy.is_active.is_(True)), isouter=True)
            .join(User, User.id == Tenancy.resident_user_id, isouter=True)
            .order_by(Room.room_number.asc())
        )
        rows = self.db.execute(stmt).all()
        result = []
        for room, tenancy_name, tenancy_phone, user_name in rows:
            resident_name = tenancy_name or user_name
            result.append(
                {
                    "room": room,
                    "resident_name": resident_name,
                    "resident_phone": tenancy_phone,
                    "has_related": room.id in related_ids,
                }
            )
        return result

    def delete_room(self, room: Room, force: bool) -> None:
        has_related = (
            self.db.query(Tenancy).filter(Tenancy.room_id == room.id).first()
            or self.db.query(RoomDocument).filter(RoomDocument.room_id == room.id).first()
            or self.db.query(MeterReading).filter(MeterReading.room_id == room.id).first()
            or self.db.query(Bill).filter(Bill.room_id == room.id).first()
        )
        if has_related and not force:
            raise ConflictError("Room has related records. Use force delete to proceed.")

        if has_related and force:
            bill_ids = [row[0] for row in self.db.query(Bill.id).filter(Bill.room_id == room.id).all()]
            if bill_ids:
                from model.receipt import Receipt  # local import to avoid circular
                self.db.execute(
                    Receipt.__table__.delete().where(Receipt.bill_id.in_(bill_ids))
                )
                self.db.execute(
                    Bill.__table__.delete().where(Bill.id.in_(bill_ids))
                )
            self.db.execute(
                MeterReading.__table__.delete().where(MeterReading.room_id == room.id)
            )
            self.db.execute(
                RoomDocument.__table__.delete().where(RoomDocument.room_id == room.id)
            )
            self.db.execute(
                Tenancy.__table__.delete().where(Tenancy.room_id == room.id)
            )
            self.db.commit()

        self.repo.delete(room)
